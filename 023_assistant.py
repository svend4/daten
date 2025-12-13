Пользователь хочет продолжить с Android интеграцией и Docker deployment. Это логическое продолжение - нужно показать:
1. Как интегрировать IOS API в Android приложения (что особенно актуально для Max, так как он создавал Android приложения)
2. Docker deployment для развертывания всей системы

Давайте создам:
1. Android Kotlin клиент для IOS API
2. Пример Android приложения с использованием IOS
3. Docker Compose конфигурацию для развертывания
4. Deployment guide с инструкциями# ЧАСТЬ 10: ANDROID ИНТЕГРАЦИЯ И DEPLOYMENT

## 10.1 Android Kotlin клиент для IOS API

```kotlin
// android/IOSClient.kt
/**
 * Kotlin клиент для Information Operating System API
 * Использует Retrofit для HTTP запросов и OkHttp для WebSocket
 */

package com.example.ios.client

import okhttp3.*
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import com.google.gson.annotations.SerializedName
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import java.util.concurrent.TimeUnit

// ============================================================================
// DATA MODELS
// ============================================================================

data class LoginRequest(
    val username: String,
    val password: String
)

data class TokenResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String,
    @SerializedName("expires_in") val expiresIn: Int
)

data class DomainCreate(
    val name: String,
    val language: String = "de",
    val description: String? = null,
    @SerializedName("entity_types") val entityTypes: List<String> = emptyList()
)

data class DomainResponse(
    val name: String,
    val language: String,
    val description: String?,
    @SerializedName("entity_types") val entityTypes: List<String>,
    @SerializedName("created_at") val createdAt: String,
    val statistics: Map<String, Any>
)

data class SearchRequest(
    val query: String,
    @SerializedName("search_type") val searchType: String = "full_text",
    @SerializedName("domain_name") val domainName: String? = null,
    val limit: Int = 10,
    val offset: Int = 0,
    val filters: Map<String, Any> = emptyMap(),
    val ranking: String = "hybrid"
)

data class SearchResponse(
    val results: List<DocumentResult>,
    @SerializedName("total_count") val totalCount: Int,
    val facets: Map<String, Map<String, Int>>?,
    val query: String,
    @SerializedName("search_time_ms") val searchTimeMs: Float
)

data class DocumentResult(
    @SerializedName("doc_id") val docId: String,
    val title: String,
    @SerializedName("document_type") val documentType: String,
    val category: String,
    val score: Float,
    val highlights: String?
)

data class EntityResponse(
    val id: String,
    val type: String,
    val name: String,
    val properties: Map<String, Any>,
    @SerializedName("source_document") val sourceDocument: String,
    val confidence: Float,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("updated_at") val updatedAt: String
)

data class GraphStatistics(
    @SerializedName("total_entities") val totalEntities: Int,
    @SerializedName("total_relations") val totalRelations: Int,
    @SerializedName("entity_types") val entityTypes: Map<String, Int>,
    @SerializedName("relation_types") val relationTypes: Map<String, Int>,
    val density: Float,
    @SerializedName("connected_components") val connectedComponents: Int
)

data class ContextCreate(
    val name: String,
    val type: String,
    val description: String? = null,
    @SerializedName("active_domains") val activeDomains: List<String> = emptyList(),
    val properties: Map<String, Any> = emptyMap()
)

data class ContextResponse(
    val id: String,
    val name: String,
    val type: String,
    val description: String?,
    @SerializedName("active_domains") val activeDomains: List<String>,
    @SerializedName("active_projects") val activeProjects: List<String>,
    @SerializedName("active_documents") val activeDocuments: List<String>,
    @SerializedName("last_accessed") val lastAccessed: String,
    @SerializedName("access_count") val accessCount: Int
)

// WebSocket messages
data class WebSocketMessage(
    val type: String,
    val data: Map<String, Any>? = null,
    val timestamp: String? = null
)

// ============================================================================
// RETROFIT API INTERFACE
// ============================================================================

interface IOSApiService {
    
    // Authentication
    @POST("api/auth/login")
    suspend fun login(@Body request: LoginRequest): TokenResponse
    
    @POST("api/auth/logout")
    suspend fun logout(): Map<String, String>
    
    // Domains
    @GET("api/domains")
    suspend fun listDomains(): List<String>
    
    @POST("api/domains")
    suspend fun createDomain(@Body domain: DomainCreate): DomainResponse
    
    @GET("api/domains/{domain_name}")
    suspend fun getDomain(@Path("domain_name") domainName: String): DomainResponse
    
    @DELETE("api/domains/{domain_name}")
    suspend fun deleteDomain(@Path("domain_name") domainName: String)
    
    // Documents
    @Multipart
    @POST("api/documents/upload")
    suspend fun uploadDocument(
        @Part file: MultipartBody.Part,
        @Query("domain_name") domainName: String,
        @Query("title") title: String? = null,
        @Query("author") author: String? = null,
        @Query("tags") tags: List<String>? = null
    ): DocumentResult
    
    // Search
    @POST("api/search")
    suspend fun search(@Body request: SearchRequest): SearchResponse
    
    @GET("api/search/suggest")
    suspend fun autocomplete(
        @Query("prefix") prefix: String,
        @Query("domain_name") domainName: String? = null,
        @Query("max_suggestions") maxSuggestions: Int = 10
    ): List<String>
    
    // Knowledge Graph
    @GET("api/graph/{domain_name}/statistics")
    suspend fun getGraphStatistics(
        @Path("domain_name") domainName: String
    ): GraphStatistics
    
    @GET("api/graph/{domain_name}/entities")
    suspend fun listEntities(
        @Path("domain_name") domainName: String,
        @Query("entity_type") entityType: String? = null,
        @Query("limit") limit: Int = 100,
        @Query("offset") offset: Int = 0
    ): List<EntityResponse>
    
    @GET("api/graph/{domain_name}/entities/{entity_id}")
    suspend fun getEntity(
        @Path("domain_name") domainName: String,
        @Path("entity_id") entityId: String
    ): EntityResponse
    
    @GET("api/graph/{domain_name}/entities/{entity_id}/related")
    suspend fun getRelatedEntities(
        @Path("domain_name") domainName: String,
        @Path("entity_id") entityId: String,
        @Query("relation_type") relationType: String? = null,
        @Query("direction") direction: String = "both"
    ): List<EntityResponse>
    
    // Contexts
    @GET("api/contexts")
    suspend fun listContexts(): List<ContextResponse>
    
    @POST("api/contexts")
    suspend fun createContext(@Body context: ContextCreate): ContextResponse
    
    @POST("api/contexts/{context_id}/switch")
    suspend fun switchContext(
        @Path("context_id") contextId: String
    ): Map<String, Any>
    
    // Analytics
    @GET("api/analytics/{domain_name}/graph")
    suspend fun getGraphAnalytics(
        @Path("domain_name") domainName: String,
        @Query("analysis_type") analysisType: String,
        @Query("top_n") topN: Int = 10
    ): Map<String, Any>
}

// ============================================================================
// IOS CLIENT
// ============================================================================

class IOSClient(
    private val baseUrl: String = "http://10.0.2.2:8000" // Android emulator localhost
) {
    private var token: String? = null
    private var webSocket: WebSocket? = null
    private val _webSocketMessages = MutableStateFlow<WebSocketMessage?>(null)
    val webSocketMessages: Flow<WebSocketMessage?> = _webSocketMessages
    
    // HTTP Client
    private val okHttpClient: OkHttpClient by lazy {
        OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor())
            .addInterceptor(HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            })
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
    }
    
    // Retrofit
    private val retrofit: Retrofit by lazy {
        Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }
    
    private val api: IOSApiService by lazy {
        retrofit.create(IOSApiService::class.java)
    }
    
    // Auth Interceptor
    private inner class AuthInterceptor : Interceptor {
        override fun intercept(chain: Interceptor.Chain): Response {
            val originalRequest = chain.request()
            
            val requestBuilder = originalRequest.newBuilder()
            
            token?.let {
                requestBuilder.header("Authorization", "Bearer $it")
            }
            
            return chain.proceed(requestBuilder.build())
        }
    }
    
    // ========================================================================
    // AUTHENTICATION
    // ========================================================================
    
    suspend fun login(username: String, password: String): Boolean {
        return try {
            val response = api.login(LoginRequest(username, password))
            token = response.accessToken
            true
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }
    
    suspend fun logout() {
        try {
            api.logout()
            token = null
            disconnectWebSocket()
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
    
    fun isLoggedIn(): Boolean = token != null
    
    // ========================================================================
    // DOMAINS
    // ========================================================================
    
    suspend fun listDomains(): Result<List<String>> = runCatching {
        api.listDomains()
    }
    
    suspend fun createDomain(
        name: String,
        language: String = "de",
        description: String? = null,
        entityTypes: List<String> = emptyList()
    ): Result<DomainResponse> = runCatching {
        api.createDomain(DomainCreate(name, language, description, entityTypes))
    }
    
    suspend fun getDomain(domainName: String): Result<DomainResponse> = runCatching {
        api.getDomain(domainName)
    }
    
    // ========================================================================
    // DOCUMENTS
    // ========================================================================
    
    suspend fun uploadDocument(
        file: java.io.File,
        domainName: String,
        title: String? = null,
        author: String? = null,
        tags: List<String>? = null
    ): Result<DocumentResult> = runCatching {
        val requestFile = file.asRequestBody("application/octet-stream".toMediaTypeOrNull())
        val filePart = MultipartBody.Part.createFormData("file", file.name, requestFile)
        
        api.uploadDocument(filePart, domainName, title, author, tags)
    }
    
    // ========================================================================
    // SEARCH
    // ========================================================================
    
    suspend fun search(
        query: String,
        domainName: String? = null,
        searchType: String = "full_text",
        limit: Int = 10,
        offset: Int = 0,
        filters: Map<String, Any> = emptyMap(),
        ranking: String = "hybrid"
    ): Result<SearchResponse> = runCatching {
        api.search(SearchRequest(query, searchType, domainName, limit, offset, filters, ranking))
    }
    
    suspend fun autocomplete(
        prefix: String,
        domainName: String? = null,
        maxSuggestions: Int = 10
    ): Result<List<String>> = runCatching {
        api.autocomplete(prefix, domainName, maxSuggestions)
    }
    
    // ========================================================================
    // KNOWLEDGE GRAPH
    // ========================================================================
    
    suspend fun getGraphStatistics(domainName: String): Result<GraphStatistics> = runCatching {
        api.getGraphStatistics(domainName)
    }
    
    suspend fun listEntities(
        domainName: String,
        entityType: String? = null,
        limit: Int = 100,
        offset: Int = 0
    ): Result<List<EntityResponse>> = runCatching {
        api.listEntities(domainName, entityType, limit, offset)
    }
    
    suspend fun getEntity(
        domainName: String,
        entityId: String
    ): Result<EntityResponse> = runCatching {
        api.getEntity(domainName, entityId)
    }
    
    suspend fun getRelatedEntities(
        domainName: String,
        entityId: String,
        relationType: String? = null,
        direction: String = "both"
    ): Result<List<EntityResponse>> = runCatching {
        api.getRelatedEntities(domainName, entityId, relationType, direction)
    }
    
    // ========================================================================
    // CONTEXTS
    // ========================================================================
    
    suspend fun listContexts(): Result<List<ContextResponse>> = runCatching {
        api.listContexts()
    }
    
    suspend fun createContext(
        name: String,
        type: String,
        description: String? = null,
        activeDomains: List<String> = emptyList(),
        properties: Map<String, Any> = emptyMap()
    ): Result<ContextResponse> = runCatching {
        api.createContext(ContextCreate(name, type, description, activeDomains, properties))
    }
    
    suspend fun switchContext(contextId: String): Result<Map<String, Any>> = runCatching {
        api.switchContext(contextId)
    }
    
    // ========================================================================
    // ANALYTICS
    // ========================================================================
    
    suspend fun getGraphAnalytics(
        domainName: String,
        analysisType: String,
        topN: Int = 10
    ): Result<Map<String, Any>> = runCatching {
        api.getGraphAnalytics(domainName, analysisType, topN)
    }
    
    // ========================================================================
    // WEBSOCKET
    // ========================================================================
    
    fun connectWebSocket(userId: String) {
        val wsUrl = baseUrl
            .replace("http://", "ws://")
            .replace("https://", "wss://")
        
        val request = Request.Builder()
            .url("$wsUrl/ws/$userId")
            .build()
        
        webSocket = okHttpClient.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                println("WebSocket connected")
            }
            
            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val message = com.google.gson.Gson().fromJson(text, WebSocketMessage::class.java)
                    _webSocketMessages.value = message
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
            
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                println("WebSocket error: ${t.message}")
            }
            
            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                println("WebSocket closing: $reason")
            }
        })
    }
    
    fun subscribeToEvent(eventType: String) {
        webSocket?.send("""
            {
                "action": "subscribe",
                "event_type": "$eventType"
            }
        """.trimIndent())
    }
    
    fun unsubscribeFromEvent(eventType: String) {
        webSocket?.send("""
            {
                "action": "unsubscribe",
                "event_type": "$eventType"
            }
        """.trimIndent())
    }
    
    fun disconnectWebSocket() {
        webSocket?.close(1000, "Client disconnect")
        webSocket = null
    }
}
```

