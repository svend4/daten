// examples/javascript_client.js
/**
 * JavaScript/TypeScript клиент для IOS API
 */

class IOSClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.token = null;
        this.ws = null;
    }

    // ========================================================================
    // AUTHENTICATION
    // ========================================================================

    async login(username, password) {
        const response = await fetch(`${this.baseUrl}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        if (response.ok) {
            const data = await response.json();
            this.token = data.access_token;
            return true;
        }

        return false;
    }

    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        return headers;
    }

    // ========================================================================
    // DOMAINS
    // ========================================================================

    async listDomains() {
        const response = await fetch(`${this.baseUrl}/api/domains`, {
            headers: this.getHeaders()
        });

        return await response.json();
    }

    async createDomain(name, language = 'de', description = '', entityTypes = []) {
        const response = await fetch(`${this.baseUrl}/api/domains`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify({
                name,
                language,
                description,
                entity_types: entityTypes
            })
        });

        return await response.json();
    }

    async getDomain(domainName) {
        const response = await fetch(`${this.baseUrl}/api/domains/${domainName}`, {
            headers: this.getHeaders()
        });

        return await response.json();
    }

    // ========================================================================
    // DOCUMENTS
    // ========================================================================

    async uploadDocument(file, domainName, title = null, author = null, tags = []) {
        const formData = new FormData();
        formData.append('file', file);

        const params = new URLSearchParams({ domain_name: domainName });
        if (title) params.append('title', title);
        if (author) params.append('author', author);
        tags.forEach(tag => params.append('tags', tag));

        const response = await fetch(
            `${this.baseUrl}/api/documents/upload?${params}`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                },
                body: formData
            }
        );

        return await response.json();
    }

    // ========================================================================
    // SEARCH
    // ========================================================================

    async search(query, options = {}) {
        const {
            domainName = null,
            searchType = 'full_text',
            limit = 10,
            offset = 0,
            filters = {},
            ranking = 'hybrid'
        } = options;

        const response = await fetch(`${this.baseUrl}/api/search`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify({
                query,
                domain_name: domainName,
                search_type: searchType,
                limit,
                offset,
                filters,
                ranking
            })
        });

        return await response.json();
    }

    async autocomplete(prefix, domainName = null, maxSuggestions = 10) {
        const params = new URLSearchParams({
            prefix,
            max_suggestions: maxSuggestions
        });

        if (domainName) {
            params.append('domain_name', domainName);
        }

        const response = await fetch(
            `${this.baseUrl}/api/search/suggest?${params}`,
            {
                headers: this.getHeaders()
            }
        );

        return await response.json();
    }

    // ========================================================================
    // KNOWLEDGE GRAPH
    // ========================================================================

    async getGraphStatistics(domainName) {
        const response = await fetch(
            `${this.baseUrl}/api/graph/${domainName}/statistics`,
            {
                headers: this.getHeaders()
            }
        );

        return await response.json();
    }

    async listEntities(domainName, entityType = null, limit = 100) {
        const params = new URLSearchParams({ limit });
        if (entityType) params.append('entity_type', entityType);

        const response = await fetch(
            `${this.baseUrl}/api/graph/${domainName}/entities?${params}`,
            {
                headers: this.getHeaders()
            }
        );

        return await response.json();
    }

    async getEntity(domainName, entityId) {
        const response = await fetch(
            `${this.baseUrl}/api/graph/${domainName}/entities/${entityId}`,
            {
                headers: this.getHeaders()
            }
        );

        return await response.json();
    }

    async getRelatedEntities(domainName, entityId, relationType = null, direction = 'both') {
        const params = new URLSearchParams({ direction });
        if (relationType) params.append('relation_type', relationType);

        const response = await fetch(
            `${this.baseUrl}/api/graph/${domainName}/entities/${entityId}/related?${params}`,
            {
                headers: this.getHeaders()
            }
        );

        return await response.json();
    }

    async createEntity(domainName, entityType, name, properties = {}, sourceDocument = 'manual', confidence = 1.0) {
        const response = await fetch(
            `${this.baseUrl}/api/graph/${domainName}/entities`,
            {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({
                    type: entityType,
                    name,
                    properties,
                    source_document: sourceDocument,
                    confidence
                })
            }
        );

        return await response.json();
    }

    async queryGraph(domainName, queryType, query, parameters = {}, limit = 10) {
        const response = await fetch(
            `${this.baseUrl}/api/graph/${domainName}/query`,
            {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({
                    query_type: queryType,
                    query,
                    parameters,
                    limit
                })
            }
        );

        return await response.json();
    }

    // ========================================================================
    // CONTEXTS
    // ========================================================================

    async listContexts() {
        const response = await fetch(`${this.baseUrl}/api/contexts`, {
            headers: this.getHeaders()
        });

        return await response.json();
    }

    async createContext(name, contextType, description = '', activeDomains = [], properties = {}) {
        const response = await fetch(`${this.baseUrl}/api/contexts`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify({
                name,
                type: contextType,
                description,
                active_domains: activeDomains,
                properties
            })
        });

        return await response.json();
    }

    async switchContext(contextId) {
        const response = await fetch(
            `${this.baseUrl}/api/contexts/${contextId}/switch`,
            {
                method: 'POST',
                headers: this.getHeaders()
            }
        );

        return await response.json();
    }

    // ========================================================================
    // ANALYTICS
    // ========================================================================

    async getGraphAnalytics(domainName, analysisType, topN = 10) {
        const params = new URLSearchParams({
            analysis_type: analysisType,
            top_n: topN
        });

        const response = await fetch(
            `${this.baseUrl}/api/analytics/${domainName}/graph?${params}`,
            {
                headers: this.getHeaders()
            }
        );

        return await response.json();
    }

    // ========================================================================
    // WEBSOCKET
    // ========================================================================

    connectWebSocket(userId, onMessageCallback = null) {
        const wsUrl = this.baseUrl
            .replace('http://', 'ws://')
            .replace('https://', 'wss://');

        this.ws = new WebSocket(`${wsUrl}/ws/${userId}`);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('WebSocket message:', data);

            if (onMessageCallback) {
                onMessageCallback(data);
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onclose = () => {
            console.log('WebSocket closed');
        };
    }

    subscribeToEvent(eventType) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                action: 'subscribe',
                event_type: eventType
            }));
        }
    }

    unsubscribeFromEvent(eventType) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                action: 'unsubscribe',
                event_type: eventType
            }));
        }
    }
}


// ============================================================================
// ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
// ============================================================================

async function exampleUsage() {
    // Создать клиента
    const client = new IOSClient('http://localhost:8000');

    // Войти
    const loggedIn = await client.login('admin', 'admin');
    if (loggedIn) {
        console.log('✓ Logged in successfully');
    }

    // Создать домен
    const domain = await client.createDomain(
        'SGB-IX',
        'de',
        'Deutsches Sozialrecht',
        ['Gesetz', 'Paragraph', 'Behörde']
    );
    console.log(`✓ Created domain: ${domain.name}`);

    // Поиск
    const results = await client.search('Persönliches Budget', {
        domainName: 'SGB-IX',
        searchType: 'hybrid',
        limit: 5
    });
    console.log(`✓ Found ${results.total_count} documents`);
    results.results.forEach(result => {
        console.log(`  - ${result.title} (score: ${result.score.toFixed(3)})`);
    });

    // Автодополнение
    const suggestions = await client.autocomplete('Pers', 'SGB-IX', 5);
    console.log('✓ Autocomplete suggestions:', suggestions);

    // Статистика графа
    const stats = await client.getGraphStatistics('SGB-IX');
    console.log('✓ Graph statistics:');
    console.log(`  Entities: ${stats.total_entities}`);
    console.log(`  Relations: ${stats.total_relations}`);

    // Сущности
    const entities = await client.listEntities('SGB-IX', 'Paragraph', 10);
    console.log(`✓ Found ${entities.length} paragraphs`);

    // Аналитика
    const analytics = await client.getGraphAnalytics('SGB-IX', 'most_connected', 5);
    console.log('✓ Top 5 most connected entities:');
    analytics.results.forEach(item => {
        const entity = item.entity;
        console.log(`  - ${entity.name} (${entity.type}): ${item.degree} connections`);
    });

    // WebSocket
    client.connectWebSocket('user123', (data) => {
        console.log(`Received: ${data.type}`);
    });

    client.subscribeToEvent('document.added');
    client.subscribeToEvent('entity.extracted');
}

// Запустить примеры (в браузере или Node.js)
// exampleUsage();