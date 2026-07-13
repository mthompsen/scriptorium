# Retrieval eval runner (DESIGN.md Section 9.4): uploads the labeled corpus,
# waits for indexing, then runs /eval/run and prints the metrics that go
# into docs/eval.md. Usage: pwsh scripts/run-eval.ps1
$ErrorActionPreference = 'Stop'
$bffBase = 'http://localhost:3001/api/v1'
# EVAL_AGENT_BASE lets the eval target a host-run agent process (e.g. the
# cli provider, which needs the host CLI) instead of the container.
$agentBase = if ($env:EVAL_AGENT_BASE) { $env:EVAL_AGENT_BASE } else { 'http://localhost:8002' }
$evalDir = Join-Path $PSScriptRoot '..\services\agent\eval'

$tenantId = '11111111-1111-4111-8111-111111111111'

Write-Host "0) reset eval corpus (local-only maintenance: metrics require a known corpus state)"
docker exec scriptorium-postgres-1 psql -U scriptorium -q -c "DELETE FROM documents WHERE tenant_id = '$tenantId';" | Out-Null
docker exec scriptorium-mongodb-1 mongosh --quiet --eval "const db2 = db.getSiblingDB('scriptorium'); db2.chunks.deleteMany({tenant_id: '$tenantId'}); db2.raw_documents.deleteMany({tenant_id: '$tenantId'});" | Out-Null
& curl.exe -s -X DELETE "http://localhost:9200/chunks-$tenantId" | Out-Null
Write-Host "   corpus cleared"

Write-Host "1) login"
Invoke-RestMethod -Uri "$bffBase/auth/login" -Method Post -ContentType 'application/json' `
  -Body (@{ email = 'demo@scriptorium.local'; password = 'scriptorium-demo' } | ConvertTo-Json) `
  -SessionVariable session | Out-Null

Write-Host "2) upload corpus"
$docIds = @{}
foreach ($file in Get-ChildItem (Join-Path $evalDir 'corpus') -Filter *.md) {
  $doc = Invoke-RestMethod -Uri "$bffBase/documents" -Method Post -WebSession $session -Form @{ file = $file }
  $docIds[$file.Name] = $doc.id
  Write-Host "   $($file.Name) -> $($doc.id)"
}

Write-Host "3) wait for indexing"
$deadline = (Get-Date).AddMinutes(10)
foreach ($name in $docIds.Keys) {
  while ($true) {
    $status = (Invoke-RestMethod -Uri "$bffBase/documents/$($docIds[$name])/status" -WebSession $session).status
    if ($status -eq 'indexed') { Write-Host "   $name indexed"; break }
    if ($status -eq 'failed') { throw "$name failed to index" }
    if ((Get-Date) -gt $deadline) { throw "timed out waiting for $name (status=$status)" }
    Start-Sleep -Seconds 3
  }
}

Write-Host "4) run eval (retrieval + generation; generation runs the agent loop and is slow on CPU)"
$dataset = Get-Content (Join-Path $evalDir 'queries.json') -Raw | ConvertFrom-Json
$queries = @($dataset.queries | ForEach-Object {
  @{ query = $_.query; expected_document_id = $docIds[$_.expected_file] }
})
$body = @{
  tenant_id         = $tenantId
  k                 = $dataset.k
  queries           = $queries
  generation        = $true
  generation_subset = 5
} | ConvertTo-Json -Depth 5
$result = Invoke-RestMethod -Uri "$agentBase/eval/run" -Method Post -ContentType 'application/json' `
  -Body $body -TimeoutSec 3600

$r = $result.retrieval
Write-Host "`n=== Retrieval ===" -ForegroundColor Green
Write-Host ("recall@{0} = {1}   MRR = {2}   ({3} queries)" -f $r.k, $r.recall_at_k, $r.mrr, $r.query_count)
$r.per_query | ForEach-Object {
  $rank = if ($null -eq $_.first_relevant_rank) { 'MISS' } else { "rank $($_.first_relevant_rank)" }
  Write-Host ("  {0,-62} {1}" -f $_.query, $rank)
}

$g = $result.generation
Write-Host "`n=== Generation (agent loop, subset of $($g.query_count)) ===" -ForegroundColor Green
Write-Host ("citation coverage = {0}   groundedness (LLM judge) = {1}" -f $g.citation_coverage, $g.groundedness)
$g.per_query | ForEach-Object {
  Write-Host ("  {0,-62} coverage={1} judge={2}" -f $_.query, $_.citation_coverage, $_.judge_grounded)
}
