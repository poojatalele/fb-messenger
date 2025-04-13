# Cassandra Schema Design for FB Messenger MVP

## Overview
This document outlines the schema design for a simplified Facebook Messenger backend implementation using Apache Cassandra. The schema is optimized for the specific query patterns required by a real-time messaging application.

## Requirements Analysis
The messenger application needs to support the following core operations:
1. Sending messages between users
2. Retrieving conversations for a user ordered by recent activity
3. Fetching all messages in a conversation (with pagination)
4. Fetching messages before a specific timestamp (for pagination)

## Schema Design Principles
When designing for Cassandra, we follow these key principles:
1. **Query-first design**: Tables are modeled based on query patterns, not entity relationships
2. **Denormalization**: Data is duplicated across tables to optimize read performance
3. **Partition key selection**: Choosing partition keys that distribute data evenly
4. **Clustering columns**: Ordering data within partitions for efficient retrieval
5. **Avoid scans**: Design tables to avoid full table scans or filtering

## Table Schemas

### 1. Messages by Conversation
This table stores all messages within conversations and allows efficient retrieval of messages ordered by timestamp.

```sql
CREATE TABLE messages_by_conversation (
    conversation_id bigint,
    created_at timestamp,
    message_id bigint,
    sender_id int,
    receiver_id int,
    content text,
    PRIMARY KEY (conversation_id, created_at, message_id)
) WITH CLUSTERING ORDER BY (created_at DESC, message_id DESC);
```

**Query patterns supported:**
- Fetch messages in a conversation with pagination
- Fetch messages before a specific timestamp

**Design rationale:**
- `conversation_id` as the partition key groups all messages from a conversation together
- `created_at` as the first clustering column enables time-based ordering and filtering
- `message_id` ensures uniqueness in case multiple messages have the same timestamp
- Descending order optimizes for retrieving the most recent messages first

### 2. Conversations by User
This table allows quick retrieval of a user's conversations sorted by most recent activity.

```sql
CREATE TABLE conversations_by_user (
    user_id int,
    last_message_at timestamp,
    conversation_id bigint,
    other_user_id int,
    last_message_content text,
    PRIMARY KEY (user_id, last_message_at, conversation_id)
) WITH CLUSTERING ORDER BY (last_message_at DESC, conversation_id DESC);
```

**Query patterns supported:**
- Fetch conversations for a user ordered by most recent activity

**Design rationale:**
- `user_id` as the partition key groups all conversations for a user together
- `last_message_at` as the first clustering column enables time-based ordering
- Descending order optimizes for retrieving the most recent conversations first
- Includes preview data (`last_message_content`) to avoid additional queries

### 3. Conversation Metadata
This table stores metadata about each conversation.

```sql
CREATE TABLE conversation_metadata (
    conversation_id bigint,
    user1_id int,
    user2_id int,
    created_at timestamp,
    last_message_at timestamp,
    last_message_content text,
    PRIMARY KEY (conversation_id)
);
```

**Query patterns supported:**
- Get detailed information about a specific conversation

**Design rationale:**
- Simple primary key on `conversation_id` for direct lookups
- Stores participants and latest message information

### 4. User Conversations Lookup
This table enables finding an existing conversation between two users.

```sql
CREATE TABLE user_conversations_lookup (
    user1_id int,
    user2_id int,
    conversation_id bigint,
    PRIMARY KEY ((user1_id, user2_id))
);
```

**Query patterns supported:**
- Find an existing conversation between two specific users

**Design rationale:**
- Composite partition key of both user IDs (sorted to ensure consistent lookup)
- Enables efficient lookups to avoid creating duplicate conversations

## Data Flow and Interaction

### Sending a Message:
1. Check if a conversation exists between the two users using `user_conversations_lookup`
2. If not, create a new conversation and record in `conversation_metadata`
3. Insert the message into `messages_by_conversation`
4. Update `conversations_by_user` for both participants 
5. Update `conversation_metadata` with the new last message information

### Retrieving User Conversations:
1. Query `conversations_by_user` with the user's ID to get all conversations
2. For each conversation, retrieve full metadata from `conversation_metadata` if needed

### Retrieving Conversation Messages:
1. Query `messages_by_conversation` with the conversation ID and pagination parameters
2. For retrieving messages before a timestamp, add a condition on the `created_at` column

## Performance Considerations

### Read vs. Write Balance
The schema design prioritizes read performance over write efficiency, which aligns with messaging applications where users read messages more frequently than they write them. This is implemented through:

- Denormalization of data across multiple tables
- Duplicate storage of metadata like last message content
- Pre-sorted data using clustering columns

### Scalability
The schema is designed for horizontal scalability:

- Partition keys distribute data across the cluster
- Avoids secondary indexes and complex query patterns
- No joins or multi-partition queries for core operations

### Trade-offs
- Increased storage requirements due to data duplication
- Additional write operations needed to maintain consistency across tables
- Simplified model assumes direct message conversations only (not group chats)

## Future Improvements
- Add TTL (Time To Live) settings for message archiving
- Implement counter tables for unread message counts
- Add support for message status (delivered, read)
- Extend schema to support group conversations