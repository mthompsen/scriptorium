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

Write-Host "4) ask a question; expect a grounded, cited answer (LLM inference may take a minute)"
$sess = Invoke-RestMethod -Uri "$base/chat/sessions" -Method Post -ContentType 'application/json' `
  -Body (@{ title = 'smoke' } | ConvertTo-Json) -WebSession $session
$reply = Invoke-RestMethod -Uri "$base/chat/sessions/$($sess.id)/messages" -Method Post `
  -ContentType 'application/json' -Body (@{ content = 'How many days of PTO do employees get?' } | ConvertTo-Json) `
  -WebSession $session -TimeoutSec 300
Write-Host "   assistant: $($reply.assistant.content)"
Write-Host "   citations: $(($reply.assistant.citations | ForEach-Object { $_.chunk_id }) -join ', ')"
if ($reply.assistant.citations.Count -lt 1) { throw 'answer has no citations' }
if ($reply.assistant.content -notmatch '25') { throw 'answer does not contain the grounded fact (25 days)' }

Write-Host "5) unauthenticated request is rejected"
try {
  Invoke-RestMethod -Uri "$base/documents" | Out-Null
  throw 'expected 401'
} catch {
  if ($_.Exception.Response.StatusCode.value__ -ne 401) { throw }
  Write-Host "   OK 401 without token"
}

Write-Host "`nM1 smoke: ALL CHECKS PASSED" -ForegroundColor Green
