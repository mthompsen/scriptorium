import json
from dataclasses import dataclass, field

from ingestion_service.extraction import EntityExtractor
from ingestion_service.graph_store import entity_id


@dataclass
class FakeReply:
    content: str
    usage: dict = field(default_factory=dict)


class FakeLLM:
    def __init__(self, reply: str) -> None:
        self.reply = reply

    def chat(self, messages, tools=None, stream=False) -> FakeReply:
        return FakeReply(self.reply)


VALID = json.dumps(
    {
        "entities": [
            {"name": "Aurelia Corp", "type": "organization"},
            {"name": "PTO Policy", "type": "policy"},
            {"name": "HR Portal", "type": "system"},
        ],
        "relations": [
            {"source": "Aurelia Corp", "relation": "owns", "target": "PTO Policy",
             "confidence": 0.9},
            {"source": "PTO Policy", "relation": "managed via", "target": "HR Portal",
             "confidence": 0.4},
            {"source": "Ghost Entity", "relation": "haunts", "target": "PTO Policy",
             "confidence": 0.95},
        ],
    }
)


def test_extracts_entities_and_filters_relations() -> None:
    entities, relations = EntityExtractor(FakeLLM(VALID)).extract("some chunk")

    assert {e.name for e in entities} == {"Aurelia Corp", "PTO Policy", "HR Portal"}
    # 0.4 confidence dropped (floor); Ghost Entity relation dropped (not extracted)
    assert len(relations) == 1
    assert relations[0].relation == "owns"
    assert relations[0].confidence == 0.9


def test_unknown_entity_types_coerce_to_other() -> None:
    reply = json.dumps(
        {"entities": [{"name": "Thing", "type": "spaceship"}], "relations": []}
    )

    entities, _ = EntityExtractor(FakeLLM(reply)).extract("x")

    assert entities[0].type == "other"


def test_fenced_and_garbage_output_degrade_gracefully() -> None:
    payload = json.dumps({"entities": [{"name": "A", "type": "person"}], "relations": []})
    fenced = f"```json\n{payload}\n```"
    entities, _ = EntityExtractor(FakeLLM(fenced)).extract("x")
    assert entities[0].name == "A"

    entities, relations = EntityExtractor(FakeLLM("I cannot extract anything, sorry!")).extract("x")
    assert entities == [] and relations == []


def test_duplicate_entities_dedupe_case_insensitively() -> None:
    reply = json.dumps(
        {
            "entities": [
                {"name": "Aurelia Corp", "type": "organization"},
                {"name": "aurelia corp", "type": "organization"},
            ],
            "relations": [],
        }
    )

    entities, _ = EntityExtractor(FakeLLM(reply)).extract("x")

    assert len(entities) == 1


def test_entity_id_is_deterministic_and_tenant_scoped() -> None:
    a = entity_id("tenant-1", "Aurelia Corp", "organization")

    assert a == entity_id("tenant-1", "aurelia corp", "organization")  # case-insensitive
    assert a != entity_id("tenant-2", "Aurelia Corp", "organization")  # tenant-scoped
    assert len(a) == 12
