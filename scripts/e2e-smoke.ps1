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
"# Employee Handbook`n`nPTO policy: 25 days." | Set-Content $tmp
$doc = Invoke-RestMethod -Uri "$base/documents" -Method Post -WebSession $session -Form @{
  file = Get-Item $tmp
}
Write-Host "   OK id=$($doc.id) status=$($doc.status)"
if ($doc.status -ne 'stored') { throw "expected status 'stored', got '$($doc.status)'" }

Write-Host "3) document status endpoint"
$status = Invoke-RestMethod -Uri "$base/documents/$($doc.id)/status" -WebSession $session
Write-Host "   OK status=$($status.status)"

Write-Host "4) create chat session + send message"
$sess = Invoke-RestMethod -Uri "$base/chat/sessions" -Method Post -ContentType 'application/json' `
  -Body (@{ title = 'smoke' } | ConvertTo-Json) -WebSession $session
$reply = Invoke-RestMethod -Uri "$base/chat/sessions/$($sess.id)/messages" -Method Post `
  -ContentType 'application/json' -Body (@{ content = 'What is the PTO policy?' } | ConvertTo-Json) `
  -WebSession $session
Write-Host "   user:      $($reply.user.content)"
Write-Host "   assistant: $($reply.assistant.content)"
if ($reply.assistant.content -notmatch 'What is the PTO policy\?') { throw 'echo did not include the question' }

Write-Host "5) unauthenticated request is rejected"
try {
  Invoke-RestMethod -Uri "$base/documents" | Out-Null
  throw 'expected 401'
} catch {
  if ($_.Exception.Response.StatusCode.value__ -ne 401) { throw }
  Write-Host "   OK 401 without token"
}

Write-Host "`nM1 smoke: ALL CHECKS PASSED" -ForegroundColor Green
