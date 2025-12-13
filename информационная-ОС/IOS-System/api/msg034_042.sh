# Test background tasks
curl -X POST "http://localhost/api/documents/upload/async" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@large_document.pdf" \
  -F "domain_name=SGB-IX"

# Response:
# {
#   "task_id": "abc-123-def",
#   "status": "processing"
# }

# Check task status
curl "http://localhost/api/tasks/abc-123-def" \
  -H "Authorization: Bearer $TOKEN"

# Commit
git commit -m "Week 9-10 complete: Security + Advanced features"
git tag v0.2.0-week10