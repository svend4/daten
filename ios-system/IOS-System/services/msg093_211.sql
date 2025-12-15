-- Database Index Optimization Script
-- Creates optimized indexes for IOS System

-- ============================================
-- Documents Table
-- ============================================

-- Primary key already exists
-- CREATE UNIQUE INDEX idx_documents_pk ON documents(id);

-- Title search (frequently used in search)
CREATE INDEX CONCURRENTLY idx_documents_title 
ON documents USING gin(to_tsvector('english', title));

-- Content full-text search
CREATE INDEX CONCURRENTLY idx_documents_content_fts 
ON documents USING gin(to_tsvector('english', content));

-- Domain filter (frequently used)
CREATE INDEX CONCURRENTLY idx_documents_domain_id 
ON documents(domain_id) WHERE domain_id IS NOT NULL;

-- Created date for sorting and filtering
CREATE INDEX CONCURRENTLY idx_documents_created_at 
ON documents(created_at DESC);

-- Updated date for sorting
CREATE INDEX CONCURRENTLY idx_documents_updated_at 
ON documents(updated_at DESC);

-- User ownership
CREATE INDEX CONCURRENTLY idx_documents_user_id 
ON documents(user_id);

-- Composite index for common query pattern
CREATE INDEX CONCURRENTLY idx_documents_user_created 
ON documents(user_id, created_at DESC);

-- Status filter
CREATE INDEX CONCURRENTLY idx_documents_status 
ON documents(status) WHERE status IS NOT NULL;

-- Partial index for active documents only
CREATE INDEX CONCURRENTLY idx_documents_active 
ON documents(id, title, created_at) 
WHERE status = 'active';

-- ============================================
-- Domains Table
-- ============================================

-- Name search
CREATE INDEX CONCURRENTLY idx_domains_name 
ON domains(name);

-- Hierarchy (parent-child relationships)
CREATE INDEX CONCURRENTLY idx_domains_parent_id 
ON domains(parent_id) WHERE parent_id IS NOT NULL;

-- Path for hierarchical queries
CREATE INDEX CONCURRENTLY idx_domains_path 
ON domains USING gist(path);

-- ============================================
-- Users Table
-- ============================================

-- Email lookup (used in authentication)
CREATE UNIQUE INDEX CONCURRENTLY idx_users_email 
ON users(LOWER(email));

-- Username lookup
CREATE UNIQUE INDEX CONCURRENTLY idx_users_username 
ON users(LOWER(username));

-- Active users filter
CREATE INDEX CONCURRENTLY idx_users_active 
ON users(id, email, username) 
WHERE is_active = true;

-- Role-based queries
CREATE INDEX CONCURRENTLY idx_users_role 
ON users(role);

-- ============================================
-- Search History Table
-- ============================================

-- User's search history
CREATE INDEX CONCURRENTLY idx_search_history_user_id 
ON search_history(user_id, created_at DESC);

-- Query text for analytics
CREATE INDEX CONCURRENTLY idx_search_history_query 
ON search_history USING gin(to_tsvector('english', query));

-- Recent searches (30 days)
CREATE INDEX CONCURRENTLY idx_search_history_recent 
ON search_history(user_id, created_at DESC) 
WHERE created_at > NOW() - INTERVAL '30 days';

-- ============================================
-- Audit Logs Table
-- ============================================

-- User actions
CREATE INDEX CONCURRENTLY idx_audit_logs_user_id 
ON audit_logs(user_id, created_at DESC);

-- Action type filter
CREATE INDEX CONCURRENTLY idx_audit_logs_action 
ON audit_logs(action);

-- Entity tracking
CREATE INDEX CONCURRENTLY idx_audit_logs_entity 
ON audit_logs(entity_type, entity_id);

-- Time-based queries
CREATE INDEX CONCURRENTLY idx_audit_logs_created_at 
ON audit_logs(created_at DESC);

-- Recent logs (7 days) - partial index
CREATE INDEX CONCURRENTLY idx_audit_logs_recent 
ON audit_logs(user_id, action, created_at DESC) 
WHERE created_at > NOW() - INTERVAL '7 days';

