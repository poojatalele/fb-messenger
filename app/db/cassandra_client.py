import os
import uuid
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from cassandra.cluster import Cluster, Session, NoHostAvailable
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import SimpleStatement, dict_factory

logger = logging.getLogger(__name__)

class CassandraClient:
    """Singleton Cassandra client for the application."""
   
    _instance = None
   
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CassandraClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
   
    def __init__(self):
        """Initialize the Cassandra connection."""
        if getattr(self, '_initialized', False):
            return
       
        self.host = os.getenv("CASSANDRA_HOST", "localhost")
        self.port = int(os.getenv("CASSANDRA_PORT", "9042"))
        self.keyspace = os.getenv("CASSANDRA_KEYSPACE", "messenger")
       
        self.cluster = None
        self.session = None
        
        # Don't connect immediately on initialization
        # We'll connect when needed
        
        self._initialized = True
   
    def connect(self) -> None:
        """Connect to the Cassandra cluster with retry logic."""
        max_retries = 10
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to Cassandra at {self.host}:{self.port} (attempt {attempt+1}/{max_retries})...")
                self.cluster = Cluster([self.host])
                
                # First connect without keyspace to verify the connection
                temp_session = self.cluster.connect()
                
                # Check if keyspace exists, create if it doesn't
                self._ensure_keyspace_exists(temp_session)
                
                # Now connect with the keyspace
                self.session = self.cluster.connect(self.keyspace)
                self.session.row_factory = dict_factory
                
                logger.info(f"Successfully connected to Cassandra at {self.host}:{self.port}, keyspace: {self.keyspace}")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Failed to connect to Cassandra (attempt {attempt+1}): {str(e)}")
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    # Increase retry delay for next attempt
                    retry_delay = min(retry_delay * 1.5, 30)  # Cap at 30 seconds
                else:
                    logger.error(f"Failed to connect to Cassandra after {max_retries} attempts: {str(e)}")
                    raise
    
    def _ensure_keyspace_exists(self, session):
        """Ensure the keyspace exists, create it if it doesn't."""
        try:
            # Check if keyspace exists
            rows = session.execute(f"SELECT keyspace_name FROM system_schema.keyspaces WHERE keyspace_name = '{self.keyspace}'")
            if not rows:
                logger.info(f"Creating keyspace {self.keyspace}...")
                session.execute(f"""
                    CREATE KEYSPACE IF NOT EXISTS {self.keyspace}
                    WITH REPLICATION = {{'class': 'SimpleStrategy', 'replication_factor': 3}}
                """)
                logger.info(f"Keyspace {self.keyspace} created successfully")
        except Exception as e:
            logger.error(f"Error ensuring keyspace exists: {str(e)}")
            raise
   
    def close(self) -> None:
        """Close the Cassandra connection."""
        if self.cluster:
            self.cluster.shutdown()
            logger.info("Cassandra connection closed")
   
    def execute(self, query: str, params: dict = None) -> List[Dict[str, Any]]:
        """
        Execute a CQL query.
       
        Args:
            query: The CQL query string
            params: The parameters for the query
           
        Returns:
            List of rows as dictionaries
        """
        if not self.session:
            self.connect()
       
        try:
            statement = SimpleStatement(query)
            result = self.session.execute(statement, params or {})
            return list(result)
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
   
    def execute_async(self, query: str, params: dict = None):
        """
        Execute a CQL query asynchronously.
       
        Args:
            query: The CQL query string
            params: The parameters for the query
           
        Returns:
            Async result object
        """
        if not self.session:
            self.connect()
       
        try:
            statement = SimpleStatement(query)
            return self.session.execute_async(statement, params or {})
        except Exception as e:
            logger.error(f"Async query execution failed: {str(e)}")
            raise
   
    def get_session(self) -> Session:
        """Get the Cassandra session."""
        if not self.session:
            self.connect()
        return self.session

# Create a global instance
cassandra_client = CassandraClient()