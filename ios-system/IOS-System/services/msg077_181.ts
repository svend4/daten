/**
 * IOS System JavaScript/TypeScript SDK
 * Official client for IOS API
 * 
 * Installation:
 *   npm install @ios-system/sdk
 * 
 * Usage:
 *   import { IOSClient } from '@ios-system/sdk';
 *   
 *   const client = new IOSClient({ apiKey: 'sk_test_...' });
 *   
 *   const doc = await client.documents.create({
 *     title: 'My Document',
 *     content: 'Content here'
 *   });
 */

export { IOSClient } from './client';
export { IOSError, AuthenticationError, RateLimitError, NotFoundError } from './errors';
export type {
  Document,
  SearchResult,
  User,
  Webhook,
  CreateDocumentRequest,
  UpdateDocumentRequest,
  SearchOptions,
  WebhookOptions
} from './types';