"""Entity/relation extraction (DESIGN.md Section 9.1, ADR-0006).

Uses the configured LLM with a strict JSON instruction and defensive
parsing: malformed output degrades to "no triples", never a failed document.
Relations below the confidence floor are dropped.
"""

import json
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

ENTITY_TYPES = {
    "person",
    "organization",
    "policy",
    "system",
    "location",
    "role",
    "benefit",
    "process",
    "other",
}

CONFIDENCE_FLOOR = 0.6

_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)

SYSTEM_PROMPT = (
    "You extract a knowledge graph from workplace documents. Given a text "
    "chunk, reply with EXACTLY ONE JSON object and nothing else:\n"
    '{"entities": [{"name": "...", "type": "..."}], '
    '"relations": [{"source": "...", "relation": "...", "target": "...", '
    '"confidence": 0.0}]}\n'
    f"Entity types must be one of: {sorted(ENTITY_TYPES - {'other'})}. "
    "Use concise canonical names (e.g. 'Aurelia Corp', not 'the company'). "
    "relations connect two extracted entity names with a short verb phrase "
    "(e.g. 'owns', 'requires', 'reports to') and a confidence between 0 and "
    "1. Only include facts stated in the text. If nothing is extractable, "
    'reply {"entities": [], "relations": []}.'
)


@dataclass(frozen=True)
class Entity:
    name: str
    type: str


@dataclass(frozen=True)
class Relation:
    source: str
    relation: str
    target: str
    confidence: float


class EntityExtractor:
    def __init__(self, llm, confidence_floor: float = CONFIDENCE_FLOOR) -> None:
        self._llm = llm
        self._confidence_floor = confidence_floor

    def extract(self, text: str) -> tuple[list[Entity], list[Relation]]:
        response = self._llm.chat(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ]
        )
        return self._parse(response.content)

    def _parse(self, raw: str) -> tuple[list[Entity], list[Relation]]:
        cleaned = _FENCE_PATTERN.sub("", raw.strip()).strip()
        try:
            body = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("extraction output was not JSON; dropping (%.80s...)", raw)
            return [], []
        if not isinstance(body, dict):
            return [], []

        entities: dict[str, Entity] = {}
        for item in body.get("entities") or []:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            entity_type = str(item.get("type") or "other").strip().lower()
            if not name:
                continue
            if entity_type not in ENTITY_TYPES:
                entity_type = "other"
            entities.setdefault(name.lower(), Entity(name=name, type=entity_type))

        relations: list[Relation] = []
        for item in body.get("relations") or []:
            if not isinstance(item, dict):
                continue
            source = str(item.get("source") or "").strip()
            target = str(item.get("target") or "").strip()
            relation = str(item.get("relation") or "").strip()
            try:
                confidence = float(item.get("confidence", 0.0))
            except (TypeError, ValueError):
                continue
            if not (source and target and relation):
                continue
            if confidence < self._confidence_floor:
                continue  # low-confidence triples are dropped (Section 9.1)
            if source.lower() not in entities or target.lower() not in entities:
                continue  # relations must connect extracted entities
            relations.append(
                Relation(
                    source=source,
                    relation=relation,
                    target=target,
                    confidence=round(min(confidence, 1.0), 3),
                )
            )
        return list(entities.values()), relations
