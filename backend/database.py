import motor.motor_asyncio
import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import asyncio
from typing import Optional

class DatabaseManager:
    def __init__(self):
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/observer_ai')
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.db = None
        self.connected = False
        
    async def connect(self):
        """Initialize MongoDB connection with connection pooling"""
        try:
            # Configure connection with optimization for high load
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                self.mongo_url,
                maxPoolSize=100,  # Maximum connections in pool
                minPoolSize=10,   # Minimum connections in pool
                maxIdleTimeMS=30000,  # Close connections after 30s idle
                waitQueueTimeoutMS=5000,  # Wait 5s for connection from pool
                serverSelectionTimeoutMS=3000,  # 3s timeout for server selection
                socketTimeoutMS=20000,  # 20s socket timeout
                connectTimeoutMS=10000,  # 10s connection timeout
                retryWrites=True,
                retryReads=True,
                readPreference='primaryPreferred',
                w='majority',  # Write concern for data safety
                journal=True   # Ensure writes are journaled
            )
            
            # Get database name from URL or use default
            db_name = 'observer_ai'
            if '/' in self.mongo_url:
                db_name = self.mongo_url.split('/')[-1].split('?')[0]
            
            self.db = self.client[db_name]
            
            # Test connection
            await self.client.admin.command('ping')
            self.connected = True
            
            # Create indexes for performance
            await self.create_indexes()
            
            print("✅ MongoDB connected successfully with connection pooling")
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            self.connected = False
            raise
    
    async def create_indexes(self):
        """Create database indexes for optimal performance"""
        if not self.connected:
            return
        
        try:
            # User indexes
            await self.db.users.create_index("email", unique=True)
            await self.db.users.create_index("id", unique=True)
            await self.db.users.create_index("created_at")
            await self.db.users.create_index("last_login")
            
            # Agent indexes  
            await self.db.agents.create_index("user_id")
            await self.db.agents.create_index("id", unique=True)
            await self.db.agents.create_index([("user_id", 1), ("created_at", -1)])
            await self.db.agents.create_index("archetype")
            
            # Conversation indexes
            await self.db.conversations.create_index("user_id")
            await self.db.conversations.create_index("id", unique=True)
            await self.db.conversations.create_index([("user_id", 1), ("created_at", -1)])
            await self.db.conversations.create_index("round_number")
            
            # Document indexes
            await self.db.documents.create_index("metadata.user_id")
            await self.db.documents.create_index("id", unique=True)
            await self.db.documents.create_index([("metadata.user_id", 1), ("metadata.created_at", -1)])
            await self.db.documents.create_index("metadata.category")
            
            # Saved agent indexes
            await self.db.saved_agents.create_index("user_id")
            await self.db.saved_agents.create_index("id", unique=True)
            await self.db.saved_agents.create_index([("user_id", 1), ("created_at", -1)])
            
            # Simulation state indexes
            await self.db.simulation_state.create_index("user_id")
            await self.db.simulation_state.create_index("created_at")
            
            print("✅ Database indexes created successfully")
            
        except Exception as e:
            print(f"❌ Error creating indexes: {e}")
    
    async def get_connection_stats(self):
        """Get current connection pool statistics"""
        if not self.connected:
            return None
        
        try:
            server_status = await self.client.admin.command("serverStatus")
            return {
                "connections": server_status.get("connections", {}),
                "active_clients": server_status.get("globalLock", {}).get("activeClients", {}),
                "pool_size": "100 max, 10 min"  # Our configured pool size
            }
        except Exception as e:
            print(f"Error getting connection stats: {e}")
            return None
    
    async def health_check(self):
        """Check database health"""
        try:
            await self.client.admin.command('ping')
            return True
        except Exception:
            return False

# Global database instance
db_manager = DatabaseManager()

# Convenience accessor for the database
def get_db():
    return db_manager.db