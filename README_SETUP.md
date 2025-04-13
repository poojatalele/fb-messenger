# FB Messenger MVP - Cassandra Implementation

## Project Overview
This project implements a simplified backend for a Facebook Messenger-like application using Apache Cassandra as the distributed database. The implementation focuses on core messaging functionality with efficient data modeling for high-performance and scalable operations.

## Features
- Send messages between users
- Retrieve user conversations sorted by recent activity
- Fetch all messages in a conversation with pagination
- Fetch messages before a specific timestamp (for scrollback pagination)

## Tech Stack
- **Python 3.11+**: Core programming language
- **FastAPI**: Web framework for building APIs
- **Apache Cassandra**: Distributed NoSQL database
- **Docker & Docker Compose**: Containerization and orchestration
- **Cassandra-driver**: Python client for Cassandra

## Project Structure
```
fb_messenger/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── conversation_router.py
│   │   │   └── message_router.py
│   ├── controllers/
│   │   ├── conversation_controller.py
│   │   └── message_controller.py
│   ├── db/
│   │   └── cassandra_client.py
│   ├── models/
│   │   └── cassandra_models.py
│   ├── schemas/
│   │   ├── conversation.py
│   │   └── message.py
│   └── main.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── setup_db.py
└── SCHEMA.md
```

## Cassandra Schema Design
The application uses a query-first design approach with four main tables:

1. **messages_by_conversation**: Stores all messages within conversations for efficient retrieval
2. **conversations_by_user**: Enables quick access to a user's conversations sorted by activity
3. **conversation_metadata**: Contains metadata about each conversation
4. **user_conversations_lookup**: Facilitates finding existing conversations between users

For detailed schema information, please see [SCHEMA.md](SCHEMA.md).

## API Endpoints

### Messages
- `POST /api/messages/`: Send a message
  ```json
  {
    "sender_id": 123,
    "receiver_id": 456,
    "content": "Hello, how are you?"
  }
  ```

- `GET /api/messages/conversation/{conversation_id}?page=1&limit=20`: 
  Get messages in a conversation with pagination

- `GET /api/messages/conversation/{conversation_id}/before?before_timestamp=2025-04-13T12:00:00&page=1&limit=20`: 
  Get messages before a specific timestamp

### Conversations
- `GET /api/conversations/user/{user_id}?page=1&limit=20`: 
  Get all conversations for a user with pagination

- `GET /api/conversations/{conversation_id}`: 
  Get details about a specific conversation

## Setup Instructions

### Prerequisites
- Docker and Docker Compose
- Git

### Running the Application
1. Clone the repository:
   ```bash
   git clone https://github.com/poojatalele/fb_messenger.git
   cd fb_messenger
   ```

2. Start the services with Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. Initialize the database (this runs automatically as part of container startup):
   ```bash
   docker-compose exec app python setup_db.py
   ```

4. The API will be available at `http://localhost:8000`

5. Access the Swagger documentation at `http://localhost:8000/docs`

### Environment Variables
The application can be configured using the following environment variables:

- `CASSANDRA_HOST`: Cassandra host (default: "localhost")
- `CASSANDRA_PORT`: Cassandra port (default: 9042)
- `CASSANDRA_KEYSPACE`: Keyspace name (default: "messenger")

## Implementation Details

### Data Flow for Sending a Message
1. User sends a message via the API
2. System checks if a conversation exists between the users
3. If no conversation exists, a new one is created
4. Message is saved in `messages_by_conversation`
5. Conversation metadata is updated in both `conversations_by_user` and `conversation_metadata`

### Pagination
The application implements efficient pagination using:
- Standard page-based pagination for conversations
- Timestamp-based pagination for message history (to support infinite scrollback)

### Performance Considerations
- Optimized read patterns for real-time messaging
- Denormalized data model to reduce query complexity
- Efficient partition keys to distribute data across the cluster

## Testing
You can test the API using the Swagger documentation or with tools like curl or Postman.

Example curl command to send a message:
```bash
curl -X POST "http://localhost:8000/api/messages/" \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": 1,
    "receiver_id": 2,
    "content": "Hello, this is a test message!"
  }'
```

## Future Improvements
- Add authentication and authorization
- Implement WebSockets for real-time message delivery
- Add read receipts functionality
- Support for group conversations
- Message reactions and attachments
- Message search functionality

## License
This project is licensed under the MIT License - see the LICENSE file for details.