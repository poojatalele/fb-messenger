"""
Models for interacting with Cassandra tables.
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.db.cassandra_client import cassandra_client

class MessageModel:
    """
    Message model for interacting with the messages table.
    """

    @staticmethod
    async def create_message(sender_id: int, receiver_id: int, content: str) -> Dict[str, Any]:
        """
        Create a new message.

        Args:
            sender_id: ID of the sender
            receiver_id: ID of the receiver
            content: Message content

        Returns:
            The created message data
        """
        # First, get or create conversation
        conversation_data = await ConversationModel.create_or_get_conversation(sender_id, receiver_id)
        conversation_id = conversation_data['conversation_id']

        # Generate a message ID (using a timestamp-based approach for simplicity)
        message_id = int(datetime.now().timestamp() * 1000)
        created_at = datetime.now()

        # Insert the message into messages_by_conversation with named parameters
        cassandra_client.execute(
            """
            INSERT INTO messages_by_conversation (
                conversation_id, created_at, message_id, sender_id, receiver_id, content
            ) VALUES (%(conversation_id)s, %(created_at)s, %(message_id)s, %(sender_id)s, %(receiver_id)s, %(content)s)
            """,
            {
                'conversation_id': conversation_id,
                'created_at': created_at,
                'message_id': message_id,
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'content': content
            }
        )

        # Update conversation metadata
        cassandra_client.execute(
            """
            UPDATE conversation_metadata 
            SET last_message_at = %(last_message_at)s, last_message_content = %(last_message_content)s
            WHERE conversation_id = %(conversation_id)s
            """,
            {
                'last_message_at': created_at,
                'last_message_content': content,
                'conversation_id': conversation_id
            }
        )

        # Update conversations_by_user for both users
        for user_id, other_id in [(sender_id, receiver_id), (receiver_id, sender_id)]:
            cassandra_client.execute(
                """
                INSERT INTO conversations_by_user (
                    user_id, last_message_at, conversation_id, other_user_id, last_message_content
                ) VALUES (%(user_id)s, %(last_message_at)s, %(conversation_id)s, %(other_user_id)s, %(last_message_content)s)
                """,
                {
                    'user_id': user_id,
                    'last_message_at': created_at,
                    'conversation_id': conversation_id,
                    'other_user_id': other_id,
                    'last_message_content': content
                }
            )

        # Return the created message data
        return {
            'id': message_id,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'content': content,
            'created_at': created_at,
            'conversation_id': conversation_id
        }

    @staticmethod
    async def get_conversation_messages(conversation_id: int, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """
        Get messages for a conversation with pagination.

        Args:
            conversation_id: ID of the conversation
            page: Page number
            limit: Number of messages per page

        Returns:
            Dictionary containing total, page, limit, and messages data
        """
        # Get the total count (Note: This is expensive in Cassandra, in production you'd handle this differently)
        count_result = cassandra_client.execute(
            "SELECT COUNT(*) as count FROM messages_by_conversation WHERE conversation_id = %(conversation_id)s",
            {'conversation_id': conversation_id}
        )
        total = count_result[0]['count'] if count_result else 0

        # Calculate the offset
        offset = (page - 1) * limit

        # Fetch messages with pagination
        # Note: Cassandra doesn't support OFFSET directly, so we'd need to use token-based pagination
        # For simplicity, we'll just limit the number of results, but this isn't efficient for deep pagination
        result = cassandra_client.execute(
            """
            SELECT conversation_id, created_at, message_id, sender_id, receiver_id, content
            FROM messages_by_conversation
            WHERE conversation_id = %(conversation_id)s
            LIMIT %(limit)s
            """,
            {
                'conversation_id': conversation_id,
                'limit': limit + offset
            }
        )

        # Apply the offset manually
        messages = result[offset:offset+limit] if len(result) > offset else []

        return {
            'total': total,
            'page': page,
            'limit': limit,
            'data': [
                {
                    'id': message['message_id'],
                    'sender_id': message['sender_id'],
                    'receiver_id': message['receiver_id'],
                    'content': message['content'],
                    'created_at': message['created_at'],
                    'conversation_id': message['conversation_id']
                }
                for message in messages
            ]
        }

    @staticmethod
    async def get_messages_before_timestamp(
        conversation_id: int,
        before_timestamp: datetime,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get messages before a timestamp with pagination.

        Args:
            conversation_id: ID of the conversation
            before_timestamp: Get messages before this timestamp
            page: Page number
            limit: Number of messages per page

        Returns:
            Dictionary containing total, page, limit, and messages data
        """
        # Count total messages before timestamp
        count_result = cassandra_client.execute(
            """
            SELECT COUNT(*) as count 
            FROM messages_by_conversation 
            WHERE conversation_id = %(conversation_id)s AND created_at < %(created_at)s
            """,
            {
                'conversation_id': conversation_id,
                'created_at': before_timestamp
            }
        )
        total = count_result[0]['count'] if count_result else 0

        # Calculate the offset
        offset = (page - 1) * limit

        # Fetch messages before timestamp with pagination
        result = cassandra_client.execute(
            """
            SELECT conversation_id, created_at, message_id, sender_id, receiver_id, content
            FROM messages_by_conversation
            WHERE conversation_id = %(conversation_id)s AND created_at < %(created_at)s
            LIMIT %(limit)s
            """,
            {
                'conversation_id': conversation_id,
                'created_at': before_timestamp,
                'limit': limit + offset
            }
        )

        # Apply the offset manually
        messages = result[offset:offset+limit] if len(result) > offset else []

        return {
            'total': total,
            'page': page,
            'limit': limit,
            'data': [
                {
                    'id': message['message_id'],
                    'sender_id': message['sender_id'],
                    'receiver_id': message['receiver_id'],
                    'content': message['content'],
                    'created_at': message['created_at'],
                    'conversation_id': message['conversation_id']
                }
                for message in messages
            ]
        }


