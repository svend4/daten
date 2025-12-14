# docs/api_examples.py

"""
API usage examples for documentation
"""

# Example 1: Basic Search
EXAMPLE_BASIC_SEARCH = {
    "request": {
        "method": "POST",
        "url": "/api/search/",
        "headers": {
            "Content-Type": "application/json"
        },
        "body": {
            "query": "persönliches budget",
            "page": 1,
            "page_size": 20
        }
    },
    "response": {
        "status": 200,
        "body": {
            "results": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "score": 0.95,
                    "rank": 1,
                    "source": "both",
                    "title": "SGB IX § 29 - Persönliches Budget",
                    "summary": "Das Persönliche Budget ist eine Leistungsform...",
                    "document_type": "LAW",
                    "category": "Sozialrecht",
                    "legal_code": "SGB IX",
                    "paragraph": "§ 29"
                }
            ],
            "total": 42,
            "page": 1,
            "page_size": 20,
            "total_pages": 3,
            "search_time_ms": 127,
            "query_id": "123e4567-e89b-12d3-a456-426614174000"
        }
    }
}

# Example 2: Search with Filters
EXAMPLE_FILTERED_SEARCH = {
    "request": {
        "method": "POST",
        "url": "/api/search/",
        "body": {
            "query": "pflege",
            "filters": {
                "document_type": "LAW",
                "legal_code": "SGB XI",
                "tags": ["pflege", "versicherung"]
            },
            "page": 1,
            "page_size": 10,
            "sort_by": "date_desc"
        }
    }
}

# Example 3: Autocomplete
EXAMPLE_AUTOCOMPLETE = {
    "request": {
        "method": "GET",
        "url": "/api/autocomplete/?query=pers&limit=5"
    },
    "response": {
        "status": 200,
        "body": [
            {
                "text": "persönliches budget",
                "frequency": 156,
                "score": 1.0
            },
            {
                "text": "persönliche assistenz",
                "frequency": 89,
                "score": 0.8
            },
            {
                "text": "persönlichkeitsrechte",
                "frequency": 45,
                "score": 0.6
            }
        ]
    }
}

# Example 4: Track Click
EXAMPLE_TRACK_CLICK = {
    "request": {
        "method": "POST",
        "url": "/api/track-click/",
        "body": {
            "query_id": "123e4567-e89b-12d3-a456-426614174000",
            "document_id": "550e8400-e29b-41d4-a716-446655440000",
            "position": 1,
            "score": 0.95
        }
    },
    "response": {
        "status": 201,
        "body": {
            "status": "Click tracked"
        }
    }
}

# Example 5: Get Document
EXAMPLE_GET_DOCUMENT = {
    "request": {
        "method": "GET",
        "url": "/api/documents/550e8400-e29b-41d4-a716-446655440000/"
    },
    "response": {
        "status": 200,
        "body": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "SGB IX § 29 - Persönliches Budget",
            "content": "Vollständiger Gesetzestext...",
            "summary": "Das Persönliche Budget...",
            "document_type": "LAW",
            "category": "Sozialrecht",
            "legal_code": "SGB IX",
            "paragraph": "§ 29",
            "tags": ["persönliches budget", "sgb ix", "teilhabe"],
            "source_url": "https://www.gesetze-im-internet.de/sgb_9/__29.html",
            "created_at": "2024-01-15T10:30:00Z",
            "view_count": 1523,
            "click_count": 342
        }
    }
}

# Example 6: Health Check
EXAMPLE_HEALTH_CHECK = {
    "request": {
        "method": "GET",
        "url": "/api/health/"
    },
    "response": {
        "status": 200,
        "body": {
            "status": "healthy",
            "services": {
                "database": "up",
                "elasticsearch": "up",
                "qdrant": "up",
                "redis": "up"
            }
        }
    }
}