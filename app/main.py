import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import asyncio

from app.api.routes import message_router, conversation_router
from app.controllers.message_controller import MessageController
from app.controllers.conversation_controller import ConversationController
from app.db.cassandra_client import cassandra_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FB Messenger API",
    description="Backend API for FB Messenger implementation using Cassandra",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[""],  # In production, this should be restricted
    allow_credentials=True,
    allow_methods=[""],
    allow_headers=["*"],
)

# Dependency injection
def get_message_controller():
    """Dependency for message controller."""
    return MessageController()

def get_conversation_controller():
    """Dependency for conversation controller."""
    return ConversationController()

# Update the routes with the dependencies
app.dependency_overrides[MessageController] = get_message_controller
app.dependency_overrides[ConversationController] = get_conversation_controller

# Include routers
app.include_router(message_router)
app.include_router(conversation_router)

@app.get("/")
async def root():
    return {"message": "FB Messenger API is running with Cassandra backend"}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Initializing application...")
    max_retries = 5
    retry_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            # Ensure Cassandra connection is established
            cassandra_client.get_session()
            logger.info("Cassandra connection established")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Failed to connect to Cassandra (attempt {attempt+1}): {str(e)}")
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to Cassandra after {max_retries} attempts: {str(e)}")
                sys.exit(1)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down application...")
    cassandra_client.close()

if __name__ == "main":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 

