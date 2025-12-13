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