class ConversationModel:
    """
    Conversation model for interacting with the conversations-related tables.
    """

    @staticmethod
    async def get_user_conversations(user_id: int, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """
        Get conversations for a user with pagination.

        Args:
            user_id: ID of the user
            page: Page number
            limit: Number of conversations per page

        Returns:
            Dictionary containing total, page, limit, and conversations data
        """
        # Count total conversations
        count_result = cassandra_client.execute(
            "SELECT COUNT(*) as count FROM conversations_by_user WHERE user_id = %(user_id)s",
            {'user_id': user_id}
        )
        total = count_result[0]['count'] if count_result else 0

        # Calculate the offset
        offset = (page - 1) * limit

        # Fetch conversations with pagination
        result = cassandra_client.execute(
            """
            SELECT user_id, last_message_at, conversation_id, other_user_id, last_message_content
            FROM conversations_by_user
            WHERE user_id = %(user_id)s
            LIMIT %(limit)s
            """,
            {
                'user_id': user_id,
                'limit': limit + offset
            }
        )

        # Apply the offset manually
        conversations = result[offset:offset+limit] if len(result) > offset else []

        # For each conversation, get the full metadata
        conversation_data = []
        for conv in conversations:
            metadata = cassandra_client.execute(
                "SELECT * FROM conversation_metadata WHERE conversation_id = %(conversation_id)s",
                {'conversation_id': conv['conversation_id']}
            )

            if metadata:
                meta = metadata[0]
                conversation_data.append({
                    'id': conv['conversation_id'],
                    'user1_id': meta['user1_id'],
                    'user2_id': meta['user2_id'],
                    'last_message_at': conv['last_message_at'],
                    'last_message_content': conv['last_message_content']
                })

        return {
            'total': total,
            'page': page,
            'limit': limit,
            'data': conversation_data
        }

    @staticmethod
    async def get_conversation(conversation_id: int) -> Dict[str, Any]:
        """
        Get a conversation by ID.

        Args:
            conversation_id: ID of the conversation

        Returns:
            Conversation data
        """
        result = cassandra_client.execute(
            "SELECT * FROM conversation_metadata WHERE conversation_id = %(conversation_id)s",
            {'conversation_id': conversation_id}
        )

        if not result:
            return None

        conversation = result[0]
        return {
            'id': conversation['conversation_id'],
            'user1_id': conversation['user1_id'],
            'user2_id': conversation['user2_id'],
            'last_message_at': conversation['last_message_at'],
            'last_message_content': conversation['last_message_content']
        }

    @staticmethod
    async def create_or_get_conversation(user1_id: int, user2_id: int) -> Dict[str, Any]:
        """
        Get an existing conversation between two users or create a new one.

        Args:
            user1_id: ID of the first user
            user2_id: ID of the second user

        Returns:
            Conversation data
        """
        # Sort the user IDs to ensure consistent lookups
        sorted_user_ids = sorted([user1_id, user2_id])
        user1_id, user2_id = sorted_user_ids[0], sorted_user_ids[1]

        # Check if conversation exists
        result = cassandra_client.execute(
            "SELECT * FROM user_conversations_lookup WHERE user1_id = %(user1_id)s AND user2_id = %(user2_id)s",
            {'user1_id': user1_id, 'user2_id': user2_id}
        )

        if result:
            # Conversation exists, get its details
            conversation_id = result[0]['conversation_id']
            conversation = await ConversationModel.get_conversation(conversation_id)
            return conversation

        # Conversation doesn't exist, create a new one
        # Generate a conversation ID (using a timestamp-based approach for simplicity)
        conversation_id = int(datetime.now().timestamp() * 1000)
        created_at = datetime.now()

        # Insert into conversation_metadata - FIXED VERSION WITH NAMED PARAMETERS
        cassandra_client.execute(
            """
            INSERT INTO conversation_metadata (
                conversation_id, user1_id, user2_id, created_at, last_message_at, last_message_content
            ) VALUES (%(conversation_id)s, %(user1_id)s, %(user2_id)s, %(created_at)s, %(last_message_at)s, %(last_message_content)s)
            """,
            {
                'conversation_id': conversation_id,
                'user1_id': user1_id,
                'user2_id': user2_id,
                'created_at': created_at,
                'last_message_at': created_at,
                'last_message_content': None
            }
        )

        # Insert into user_conversations_lookup - FIXED VERSION WITH NAMED PARAMETERS
        cassandra_client.execute(
            """
            INSERT INTO user_conversations_lookup (
                user1_id, user2_id, conversation_id
            ) VALUES (%(user1_id)s, %(user2_id)s, %(conversation_id)s)
            """,
            {
                'user1_id': user1_id,
                'user2_id': user2_id,
                'conversation_id': conversation_id
            }
        )

        return {
            'conversation_id': conversation_id,
            'user1_id': user1_id,
            'user2_id': user2_id,
            'last_message_at': created_at,
            'last_message_content': None
        }