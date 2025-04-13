from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ConversationResponse(BaseModel):
    id: str = Field(..., description="Unique ID of the conversation") 
    user1_id: int = Field(..., description="ID of the first user in conversation")
    user2_id: int = Field(..., description="ID of the second user in conversation")
    last_message_at: Optional[datetime] = Field(None, description="Timestamp of the last message")
    last_message_content: Optional[str] = Field(None, description="Content of the last message")

class PaginatedConversationResponse(BaseModel):
    total: int = Field(..., description="Total number of conversations")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Number of items per page")
    data: List[ConversationResponse] = Field(..., description="List of conversations")