## 10.2 Android ViewModel и Repository

```kotlin
// android/IOSRepository.kt
/**
 * Repository для работы с IOS API
 */

package com.example.ios.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class IOSRepository(
    private val client: IOSClient
) {
    // ========================================================================
    // SEARCH
    // ========================================================================
    
    suspend fun search(
        query: String,
        domainName: String? = null,
        searchType: String = "hybrid"
    ): Result<SearchResponse> = withContext(Dispatchers.IO) {
        client.search(query, domainName, searchType)
    }
    
    suspend fun autocomplete(
        prefix: String,
        domainName: String? = null
    ): Result<List<String>> = withContext(Dispatchers.IO) {
        client.autocomplete(prefix, domainName)
    }
    
    // ========================================================================
    // KNOWLEDGE GRAPH
    // ========================================================================
    
    suspend fun getGraphStatistics(
        domainName: String
    ): Result<GraphStatistics> = withContext(Dispatchers.IO) {
        client.getGraphStatistics(domainName)
    }
    
    suspend fun listEntities(
        domainName: String,
        entityType: String? = null
    ): Result<List<EntityResponse>> = withContext(Dispatchers.IO) {
        client.listEntities(domainName, entityType)
    }
    
    suspend fun getEntity(
        domainName: String,
        entityId: String
    ): Result<EntityResponse> = withContext(Dispatchers.IO) {
        client.getEntity(domainName, entityId)
    }
    
    suspend fun getRelatedEntities(
        domainName: String,
        entityId: String
    ): Result<List<EntityResponse>> = withContext(Dispatchers.IO) {
        client.getRelatedEntities(domainName, entityId)
    }
}


// android/SearchViewModel.kt
/**
 * ViewModel для экрана поиска
 */

package com.example.ios.ui.search

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

data class SearchUiState(
    val query: String = "",
    val results: List<DocumentResult> = emptyList(),
    val suggestions: List<String> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null
)

class SearchViewModel(
    private val repository: IOSRepository
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(SearchUiState())
    val uiState: StateFlow<SearchUiState> = _uiState.asStateFlow()
    
    fun updateQuery(query: String) {
        _uiState.update { it.copy(query = query) }
        
        // Автодополнение
        if (query.length >= 2) {
            loadSuggestions(query)
        }
    }
    
    fun search(searchType: String = "hybrid") {
        val query = _uiState.value.query
        
        if (query.isBlank()) return
        
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            
            repository.search(query, searchType = searchType)
                .onSuccess { response ->
                    _uiState.update {
                        it.copy(
                            results = response.results,
                            isLoading = false
                        )
                    }
                }
                .onFailure { error ->
                    _uiState.update {
                        it.copy(
                            error = error.message,
                            isLoading = false
                        )
                    }
                }
        }
    }
    
    private fun loadSuggestions(prefix: String) {
        viewModelScope.launch {
            repository.autocomplete(prefix)
                .onSuccess { suggestions ->
                    _uiState.update { it.copy(suggestions = suggestions) }
                }
                .onFailure { error ->
                    // Игнорировать ошибки автодополнения
                }
        }
    }
}


// android/KnowledgeGraphViewModel.kt
/**
 * ViewModel для графа знаний
 */

package com.example.ios.ui.graph

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

data class GraphUiState(
    val statistics: GraphStatistics? = null,
    val entities: List<EntityResponse> = emptyList(),
    val selectedEntity: EntityResponse? = null,
    val relatedEntities: List<EntityResponse> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null
)

class KnowledgeGraphViewModel(
    private val repository: IOSRepository,
    private val domainName: String
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(GraphUiState())
    val uiState: StateFlow<GraphUiState> = _uiState.asStateFlow()
    
    init {
        loadStatistics()
    }
    
    fun loadStatistics() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            
            repository.getGraphStatistics(domainName)
                .onSuccess { stats ->
                    _uiState.update {
                        it.copy(
                            statistics = stats,
                            isLoading = false
                        )
                    }
                }
                .onFailure { error ->
                    _uiState.update {
                        it.copy(
                            error = error.message,
                            isLoading = false
                        )
                    }
                }
        }
    }
    
    fun loadEntities(entityType: String? = null) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            
            repository.listEntities(domainName, entityType)
                .onSuccess { entities ->
                    _uiState.update {
                        it.copy(
                            entities = entities,
                            isLoading = false
                        )
                    }
                }
                .onFailure { error ->
                    _uiState.update {
                        it.copy(
                            error = error.message,
                            isLoading = false
                        )
                    }
                }
        }
    }
    
    fun selectEntity(entity: EntityResponse) {
        _uiState.update { it.copy(selectedEntity = entity) }
        loadRelatedEntities(entity.id)
    }
    
    private fun loadRelatedEntities(entityId: String) {
        viewModelScope.launch {
            repository.getRelatedEntities(domainName, entityId)
                .onSuccess { related ->
                    _uiState.update { it.copy(relatedEntities = related) }
                }
                .onFailure { error ->
                    _uiState.update { it.copy(error = error.message) }
                }
        }
    }
}
```

