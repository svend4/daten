/**
 * Documents Resource
 */

import { AxiosInstance } from 'axios';
import {
  Document,
  CreateDocumentRequest,
  UpdateDocumentRequest,
  ListDocumentsOptions
} from '../types';

export class DocumentsResource {
  constructor(private axios: AxiosInstance) {}
  
  /**
   * List documents
   */
  async list(options?: ListDocumentsOptions): Promise<Document[]> {
    const { data } = await this.axios.get('/api/documents', {
      params: options
    });
    
    return data.documents;
  }
  
  /**
   * Get document by ID
   */
  async get(documentId: string): Promise<Document> {
    const { data } = await this.axios.get(`/api/documents/${documentId}`);
    return data;
  }
  
  /**
   * Create document
   */
  async create(request: CreateDocumentRequest): Promise<Document> {
    const { data } = await this.axios.post('/api/documents', request);
    return data;
  }
  
  /**
   * Update document
   */
  async update(
    documentId: string,
    request: UpdateDocumentRequest
  ): Promise<Document> {
    const { data } = await this.axios.patch(
      `/api/documents/${documentId}`,
      request
    );
    return data;
  }
  
  /**
   * Delete document
   */
  async delete(documentId: string): Promise<void> {
    await this.axios.delete(`/api/documents/${documentId}`);
  }
}