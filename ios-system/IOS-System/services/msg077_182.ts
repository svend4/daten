/**
 * Search Resource
 */

import { AxiosInstance } from 'axios';
import { SearchResult, SearchOptions } from '../types';

export class SearchResource {
  constructor(private axios: AxiosInstance) {}
  
  /**
   * Basic search
   */
  async query(
    query: string,
    options?: SearchOptions
  ): Promise<SearchResult[]> {
    const { data } = await this.axios.get('/api/search', {
      params: { query, ...options }
    });
    
    return data.results;
  }
  
  /**
   * Neural search (hybrid)
   */
  async neural(
    query: string,
    options?: SearchOptions
  ): Promise<SearchResult[]> {
    const { data } = await this.axios.get('/api/search/neural', {
      params: { query, ...options }
    });
    
    return data.results;
  }
  
  /**
   * Semantic search (embeddings)
   */
  async semantic(
    query: string,
    options?: SearchOptions
  ): Promise<SearchResult[]> {
    const { data } = await this.axios.get('/api/semantic/search', {
      params: { query, ...options }
    });
    
    return data.results;
  }
}