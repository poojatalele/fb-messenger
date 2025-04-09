from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ConversationResponse(BaseModel):
    id: str = Field(..., description="Unique ID of the conversation") 
    last_activity: datetime = Field(..., description="Timestamp of the last activity")
    other_user_id: int = Field(..., description="ID of the other user in conversation")
    last_message: str = Field(..., description="Content of the last message")

class PaginatedConversationResponse(BaseModel):
    total: int = Field(..., description="Total number of conversations")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page")
    items: List[ConversationResponse] = Field(..., description="List of conversations") 
    pages: int = Field(..., description="Total number of pages")