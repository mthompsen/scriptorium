# M1 end-to-end smoke: login -> upload -> chat, against the local compose stack.
# Usage: pwsh scripts/e2e-smoke.ps1
$ErrorActionPreference = 'Stop'
$base = 'http://localhost:3001/api/v1'

Write-Host "1) login as demo user"
$login = Invoke-RestMethod -Uri "$base/auth/login" -Method Post -ContentType 'application/json' `
  -Body (@{ email = 'demo@scriptorium.local'; password = 'scriptorium-demo' } | ConvertTo-Json) `
  -SessionVariable session
Write-Host "   OK user=$($login.user.email) tenant=$($login.user.tenantId) roles=$($login.user.roles -join ',')"

Write-Host "2) upload a markdown document"
$tmp = Join-Path ([System.IO.Path]::GetTempPath()) 'scriptorium-smoke.md'
@"
# Smoke Test Handbook

## Paid time off

Employees receive 25 days of paid time off per year, accrued monthly.
"@ | Set-Content $tmp
$doc = Invoke-RestMethod -Uri "$base/documents" -Method Post -WebSession $session -Form @{
  file = Get-Item $tmp
}
Write-Host "   OK id=$($doc.id) status=$($doc.status)"
if ($doc.status -ne 'stored') { throw "expected status 'stored', got '$($doc.status)'" }

Write-Host "3) wait for document to be indexed (parse -> chunk -> embed -> index)"
$deadline = (Get-Date).AddMinutes(5)
while ($true) {
  $status = (Invoke-RestMethod -Uri "$base/documents/$($doc.id)/status" -WebSession $session).status
  if ($status -eq 'indexed') { Write-Host "   OK status=indexed"; break }
  if ($status -eq 'failed') { throw 'document failed to index' }
  if ((Get-Date) -gt $deadline) { throw "timed out (status=$status)" }
  Start-Sleep -Seconds 3
}

Write-Host "4) ask a question (JSON mode); expect a grounded, cited answer (LLM inference may take a minute)"
$sess = Invoke-RestMethod -Uri "$base/chat/sessions" -Method Post -ContentType 'application/json' `
  -Body (@{ title = 'smoke' } | ConvertTo-Json) -WebSession $session
$reply = Invoke-RestMethod -Uri "$base/chat/sessions/$($sess.id)/messages?stream=false" -Method Post `
  -ContentType 'application/json' -Body (@{ content = 'How many days of PTO do employees get?' } | ConvertTo-Json) `
  -WebSession $session -TimeoutSec 300
Write-Host "   assistant: $($reply.assistant.content)"
Write-Host "   citations: $(($reply.assistant.citations | ForEach-Object { $_.chunk_id }) -join ', ')"
if ($reply.assistant.citations.Count -lt 1) { throw 'answer has no citations' }
if ($reply.assistant.content -notmatch '25') { throw 'answer does not contain the grounded fact (25 days)' }

Write-Host "4b) same question over SSE; expect tool, token, and final events"
$token = $login.accessToken
$sseBody = '{"content":"How many days of PTO do employees get?"}'
$sse = & curl.exe -s -N --max-time 280 -X POST `
  -H "Authorization: Bearer $token" -H "Content-Type: application/json" `
  -d $sseBody "$base/chat/sessions/$($sess.id)/messages" | Out-String
foreach ($expected in 'event: run_start', 'event: tool', 'event: token', 'event: final') {
  if ($sse -notmatch [regex]::Escape($expected)) { throw "SSE stream missing '$expected'" }
}
$toolLine = ($sse -split "`n" | Where-Object { $_ -match '"name":' } | Select-Object -First 1).Trim()
Write-Host "   OK stream carried run_start/tool/token/final ($toolLine)"

Write-Host "4c) trace rows exist and the run links to its message"
$trace = docker exec scriptorium-postgres-1 psql -U scriptorium -t -A -c `
  "SELECT (SELECT count(*) FROM agent_runs WHERE status='succeeded' AND message_id IS NOT NULL), (SELECT count(*) FROM agent_steps WHERE kind='tool'), (SELECT count(*) FROM agent_steps WHERE kind='final');"
$parts = $trace.Trim() -split '\|'
if ([int]$parts[0] -lt 1) { throw 'no succeeded agent_runs linked to a message' }
if ([int]$parts[1] -lt 1) { throw 'no tool steps traced' }
if ([int]$parts[2] -lt 1) { throw 'no final steps traced' }
Write-Host "   OK linked_runs=$($parts[0]) tool_steps=$($parts[1]) final_steps=$($parts[2])"

Write-Host "4d) off-corpus question is refused, not answered from memory"
$refusal = Invoke-RestMethod -Uri 'http://localhost:8002/answer' -Method Post -ContentType 'application/json' `
  -Body '{"tenant_id":"11111111-1111-4111-8111-111111111111","question":"What is the capital of France?","stream":false}' `
  -TimeoutSec 300
if ($refusal.grounded) { throw 'expected an ungrounded refusal' }
if ($refusal.citations.Count -ne 0) { throw 'refusal should carry no citations' }
Write-Host "   OK refused: $($refusal.answer.Substring(0, [Math]::Min(80, $refusal.answer.Length)))..."

Write-Host "5) unauthenticated request is rejected"
try {
  Invoke-RestMethod -Uri "$base/documents" | Out-Null
  throw 'expected 401'
} catch {
  if ($_.Exception.Response.StatusCode.value__ -ne 401) { throw }
  Write-Host "   OK 401 without token"
}

Write-Host "`nSmoke: ALL CHECKS PASSED" -ForegroundColor Green
