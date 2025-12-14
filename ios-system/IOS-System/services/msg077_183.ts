/**
 * SDK Types
 */

export interface Document {
  id: string;
  title: string;
  content: string;
  domain_id?: string;
  metadata?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface CreateDocumentRequest {
  title: string;
  content: string;
  domain_id?: string;
  metadata?: Record<string, any>;
}

export interface UpdateDocumentRequest {
  title?: string;
  content?: string;
  metadata?: Record<string, any>;
}

export interface ListDocumentsOptions {
  limit?: number;
  offset?: number;
  domain_id?: string;
  search?: string;
}

export interface SearchResult {
  document_id: string;
  title: string;
  content: string;
  score: number;
  highlight?: string;
  metadata?: Record<string, any>;
}

export interface SearchOptions {
  limit?: number;
  domain_id?: string;
  score_threshold?: number;
  threshold?: number;
}

export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  roles: string[];
  created_at?: string;
}

export interface Webhook {
  id: string;
  name: string;
  url: string;
  event_types: string[];
  is_active: boolean;
  secret?: string;
  created_at?: string;
}

export interface WebhookOptions {
  name: string;
  url: string;
  event_types: string[];
  secret?: string;
}