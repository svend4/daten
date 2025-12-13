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