## 10.3 Android UI с Jetpack Compose

```kotlin
// android/SearchScreen.kt
/**
 * Экран поиска документов
 */

package com.example.ios.ui.search

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SearchScreen(
    viewModel: SearchViewModel,
    modifier: Modifier = Modifier
) {
    val uiState by viewModel.uiState.collectAsState()
    
    Column(modifier = modifier.fillMaxSize()) {
        // Search bar
        SearchBar(
            query = uiState.query,
            onQueryChange = { viewModel.updateQuery(it) },
            onSearch = { viewModel.search() },
            suggestions = uiState.suggestions,
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        )
        
        // Search type selector
        SearchTypeSelector(
            onTypeSelected = { viewModel.search(it) },
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp)
        )
        
        // Results
        if (uiState.isLoading) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = androidx.compose.ui.Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else if (uiState.error != null) {
            Text(
                text = "Error: ${uiState.error}",
                color = MaterialTheme.colorScheme.error,
                modifier = Modifier.padding(16.dp)
            )
        } else {
            SearchResults(
                results = uiState.results,
                modifier = Modifier.fillMaxSize()
            )
        }
    }
}

@Composable
fun SearchBar(
    query: String,
    onQueryChange: (String) -> Unit,
    onSearch: () -> Unit,
    suggestions: List<String>,
    modifier: Modifier = Modifier
) {
    var expanded by remember { mutableStateOf(false) }
    
    Column(modifier = modifier) {
        OutlinedTextField(
            value = query,
            onValueChange = {
                onQueryChange(it)
                expanded = it.isNotEmpty() && suggestions.isNotEmpty()
            },
            label = { Text("Search") },
            trailingIcon = {
                IconButton(onClick = onSearch) {
                    Icon(Icons.Default.Search, "Search")
                }
            },
            modifier = Modifier.fillMaxWidth()
        )
        
        // Suggestions dropdown
        if (expanded) {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 4.dp)
            ) {
                LazyColumn {
                    items(suggestions) { suggestion ->
                        Text(
                            text = suggestion,
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable {
                                    onQueryChange(suggestion)
                                    expanded = false
                                    onSearch()
                                }
                                .padding(16.dp)
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun SearchTypeSelector(
    onTypeSelected: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    var selectedType by remember { mutableStateOf("hybrid") }
    
    Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        FilterChip(
            selected = selectedType == "full_text",
            onClick = {
                selectedType = "full_text"
                onTypeSelected("full_text")
            },
            label = { Text("Full Text") }
        )
        
        FilterChip(
            selected = selectedType == "semantic",
            onClick = {
                selectedType = "semantic"
                onTypeSelected("semantic")
            },
            label = { Text("Semantic") }
        )
        
        FilterChip(
            selected = selectedType == "hybrid",
            onClick = {
                selectedType = "hybrid"
                onTypeSelected("hybrid")
            },
            label = { Text("Hybrid") }
        )
    }
}

@Composable
fun SearchResults(
    results: List<DocumentResult>,
    modifier: Modifier = Modifier
) {
    LazyColumn(modifier = modifier) {
        items(results) { result ->
            SearchResultItem(result = result)
            Divider()
        }
    }
}

@Composable
fun SearchResultItem(
    result: DocumentResult,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .padding(8.dp)
            .clickable { /* Navigate to document */ }
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = result.title,
                style = MaterialTheme.typography.titleMedium
            )
            
            Spacer(modifier = Modifier.height(4.dp))
            
            Row {
                AssistChip(
                    onClick = { },
                    label = { Text(result.documentType) }
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "Score: ${String.format("%.3f", result.score)}",
                    style = MaterialTheme.typography.bodySmall
                )
            }
            
            result.highlights?.let {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = it,
                    style = MaterialTheme.typography.bodySmall,
                    maxLines = 3
                )
            }
        }
    }
}
```

