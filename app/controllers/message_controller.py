from typing import Optional
from datetime import datetime
from fastapi import HTTPException, status

from app.schemas.message import MessageCreate, MessageResponse, PaginatedMessageResponse
from app.models.cassandra_models import MessageModel


class MessageController:
    """
    Controller for handling message operations
    """

    async def send_message(self, message_data: MessageCreate) -> MessageResponse:
        """
        Send a message from one user to another

        Args:
            message_data: The message data including content, sender_id, and receiver_id

        Returns:
            The created message with metadata

        Raises:
            HTTPException: If message sending fails
        """
        try:
            from app.models.cassandra_models import MessageModel

            result = await MessageModel.create_message(
                sender_id=message_data.sender_id,
                receiver_id=message_data.receiver_id,
                content=message_data.content
            )

            return MessageResponse(
                id=result['id'],
                sender_id=result['sender_id'],
                receiver_id=result['receiver_id'],
                content=result['content'],
                created_at=result['created_at'],
                conversation_id=result['conversation_id']
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send message: {str(e)}"
            )

    async def get_conversation_messages(
            self,
            conversation_id: int,
            page: int = 1,
            limit: int = 20
    ) -> PaginatedMessageResponse:
        """
        Get all messages in a conversation with pagination

        Args:
            conversation_id: ID of the conversation
            page: Page number
            limit: Number of messages per page

        Returns:
            Paginated list of messages

        Raises:
            HTTPException: If conversation not found or access denied
        """
        try:
            from app.models.cassandra_models import MessageModel

            result = await MessageModel.get_conversation_messages(conversation_id, page, limit)

            return PaginatedMessageResponse(
                total=result['total'],
                page=result['page'],
                limit=result['limit'],
                data=[
                    MessageResponse(
                        id=msg['id'],
                        sender_id=msg['sender_id'],
                        receiver_id=msg['receiver_id'],
                        content=msg['content'],
                        created_at=msg['created_at'],
                        conversation_id=msg['conversation_id']
                    )
                    for msg in result['data']
                ]
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get conversation messages: {str(e)}"
            )

    async def get_messages_before_timestamp(
            self,
            conversation_id: int,
            before_timestamp: datetime,
            page: int = 1,
            limit: int = 20
    ) -> PaginatedMessageResponse:
        """
        Get messages in a conversation before a specific timestamp with pagination

        Args:
            conversation_id: ID of the conversation
            before_timestamp: Get messages before this timestamp
            page: Page number
            limit: Number of messages per page

        Returns:
            Paginated list of messages

        Raises:
            HTTPException: If conversation not found or access denied
        """
        try:
            from app.models.cassandra_models import MessageModel

            result = await MessageModel.get_messages_before_timestamp(
                conversation_id, before_timestamp, page, limit
            )

            return PaginatedMessageResponse(
                total=result['total'],
                page=result['page'],
                limit=result['limit'],
                data=[
                    MessageResponse(
                        id=msg['id'],
                        sender_id=msg['sender_id'],
                        receiver_id=msg['receiver_id'],
                        content=msg['content'],
                        created_at=msg['created_at'],
                        conversation_id=msg['conversation_id']
                    )
                    for msg in result['data']
                ]
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get messages before timestamp: {str(e)}"
            )