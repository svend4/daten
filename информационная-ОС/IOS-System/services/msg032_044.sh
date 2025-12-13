# Start API server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Test endpoints
# 1. Health check
curl http://localhost:8000/health

# 2. Login
TOKEN=$(curl -X POST "http://localhost:8000/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin" | jq -r '.access_token')

# 3. Upload document
curl -X POST "http://localhost:8000/api/documents/upload?domain_name=SGB-IX" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_document.txt"

# 4. Search
curl -X POST "http://localhost:8000/api/search/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"test","search_type":"hybrid"}'

# Expected: All endpoints work, return valid JSON