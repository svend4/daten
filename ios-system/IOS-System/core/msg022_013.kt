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