## 10.4 Docker Deployment

```dockerfile
# Dockerfile
# Dockerfile для IOS API сервера

FROM python:3.11-slim

# Установить системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копировать requirements
COPY requirements.txt .

# Установить Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копировать код приложения
COPY . .

# Создать директории для данных
RUN mkdir -p /data/ios-root \
    /data/uploads \
    /data/exports

# Переменные окружения
ENV IOS_ROOT_PATH=/data/ios-root \
    PYTHONUNBUFFERED=1 \
    SECRET_KEY=change-this-in-production

# Открыть порт
EXPOSE 8000

# Команда запуска
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
# Docker Compose конфигурация для полного стека IOS

version: '3.8'

services:
  # ========================================================================
  # IOS API Server
  # ========================================================================
  ios-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ios-api
    ports:
      - "8000:8000"
    volumes:
      - ios-data:/data/ios-root
      - ios-uploads:/data/uploads
      - ios-exports:/data/exports
      - ./logs:/app/logs
    environment:
      - IOS_ROOT_PATH=/data/ios-root
      - SECRET_KEY=${SECRET_KEY:-your-secret-key-change-in-production}
      - DATABASE_URL=postgresql://ios_user:ios_password@postgres:5432/ios_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - ios-network
    restart: unless-stopped

  # ========================================================================
  # PostgreSQL Database
  # ========================================================================
  postgres:
    image: postgres:15-alpine
    container_name: ios-postgres
    environment:
      - POSTGRES_DB=ios_db
      - POSTGRES_USER=ios_user
      - POSTGRES_PASSWORD=ios_password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - ios-network
    restart: unless-stopped

  # ========================================================================
  # Redis Cache
  # ========================================================================
  redis:
    image: redis:7-alpine
    container_name: ios-redis
    volumes:
      - redis-data:/data
    networks:
      - ios-network
    restart: unless-stopped

  # ========================================================================
  # Nginx Reverse Proxy
  # ========================================================================
  nginx:
    image: nginx:alpine
    container_name: ios-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ios-exports:/usr/share/nginx/html/exports:ro
    depends_on:
      - ios-api
    networks:
      - ios-network
    restart: unless-stopped

  # ========================================================================
  # ElasticSearch (опционально для продвинутого поиска)
  # ========================================================================
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: ios-elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    networks:
      - ios-network
    restart: unless-stopped

  # ========================================================================
  # Monitoring (опционально)
  # ========================================================================
  grafana:
    image: grafana/grafana:latest
    container_name: ios-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - ios-network
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    container_name: ios-prometheus
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    networks:
      - ios-network
    restart: unless-stopped

# ============================================================================
# VOLUMES
# ============================================================================
volumes:
  ios-data:
    driver: local
  ios-uploads:
    driver: local
  ios-exports:
    driver: local
  postgres-data:
    driver: local
  redis-data:
    driver: local
  elasticsearch-data:
    driver: local
  grafana-data:
    driver: local
  prometheus-data:
    driver: local

# ============================================================================
# NETWORKS
# ============================================================================
networks:
  ios-network:
    driver: bridge
```

