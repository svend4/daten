/**
 * IOS Client
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import { DocumentsResource } from './resources/documents';
import { SearchResource } from './resources/search';
import { WebhooksResource } from './resources/webhooks';
import { UsersResource } from './resources/users';
import {
  IOSError,
  AuthenticationError,
  RateLimitError,
  NotFoundError,
  ServerError
} from './errors';

export interface IOSClientOptions {
  apiKey: string;
  baseURL?: string;
  timeout?: number;
}

export class IOSClient {
  private axios: AxiosInstance;
  
  public documents: DocumentsResource;
  public search: SearchResource;
  public webhooks: WebhooksResource;
  public users: UsersResource;
  
  constructor(options: IOSClientOptions) {
    const {
      apiKey,
      baseURL = 'https://api.ios-system.com',
      timeout = 30000
    } = options;
    
    // Initialize axios
    this.axios = axios.create({
      baseURL,
      timeout,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'User-Agent': 'ios-sdk-js/1.0.0'
      }
    });
    
    // Add error interceptor
    this.axios.interceptors.response.use(
      response => response,
      error => this.handleError(error)
    );
    
    // Initialize resources
    this.documents = new DocumentsResource(this.axios);
    this.search = new SearchResource(this.axios);
    this.webhooks = new WebhooksResource(this.axios);
    this.users = new UsersResource(this.axios);
  }
  
  private handleError(error: AxiosError): never {
    if (!error.response) {
      throw new IOSError('Network error');
    }
    
    const { status, data } = error.response;
    const message = (data as any)?.detail || 'Unknown error';
    
    switch (status) {
      case 401:
        throw new AuthenticationError(message);
      
      case 404:
        throw new NotFoundError(message);
      
      case 429:
        const retryAfter = error.response.headers['retry-after'];
        throw new RateLimitError(message, retryAfter);
      
      case 500:
      case 502:
      case 503:
        throw new ServerError(message);
      
      default:
        throw new IOSError(`HTTP ${status}: ${message}`);
    }
  }
}