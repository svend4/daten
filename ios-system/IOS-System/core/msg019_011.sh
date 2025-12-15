#!/bin/bash
# examples/curl_examples.sh
# Примеры использования API через cURL

BASE_URL="http://localhost:8000"
TOKEN=""

# ============================================================================
# AUTHENTICATION
# ============================================================================

# Вход
echo "=== Login ==="
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "Token: ${TOKEN:0:20}..."

# ============================================================================
# DOMAINS
# ============================================================================

# Список доменов
echo -e "\n=== List Domains ==="
curl -s -X GET "$BASE_URL/api/domains" \
  -H "Authorization: Bearer $TOKEN" | jq

# Создать домен
echo -e "\n=== Create Domain ==="
curl -s -X POST "$BASE_URL/api/domains" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SGB-IX",
    "language": "de",
    "description": "Deutsches Sozialrecht",
    "entity_types": ["Gesetz", "Paragraph", "Behörde", "Leistung"]
  }' | jq

# Получить домен
echo -e "\n=== Get Domain ==="
curl -s -X GET "$BASE_URL/api/domains/SGB-IX" \
  -H "Authorization: Bearer $TOKEN" | jq

# ============================================================================
# DOCUMENTS
# ============================================================================

# Загрузить документ
echo -e "\n=== Upload Document ==="
curl -s -X POST "$BASE_URL/api/documents/upload?domain_name=SGB-IX&title=Test+Document" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/document.pdf" | jq

# ============================================================================
# SEARCH
# ============================================================================

# Полнотекстовый поиск
echo -e "\n=== Full-Text Search ==="
curl -s -X POST "$BASE_URL/api/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Persönliches Budget",
    "domain_name": "SGB-IX",
    "search_type": "full_text",
    "limit": 5
  }' | jq

# Семантический поиск
echo -e "\n=== Semantic Search ==="
curl -s -X POST "$BASE_URL/api/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Wie bekomme ich Unterstützung?",
    "domain_name": "SGB-IX",
    "search_type": "semantic",
    "limit": 5
  }' | jq

# Гибридный поиск
echo -e "\n=== Hybrid Search ==="
curl -s -X POST "$BASE_URL/api/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SGB IX Teilhabe",
    "domain_name": "SGB-IX",
    "search_type": "hybrid",
    "ranking": "hybrid",
    "limit": 5
  }' | jq

# Автодополнение
echo -e "\n=== Autocomplete ==="
curl -s -X GET "$BASE_URL/api/search/suggest?prefix=Pers&domain_name=SGB-IX&max_suggestions=5" \
  -H "Authorization: Bearer $TOKEN" | jq

# ============================================================================
# KNOWLEDGE GRAPH
# ============================================================================

# Статистика графа
echo -e "\n=== Graph Statistics ==="
curl -s -X GET "$BASE_URL/api/graph/SGB-IX/statistics" \
  -H "Authorization: Bearer $TOKEN" | jq

# Список сущностей
echo -e "\n=== List Entities ==="
curl -s -X GET "$BASE_URL/api/graph/SGB-IX/entities?entity_type=Paragraph&limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq

# Создать сущность
echo -e "\n=== Create Entity ==="
curl -s -X POST "$BASE_URL/api/graph/SGB-IX/entities" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "Paragraph",
    "name": "§29",
    "properties": {
      "title": "Persönliches Budget",
      "law": "SGB-IX"
    },
    "source_document": "manual",
    "confidence": 1.0
  }' | jq

# Получить сущность
echo -e "\n=== Get Entity ==="
ENTITY_ID="entity_Paragraph_§29"
curl -s -X GET "$BASE_URL/api/graph/SGB-IX/entities/$ENTITY_ID" \
  -H "Authorization: Bearer $TOKEN" | jq

# Получить связанные сущности
echo -e "\n=== Get Related Entities ==="
curl -s -X GET "$BASE_URL/api/graph/SGB-IX/entities/$ENTITY_ID/related?direction=both" \
  -H "Authorization: Bearer $TOKEN" | jq

# Создать отношение
echo -e "\n=== Create Relation ==="
curl -s -X POST "$BASE_URL/api/graph/SGB-IX/relations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "verweist_auf",
    "source_id": "entity_para_29",
    "target_id": "entity_para_8",
    "properties": {},
    "confidence": 0.95
  }' | jq

# Запрос к графу (Cypher-like)
echo -e "\n=== Graph Query ==="
curl -s -X POST "$BASE_URL/api/graph/SGB-IX/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "cypher",
    "query": "MATCH (p:Paragraph)-[:belongs_to]->(g:Gesetz) RETURN p, g",
    "limit": 10
  }' | jq

# ============================================================================
# CONTEXTS
# ============================================================================

# Список контекстов
echo -e "\n=== List Contexts ==="
curl -s -X GET "$BASE_URL/api/contexts" \
  -H "Authorization: Bearer $TOKEN" | jq

# Создать контекст
echo -e "\n=== Create Context ==="
curl -s -X POST "$BASE_URL/api/contexts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Court Case S 12/2024",
    "type": "legal_case",
    "description": "Personal budget dispute",
    "active_domains": ["SGB-IX"],
    "properties": {
      "case_number": "S 12/2024",
      "court": "Sozialgericht München"
    }
  }' | jq

# Переключить контекст
echo -e "\n=== Switch Context ==="
CONTEXT_ID="ctx_court_case_s_12_2024"
curl -s -X POST "$BASE_URL/api/contexts/$CONTEXT_ID/switch" \
  -H "Authorization: Bearer $TOKEN" | jq

# ============================================================================
# ANALYTICS
# ============================================================================

# Наиболее связанные сущности
echo -e "\n=== Most Connected Entities ==="
curl -s -X GET "$BASE_URL/api/analytics/SGB-IX/graph?analysis_type=most_connected&top_n=5" \
  -H "Authorization: Bearer $TOKEN" | jq

# Центральные сущности
echo -e "\n=== Central Entities ==="
curl -s -X GET "$BASE_URL/api/analytics/SGB-IX/graph?analysis_type=central&top_n=5" \
  -H "Authorization: Bearer $TOKEN" | jq

# Обнаружение сообществ
echo -e "\n=== Communities ==="
curl -s -X GET "$BASE_URL/api/analytics/SGB-IX/graph?analysis_type=communities" \
  -H "Authorization: Bearer $TOKEN" | jq

# Рекомендации
echo -e "\n=== Recommendations ==="
curl -s -X GET "$BASE_URL/api/analytics/SGB-IX/graph?analysis_type=recommendations" \
  -H "Authorization: Bearer $TOKEN" | jq

# ============================================================================
# EXPORT
# ============================================================================

# Экспорт графа в GEXF (Gephi)
echo -e "\n=== Export Graph (GEXF) ==="
curl -X GET "$BASE_URL/api/export/SGB-IX/graph?format=gexf" \
  -H "Authorization: Bearer $TOKEN" \
  -o "graph_export.gexf"

# Экспорт графа в JSON
echo -e "\n=== Export Graph (JSON) ==="
curl -s -X GET "$BASE_URL/api/export/SGB-IX/graph?format=json" \
  -H "Authorization: Bearer $TOKEN" | jq

# ============================================================================
# SYSTEM
# ============================================================================

# Статус системы
echo -e "\n=== System Status ==="
curl -s -X GET "$BASE_URL/api/system/status" \
  -H "Authorization: Bearer $TOKEN" | jq

# Health check
echo -e "\n=== Health Check ==="
curl -s -X GET "$BASE_URL/api/system/health" | jq