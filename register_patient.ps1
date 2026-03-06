$apiKey = $env:API_KEY
if (-not $apiKey) {
  Write-Error "Missing API_KEY environment variable. Set it before running this script."
  exit 1
}

Invoke-RestMethod -Uri "http://127.0.0.1:8000/register" -Method Post `
  -Headers @{"X-API-KEY"=$apiKey; "Content-Type"="application/json"} `
  -Body '{"patient_id":"PAT-001","full_name":"AYADI Fodil","age":22}'