-- ============================================
-- Sessions Table
-- ============================================

-- Token lookup
CREATE UNIQUE INDEX CONCURRENTLY idx_sessions_token 
ON sessions(token);

-- User sessions
CREATE INDEX CONCURRENTLY idx_sessions_user_id 
ON sessions(user_id, created_at DESC);

-- Active sessions only
CREATE INDEX CONCURRENTLY idx_sessions_active 
ON sessions(user_id, expires_at) 
WHERE expires_at > NOW();

-- Cleanup expired sessions
CREATE INDEX CONCURRENTLY idx_sessions_expired 
ON sessions(expires_at) 
WHERE expires_at <= NOW();

-- ============================================
-- Tags Table
-- ============================================

-- Tag name
CREATE INDEX CONCURRENTLY idx_tags_name 
ON tags(LOWER(name));

-- Tag usage count
CREATE INDEX CONCURRENTLY idx_tags_usage_count 
ON tags(usage_count DESC);

-- ============================================
-- Document Tags Join Table
-- ============================================

-- Document's tags
CREATE INDEX CONCURRENTLY idx_document_tags_document_id 
ON document_tags(document_id);

-- Tag's documents
CREATE INDEX CONCURRENTLY idx_document_tags_tag_id 
ON document_tags(tag_id);

-- Composite for join queries
CREATE INDEX CONCURRENTLY idx_document_tags_composite 
ON document_tags(document_id, tag_id);

-- ============================================
-- Comments Table
-- ============================================

-- Document comments
CREATE INDEX CONCURRENTLY idx_comments_document_id 
ON comments(document_id, created_at DESC);

-- User comments
CREATE INDEX CONCURRENTLY idx_comments_user_id 
ON comments(user_id, created_at DESC);

-- Parent-child relationships (threaded comments)
CREATE INDEX CONCURRENTLY idx_comments_parent_id 
ON comments(parent_id) WHERE parent_id IS NOT NULL;

-- ============================================
-- Notifications Table
-- ============================================

-- User notifications
CREATE INDEX CONCURRENTLY idx_notifications_user_id 
ON notifications(user_id, created_at DESC);

-- Unread notifications
CREATE INDEX CONCURRENTLY idx_notifications_unread 
ON notifications(user_id, created_at DESC) 
WHERE is_read = false;

-- ============================================
-- API Keys Table
-- ============================================

-- Key lookup
CREATE UNIQUE INDEX CONCURRENTLY idx_api_keys_key 
ON api_keys(key_hash);

-- User's API keys
CREATE INDEX CONCURRENTLY idx_api_keys_user_id 
ON api_keys(user_id);

-- Active keys only
CREATE INDEX CONCURRENTLY idx_api_keys_active 
ON api_keys(user_id, created_at DESC) 
WHERE is_active = true;

-- ============================================
-- Webhooks Table
-- ============================================

-- User webhooks
CREATE INDEX CONCURRENTLY idx_webhooks_user_id 
ON webhooks(user_id);

-- Active webhooks
CREATE INDEX CONCURRENTLY idx_webhooks_active 
ON webhooks(id, url, event_types) 
WHERE is_active = true;

-- ============================================
-- Analytics Table
-- ============================================

-- Time-series data
CREATE INDEX CONCURRENTLY idx_analytics_timestamp 
ON analytics(timestamp DESC);

-- Metric queries
CREATE INDEX CONCURRENTLY idx_analytics_metric 
ON analytics(metric_name, timestamp DESC);

-- Composite for metric queries with filters
CREATE INDEX CONCURRENTLY idx_analytics_composite 
ON analytics(metric_name, entity_type, timestamp DESC);

-- ============================================
-- Verify Indexes
-- ============================================

-- Show all indexes with sizes
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM
    pg_stat_user_indexes
ORDER BY
    pg_relation_size(indexrelid) DESC;

-- Show unused indexes (scanned less than 100 times)
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM
    pg_stat_user_indexes
WHERE
    idx_scan < 100
    AND indexname NOT LIKE '%_pkey'
ORDER BY
    pg_relation_size(indexrelid) DESC;