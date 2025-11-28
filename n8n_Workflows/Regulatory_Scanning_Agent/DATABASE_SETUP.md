# Database Setup Guide

Complete PostgreSQL database schema and setup instructions for the Mycroft Financial Regulatory Intelligence System.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Database Schema](#database-schema)
- [Setup Instructions](#setup-instructions)
- [Indexes](#indexes)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- PostgreSQL 12 or higher
- JSONB support enabled (default in PostgreSQL 9.4+)
- Database user with CREATE TABLE privileges

## Database Schema

### Main Table: `regulatory_feeds`

```sql
CREATE TABLE IF NOT EXISTS regulatory_feeds (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Source Information
    source_feed VARCHAR(255) NOT NULL,
    source VARCHAR(255) NOT NULL,
    
    -- Content Fields
    title TEXT NOT NULL,
    link TEXT NOT NULL UNIQUE,
    published TIMESTAMP WITH TIME ZONE NOT NULL,
    content TEXT,
    
    -- Analysis Results
    urgency_score INTEGER NOT NULL CHECK (urgency_score >= 1 AND urgency_score <= 10),
    impact_level VARCHAR(20) NOT NULL CHECK (impact_level IN ('Critical', 'High', 'Medium', 'Low')),
    
    -- Keyword Analysis (JSONB for flexible querying)
    keyword_matches JSONB NOT NULL DEFAULT '{}',
    categories JSONB NOT NULL DEFAULT '[]',
    
    -- Metadata
    word_count INTEGER,
    has_deadline BOOLEAN DEFAULT FALSE,
    is_enforcement BOOLEAN DEFAULT FALSE,
    
    -- Email Tracking
    email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    scraped_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | SERIAL | Auto-incrementing primary key |
| `source_feed` | VARCHAR(255) | Identified feed source (e.g., "SEC Press Releases") |
| `source` | VARCHAR(255) | Original creator/author from RSS feed |
| `title` | TEXT | Article/regulation title |
| `link` | TEXT | Unique URL (used for deduplication) |
| `published` | TIMESTAMPTZ | Original publication date from feed |
| `content` | TEXT | Full content/description from feed |
| `urgency_score` | INTEGER | Calculated priority score (1-10) |
| `impact_level` | VARCHAR(20) | Classification: Critical, High, Medium, Low |
| `keyword_matches` | JSONB | Boolean flags for each category match |
| `categories` | JSONB | Array of matched category names |
| `word_count` | INTEGER | Content length in words |
| `has_deadline` | BOOLEAN | Whether item mentions compliance deadline |
| `is_enforcement` | BOOLEAN | Whether item is enforcement-related |
| `email_sent` | BOOLEAN | Email notification status |
| `email_sent_at` | TIMESTAMPTZ | Timestamp of email notification |
| `scraped_at` | TIMESTAMPTZ | When item was collected by workflow |
| `created_at` | TIMESTAMPTZ | Database insertion timestamp |
| `updated_at` | TIMESTAMPTZ | Last update timestamp |

### JSONB Field Structures

#### `keyword_matches` Example
```json
{
  "enforcement": true,
  "compliance": false,
  "crypto": false,
  "securities": true,
  "derivatives": false,
  "fraud": false
}
```

#### `categories` Example
```json
["enforcement", "securities"]
```

## Setup Instructions

### Step 1: Create Database

```sql
-- Create database (if not exists)
CREATE DATABASE mycroft_intelligence;

-- Connect to database
\c mycroft_intelligence
```

### Step 2: Create Table

```sql
-- Create main table
CREATE TABLE IF NOT EXISTS regulatory_feeds (
    id SERIAL PRIMARY KEY,
    source_feed VARCHAR(255) NOT NULL,
    source VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    link TEXT NOT NULL UNIQUE,
    published TIMESTAMP WITH TIME ZONE NOT NULL,
    content TEXT,
    urgency_score INTEGER NOT NULL CHECK (urgency_score >= 1 AND urgency_score <= 10),
    impact_level VARCHAR(20) NOT NULL CHECK (impact_level IN ('Critical', 'High', 'Medium', 'Low')),
    keyword_matches JSONB NOT NULL DEFAULT '{}',
    categories JSONB NOT NULL DEFAULT '[]',
    word_count INTEGER,
    has_deadline BOOLEAN DEFAULT FALSE,
    is_enforcement BOOLEAN DEFAULT FALSE,
    email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP WITH TIME ZONE,
    scraped_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Step 3: Create Indexes

```sql
-- Index on link for fast duplicate checking
CREATE UNIQUE INDEX idx_regulatory_feeds_link ON regulatory_feeds(link);

-- Index on urgency and impact for priority queries
CREATE INDEX idx_regulatory_feeds_urgency ON regulatory_feeds(urgency_score DESC);
CREATE INDEX idx_regulatory_feeds_impact ON regulatory_feeds(impact_level);

-- Index on email tracking for unsent items query
CREATE INDEX idx_regulatory_feeds_email_sent ON regulatory_feeds(email_sent, created_at DESC)
WHERE email_sent = FALSE;

-- Index on timestamps for date-range queries
CREATE INDEX idx_regulatory_feeds_created_at ON regulatory_feeds(created_at DESC);
CREATE INDEX idx_regulatory_feeds_published ON regulatory_feeds(published DESC);

-- Index on enforcement flag for filtering
CREATE INDEX idx_regulatory_feeds_enforcement ON regulatory_feeds(is_enforcement)
WHERE is_enforcement = TRUE;

-- GIN index on JSONB fields for fast keyword queries
CREATE INDEX idx_regulatory_feeds_keyword_matches ON regulatory_feeds USING GIN (keyword_matches);
CREATE INDEX idx_regulatory_feeds_categories ON regulatory_feeds USING GIN (categories);

-- Composite index for priority email queries
CREATE INDEX idx_regulatory_feeds_priority_unsent 
ON regulatory_feeds(urgency_score DESC, impact_level, created_at DESC)
WHERE email_sent = FALSE;
```

### Step 4: Create Update Trigger

```sql
-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to call function on updates
CREATE TRIGGER update_regulatory_feeds_updated_at
BEFORE UPDATE ON regulatory_feeds
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

### Step 5: Create Helper Views (Optional)

```sql
-- View for high priority items
CREATE VIEW high_priority_feeds AS
SELECT * FROM regulatory_feeds
WHERE urgency_score > 7 OR impact_level IN ('Critical', 'High')
ORDER BY urgency_score DESC, created_at DESC;

-- View for unsent high priority items
CREATE VIEW unsent_priority_alerts AS
SELECT * FROM regulatory_feeds
WHERE (urgency_score > 7 OR impact_level IN ('Critical', 'High'))
  AND email_sent = FALSE
  AND created_at >= NOW() - INTERVAL '1 day'
ORDER BY urgency_score DESC, created_at DESC;

-- View for enforcement actions
CREATE VIEW enforcement_actions AS
SELECT * FROM regulatory_feeds
WHERE is_enforcement = TRUE
ORDER BY created_at DESC;

-- View for items with deadlines
CREATE VIEW deadline_items AS
SELECT * FROM regulatory_feeds
WHERE has_deadline = TRUE
ORDER BY created_at DESC;
```

## Indexes

### Performance Optimization

The indexes are designed for common query patterns:

1. **Link Uniqueness**: Prevents duplicate entries efficiently
2. **Priority Queries**: Fast retrieval of high-urgency items
3. **Email Tracking**: Optimizes unsent items lookup
4. **Date Ranges**: Efficient filtering by time periods
5. **JSONB Queries**: Fast keyword category searches
6. **Composite Indexes**: Optimized for multi-condition queries

### Index Maintenance

```sql
-- Check index usage statistics
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = 'regulatory_feeds'
ORDER BY idx_scan DESC;

-- Rebuild indexes if needed
REINDEX TABLE regulatory_feeds;
```

## Maintenance

### Vacuum and Analyze

```sql
-- Regular maintenance (run weekly)
VACUUM ANALYZE regulatory_feeds;

-- Full vacuum (run monthly, requires table lock)
VACUUM FULL regulatory_feeds;
```

### Data Retention Policy

```sql
-- Example: Delete items older than 2 years
DELETE FROM regulatory_feeds
WHERE created_at < NOW() - INTERVAL '2 years';

-- Or archive to another table
CREATE TABLE regulatory_feeds_archive AS
SELECT * FROM regulatory_feeds
WHERE created_at < NOW() - INTERVAL '2 years';

DELETE FROM regulatory_feeds
WHERE created_at < NOW() - INTERVAL '2 years';
```

### Backup Strategy

```bash
# Backup database
pg_dump -U your_user -d mycroft_intelligence -F c -b -v -f "mycroft_backup_$(date +%Y%m%d).backup"

# Restore from backup
pg_restore -U your_user -d mycroft_intelligence -v "mycroft_backup_20240115.backup"
```

## Useful Queries

### Query Examples

```sql
-- Get today's high priority items
SELECT source_feed, title, urgency_score, impact_level, link
FROM regulatory_feeds
WHERE created_at >= CURRENT_DATE
  AND (urgency_score > 7 OR impact_level IN ('Critical', 'High'))
ORDER BY urgency_score DESC;

-- Count items by source feed
SELECT source_feed, COUNT(*) as item_count
FROM regulatory_feeds
GROUP BY source_feed
ORDER BY item_count DESC;

-- Find enforcement actions in last 7 days
SELECT title, source_feed, published, link
FROM regulatory_feeds
WHERE is_enforcement = TRUE
  AND created_at >= NOW() - INTERVAL '7 days'
ORDER BY published DESC;

-- Get items matching specific keyword category
SELECT title, categories, urgency_score
FROM regulatory_feeds
WHERE keyword_matches->>'crypto' = 'true'
  AND created_at >= NOW() - INTERVAL '30 days'
ORDER BY urgency_score DESC;

-- Email notification statistics
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_items,
    SUM(CASE WHEN email_sent THEN 1 ELSE 0 END) as emailed_items,
    AVG(urgency_score) as avg_urgency
FROM regulatory_feeds
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Top categories by frequency
SELECT 
    jsonb_array_elements_text(categories) as category,
    COUNT(*) as frequency
FROM regulatory_feeds
WHERE created_at >= NOW() - INTERVAL '90 days'
GROUP BY category
ORDER BY frequency DESC;
```

## Troubleshooting

### Common Issues

#### Issue: Duplicate Key Error
```
ERROR: duplicate key value violates unique constraint "idx_regulatory_feeds_link"
```

**Solution**: The workflow handles this with `ON CONFLICT (link) DO UPDATE`. Ensure the n8n workflow uses this upsert pattern.

#### Issue: JSONB Query Not Using Index
```sql
-- Bad (doesn't use GIN index)
SELECT * FROM regulatory_feeds WHERE keyword_matches::text LIKE '%enforcement%';

-- Good (uses GIN index)
SELECT * FROM regulatory_feeds WHERE keyword_matches->>'enforcement' = 'true';
```

#### Issue: Slow Priority Queries

**Solution**: Ensure composite index exists:
```sql
CREATE INDEX IF NOT EXISTS idx_regulatory_feeds_priority_unsent 
ON regulatory_feeds(urgency_score DESC, impact_level, created_at DESC)
WHERE email_sent = FALSE;
```

#### Issue: Table Bloat

**Solution**: Run VACUUM FULL during maintenance window:
```sql
VACUUM FULL regulatory_feeds;
```

### Connection Testing

```sql
-- Test database connection
SELECT version();

-- Verify table exists
SELECT COUNT(*) FROM regulatory_feeds;

-- Check recent inserts
SELECT id, title, created_at 
FROM regulatory_feeds 
ORDER BY created_at DESC 
LIMIT 5;
```

## Security Considerations

### Recommended Permissions

```sql
-- Create read-only user for reporting
CREATE USER mycroft_readonly WITH PASSWORD 'your_secure_password';
GRANT CONNECT ON DATABASE mycroft_intelligence TO mycroft_readonly;
GRANT SELECT ON regulatory_feeds TO mycroft_readonly;

-- Create application user with limited permissions
CREATE USER mycroft_app WITH PASSWORD 'your_secure_password';
GRANT CONNECT ON DATABASE mycroft_intelligence TO mycroft_app;
GRANT SELECT, INSERT, UPDATE ON regulatory_feeds TO mycroft_app;
GRANT USAGE, SELECT ON SEQUENCE regulatory_feeds_id_seq TO mycroft_app;
```

### SSL Connection

Configure PostgreSQL to require SSL connections:
```
# In postgresql.conf
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'

# In pg_hba.conf
hostssl all all 0.0.0.0/0 md5
```

---

**Database Version**: PostgreSQL 12+  
**Schema Version**: 1.0.0  
**Last Updated**: 2025