```nginx
# nginx/nginx.conf
# Nginx конфигурация для IOS

events {
    worker_connections 1024;
}

http {
    upstream ios_api {
        server ios-api:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    server {
        listen 80;
        server_name localhost;

        client_max_body_size 100M;

        # API endpoints
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://ios_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # CORS headers
            add_header Access-Control-Allow-Origin * always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
            
            if ($request_method = OPTIONS) {
                return 204;
            }
        }

        # WebSocket
        location /ws/ {
            proxy_pass http://ios_api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Static exports
        location /exports/ {
            alias /usr/share/nginx/html/exports/;
            autoindex on;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

```python
# requirements.txt
# Python зависимости для IOS

fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.0

# Caching
redis==5.0.1

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# HTTP clients
httpx==0.25.2
requests==2.31.0

# WebSocket
websockets==12.0

# Search & NLP
whoosh==2.7.4
scikit-learn==1.3.2
numpy==1.26.2

# Graph processing
networkx==3.2.1
python-louvain==0.16

# Visualization
matplotlib==3.8.2
plotly==5.18.0

# Document processing
python-docx==1.1.0
PyPDF2==3.0.1
openpyxl==3.1.2
python-pptx==0.6.23

# Utilities
python-dotenv==1.0.0
aiofiles==23.2.1
```

Продолжить с deployment инструкциями и финальной интеграцией?