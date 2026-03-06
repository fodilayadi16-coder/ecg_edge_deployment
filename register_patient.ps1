Invoke-RestMethod -Uri "http://127.0.0.1:8000/register" -Method Post `
  -Headers @{"X-API-KEY"="ecg_prod_5456a7628afc0baf8d4cf39a568a35bb45adb45b3775731791ea0c82b35b792c"; "Content-Type"="application/json"} `
  -Body '{"patient_id":"PAT-001","full_name":"AYADI Fodil","age":22}'