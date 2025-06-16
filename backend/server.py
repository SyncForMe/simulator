from fastapi import FastAPI, HTTPException, Depends, status, APIRouter, UploadFile, File, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
import bcrypt
import jwt
from jwt.exceptions import InvalidTokenError as JWTError
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime, timedelta, date
import uuid
import logging
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage
from google.cloud import texttospeech
import base64
import fal_client
from jose import JWTError, jwt
from google.auth.transport import requests
from google.oauth2 import id_token
import httpx
import tempfile
import openai
from pydub import AudioSegment
import io
import asyncio
import re
import urllib.parse

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Environment variables
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')  
JWT_SECRET = os.environ.get('JWT_SECRET')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
ADMIN_EMAIL = "dino@cytonic.com"  # Admin email for special privileges

# Security
security = HTTPBearer()

# Password hashing utilities
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

# Base Models
class AgentPersonality(BaseModel):
    extroversion: int = Field(ge=1, le=10)
    optimism: int = Field(ge=1, le=10) 
    curiosity: int = Field(ge=1, le=10)
    cooperativeness: int = Field(ge=1, le=10)
    energy: int = Field(ge=1, le=10)

# User Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    picture: str = ""
    google_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class GoogleAuthRequest(BaseModel):
    credential: str  # Google JWT token

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: str
    created_at: datetime
    last_login: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Email/Password Authentication Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=1)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Enhanced User model for email/password auth
class UserWithPassword(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    picture: str = ""
    google_id: str = ""  # Optional for email/password users
    password_hash: str = ""  # For email/password users
    auth_type: str = "google"  # "google" or "email"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

# Saved Agent Models
class SavedAgent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    archetype: str
    personality: AgentPersonality
    goal: str
    expertise: str = ""
    background: str = ""
    avatar_url: str = ""
    avatar_prompt: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_template: bool = False  # User can mark agents as templates
    usage_count: int = 0  # How many times used in simulations

class SavedAgentCreate(BaseModel):
    name: str
    archetype: str
    personality: Optional[AgentPersonality] = None
    goal: str
    expertise: str = ""
    background: str = ""
    avatar_url: str = ""
    avatar_prompt: str = ""
    is_template: bool = False

# Conversation History Models
class ConversationHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    simulation_id: str = ""  # Links to simulation session
    participants: List[str] = []  # Agent names
    messages: List[dict] = []  # Conversation messages
    language: str = "en"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    title: str = ""  # Auto-generated or user-defined title
    tags: List[str] = []  # User can tag conversations

# File Center Models for Action-Oriented Agent Behavior
class DocumentMetadata(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    filename: str
    authors: List[str] = []  # Agent names who contributed
    category: str  # Protocol/Training/Research/Equipment/Budget
    status: str = "Draft"  # Draft/Review/Approved/Implemented
    description: str
    keywords: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    simulation_id: str = ""  # Links to the simulation where it was created
    conversation_round: int = 0  # Which conversation round triggered creation
    scenario_name: str = ""  # Name of the scenario for organization
    user_id: str = ""  # User who owns this simulation

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: DocumentMetadata
    content: str  # The actual document content in markdown format
    created_by_agents: List[str] = []  # Agent IDs involved in creation
    conversation_context: str = ""  # What conversation led to this document
    action_trigger: str = ""  # The specific phrase that triggered creation

class DocumentCreate(BaseModel):
    title: str
    category: str
    description: str
    content: str
    keywords: List[str] = []
    authors: List[str] = []
    
class DocumentResponse(BaseModel):
    id: str
    metadata: DocumentMetadata
    content: str
    preview: str = ""  # First 200 characters for listings

class ActionTriggerResult(BaseModel):
    should_create_document: bool
    document_type: str = ""  # protocol/training/research
    document_title: str = ""
    trigger_phrase: str = ""
    reasoning: str = ""

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'ai_simulation')]

# Configure fal.ai
import fal_client
fal_client.api_key = os.environ.get('FAL_KEY')

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Agent Archetypes
AGENT_ARCHETYPES = {
    "scientist": {
        "name": "The Scientist",
        "description": "Logical, curious, methodical",
        "default_traits": {"extroversion": 4, "optimism": 6, "curiosity": 9, "cooperativeness": 7, "energy": 6}
    },
    "artist": {
        "name": "The Artist", 
        "description": "Creative, emotional, expressive",
        "default_traits": {"extroversion": 6, "optimism": 7, "curiosity": 8, "cooperativeness": 6, "energy": 7}
    },
    "leader": {
        "name": "The Leader",
        "description": "Confident, decisive, social", 
        "default_traits": {"extroversion": 9, "optimism": 8, "curiosity": 6, "cooperativeness": 8, "energy": 8}
    },
    "skeptic": {
        "name": "The Skeptic",
        "description": "Questioning, cautious, analytical",
        "default_traits": {"extroversion": 4, "optimism": 3, "curiosity": 7, "cooperativeness": 5, "energy": 5}
    },
    "optimist": {
        "name": "The Optimist", 
        "description": "Positive, encouraging, hopeful",
        "default_traits": {"extroversion": 8, "optimism": 10, "curiosity": 6, "cooperativeness": 9, "energy": 8}
    },
    "introvert": {
        "name": "The Introvert",
        "description": "Quiet, thoughtful, observant",
        "default_traits": {"extroversion": 2, "optimism": 5, "curiosity": 7, "cooperativeness": 6, "energy": 4}
    },
    "adventurer": {
        "name": "The Adventurer",
        "description": "Bold, spontaneous, energetic", 
        "default_traits": {"extroversion": 8, "optimism": 8, "curiosity": 9, "cooperativeness": 6, "energy": 9}
    },
    "mediator": {
        "name": "The Mediator",
        "description": "Peaceful, diplomatic, empathetic",
        "default_traits": {"extroversion": 6, "optimism": 7, "curiosity": 6, "cooperativeness": 10, "energy": 6}
    },
    "researcher": {
        "name": "The Researcher",
        "description": "Investigative, detail-oriented, systematic",
        "default_traits": {"extroversion": 3, "optimism": 6, "curiosity": 9, "cooperativeness": 7, "energy": 5}
    }
}

class ObserverMessage(BaseModel):
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ObserverInput(BaseModel):
    observer_message: str

@api_router.post("/observer/send-message")
async def send_observer_message(input_data: ObserverInput):
    """Send a message from the observer (user) to the AI agents"""
    observer_message = input_data.observer_message.strip()
    
    if not observer_message:
        raise HTTPException(status_code=400, detail="Observer message cannot be empty")
    
    # Get current agents
    agents = await db.agents.find().to_list(100)
    if len(agents) < 1:
        raise HTTPException(status_code=400, detail="No agents available to respond")
    
    agent_objects = [Agent(**agent) for agent in agents]
    
    # Get simulation state
    state = await db.simulation_state.find_one()
    if not state:
        raise HTTPException(status_code=404, detail="Simulation not started")
    
    scenario = state.get("scenario", "Research Station")
    
    # Store observer message
    observer_msg = ObserverMessage(message=observer_message)
    await db.observer_messages.insert_one(observer_msg.dict())
    
    # Generate responses from each agent to the observer
    messages = []
    for agent in agent_objects:
        if not await llm_manager.can_make_request():
            response = f"{agent.name} is listening but cannot respond right now (API limit reached)."
        else:
            # Create LLM chat instance for this agent responding to observer
            chat = LlmChat(
                api_key=llm_manager.api_key,
                session_id=f"observer_{agent.id}_{datetime.now().timestamp()}",
                system_message=f"""You are {agent.name}, {AGENT_ARCHETYPES[agent.archetype]['description']}.
                
Your personality traits:
- Extroversion: {agent.personality.extroversion}/10
- Optimism: {agent.personality.optimism}/10  
- Curiosity: {agent.personality.curiosity}/10
- Cooperativeness: {agent.personality.cooperativeness}/10
- Energy: {agent.personality.energy}/10

Your goal: {agent.goal}

You are in {scenario}. The Observer (project lead/supervisor) has just spoken to you and your team.
Respond professionally and authentically to your personality. Keep it brief (1-2 sentences).
Address the Observer respectfully but naturally according to your personality."""
            ).with_model("gemini", "gemini-2.0-flash")
            
            try:
                user_message = UserMessage(text=f"Observer says: '{observer_message}'\n\nRespond to the Observer professionally according to your personality.")
                response = await chat.send_message(user_message)
                await llm_manager.increment_usage()
            except Exception as e:
                logging.error(f"Error generating observer response for {agent.name}: {e}")
                response = f"{agent.name} nods thoughtfully in response."
        
        message = ConversationMessage(
            agent_id=agent.id,
            agent_name=agent.name,
            message=response,
            mood=agent.current_mood
        )
        messages.append(message)
    
    # Get current round number
    conversation_count = await db.conversations.count_documents({})
    
    # Create special observer conversation round
    conversation_round = ConversationRound(
        round_number=conversation_count + 1,
        time_period=f"Observer Input - {datetime.now().strftime('%H:%M')}",
        scenario=f"Observer: {observer_message}",
        messages=messages
    )
    
    await db.conversations.insert_one(conversation_round.dict())
    
    return {
        "message": "Observer message sent and responses received",
        "observer_message": observer_message,
        "agent_responses": conversation_round
    }

@api_router.get("/usage")
async def get_usage():
    """Get current API usage statistics"""
    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        usage = await db.api_usage.find_one({"date": today})
        if usage:
            # Convert MongoDB ObjectId to string
            if '_id' in usage:
                usage['_id'] = str(usage['_id'])
            
            # Map field names to expected names
            return {
                "date": usage.get("date", today),
                "requests": usage.get("requests_used", 0),
                "remaining": 1000 - usage.get("requests_used", 0)
            }
        else:
            # Return default values if no usage record found
            return {
                "date": today,
                "requests": 0,
                "remaining": 1000
            }
    except Exception as e:
        logging.error(f"Error getting API usage: {e}")
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return {
            "date": today,
            "requests": 0,
            "remaining": 1000
        }

@api_router.get("/observer/messages")
async def get_observer_messages():
    """Get all observer messages"""
    messages = await db.observer_messages.find().sort("timestamp", -1).to_list(100)
    return messages


class Agent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    archetype: str
    personality: AgentPersonality
    goal: str
    expertise: str = ""
    background: str = ""
    current_mood: str = "neutral"
    current_activity: str = "idle"
    memory_summary: str = ""  # Summary of important memories/developments
    avatar_url: str = ""  # URL to the agent's avatar image
    avatar_prompt: str = ""  # The prompt used to generate the avatar
    user_id: str = ""  # Associate agent with user for data isolation
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AgentCreate(BaseModel):
    name: str
    archetype: str
    personality: Optional[AgentPersonality] = None
    goal: str
    expertise: str = ""
    background: str = ""
    memory_summary: str = ""  # Memory and knowledge data
    avatar_prompt: str = ""  # Prompt for avatar generation
    avatar_url: str = ""  # Pre-generated avatar URL (from preview)

class AvatarGenerateRequest(BaseModel):
    prompt: str

class AvatarResponse(BaseModel):
    success: bool
    image_url: str = ""
    error: str = ""

class ConversationMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    agent_name: str
    message: str
    mood: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConversationRound(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    round_number: int
    time_period: str  # morning, afternoon, evening
    scenario: str
    scenario_name: str = ""  # Name/title of the scenario
    messages: List[ConversationMessage]
    user_id: str = ""  # Associate conversation with user for data isolation
    created_at: datetime = Field(default_factory=datetime.utcnow)
    language: str = "en"
    original_language: Optional[str] = None
    translated_at: Optional[datetime] = None
    force_translated: bool = False

class Relationship(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent1_id: str
    agent2_id: str
    score: int = 0  # -10 to +10
    status: str = "neutral"  # friends, tension, neutral
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SimulationState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    current_day: int = 1
    current_time_period: str = "morning"
    daily_api_requests: int = 0
    last_reset_date: str = Field(default_factory=lambda: str(date.today()))
    scenario: str = "The Research Station"
    is_active: bool = False
    time_limit_hours: Optional[int] = None  # Time limit in hours
    time_limit_display: Optional[str] = None  # Human readable time limit
    simulation_start_time: Optional[datetime] = None  # When simulation started
    time_remaining_hours: Optional[float] = None  # Calculated remaining time

class ApiUsageTracker(BaseModel):
    date: str
    requests_used: int
    max_requests: int = 1400  # Buffer under 1500 limit

class ScenarioRequest(BaseModel):
    scenario: str
    scenario_name: str = ""

class AutoModeRequest(BaseModel):
    auto_conversations: bool = False
    auto_time: bool = False
    conversation_interval: int = 10
    time_interval: int = 30

class FastForwardRequest(BaseModel):
    target_days: int = Field(ge=1, le=30)  # 1-30 days max
    conversations_per_period: int = Field(ge=1, le=5, default=2)  # 1-5 conversations per time period

class SimulationStartRequest(BaseModel):
    time_limit_hours: Optional[int] = None  # Time limit in hours, None for unlimited
    time_limit_display: Optional[str] = None  # Human readable time limit for agents

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    archetype: Optional[str] = None
    personality: Optional[AgentPersonality] = None
    goal: Optional[str] = None
    expertise: Optional[str] = None
    background: Optional[str] = None
    memory_summary: Optional[str] = None
    avatar_url: Optional[str] = None

# LLM Integration and Request Management
class LLMManager:
    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        self.max_daily_requests = 50000  # Paid tier - much higher limit
        
    async def get_usage_today(self):
        """Get current API usage for today"""
        today = str(date.today())
        usage = await db.api_usage.find_one({"date": today})
        if not usage:
            usage = {"date": today, "requests_used": 0}
            await db.api_usage.insert_one(usage)
        return usage["requests_used"]
    
    async def increment_usage(self):
        """Increment today's API usage count"""
        today = str(date.today())
        await db.api_usage.update_one(
            {"date": today},
            {"$inc": {"requests_used": 1}},
            upsert=True
        )
    
    async def fetch_url_content(self, url: str) -> str:
        """Fetch and summarize content from a URL for agent memory"""
        try:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=5)  # 5 second timeout
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        # Simple content extraction - remove HTML tags and limit length
                        import re
                        text_content = re.sub(r'<[^>]+>', ' ', content)
                        text_content = re.sub(r'\s+', ' ', text_content).strip()
                        
                        # Limit to first 1500 characters
                        if len(text_content) > 1500:
                            text_content = text_content[:1500] + "..."
                        
                        return text_content
                    else:
                        return f"Could not access {url} (status: {response.status})"
        except asyncio.TimeoutError:
            return f"Timeout accessing {url}"
        except Exception as e:
            logging.warning(f"Error fetching {url}: {e}")
            return f"Could not access {url}"

    async def process_memory_with_urls(self, memory_text: str) -> str:
        """Process memory text and fetch content from any URLs found"""
        if not memory_text:
            return memory_text
        
        # Find URLs in memory text
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, memory_text)
        
        if not urls:
            return memory_text
        
        enhanced_memory = memory_text
        
        for url in urls[:2]:  # Limit to 2 URLs to avoid timeout issues
            try:
                # Fetch content from URL
                url_content = await self.fetch_url_content(url)
                
                # Create a summary of the URL content using LLM only if we have substantial content
                if url_content and len(url_content) > 100 and "Could not access" not in url_content:
                    try:
                        if await self.can_make_request():
                            chat = LlmChat(
                                api_key=self.api_key,
                                session_id=f"url_summary_{hash(url)}",
                                system_message="Summarize web content into 2-3 key facts that would be relevant for an AI agent's memory. Focus on the most important information."
                            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(100)
                            
                            user_message = UserMessage(text=f"Summarize this web content concisely:\n\n{url_content}")
                            summary = await chat.send_message(user_message)
                            await self.increment_usage()
                            
                            # Replace the URL with enriched content
                            enhanced_memory = enhanced_memory.replace(
                                url, 
                                f"[Knowledge from {url}]: {summary}"
                            )
                        else:
                            enhanced_memory = enhanced_memory.replace(
                                url,
                                f"[Reference: {url}] (Content processing skipped - API limit)"
                            )
                    except Exception as e:
                        logging.warning(f"Error summarizing {url}: {e}")
                        enhanced_memory = enhanced_memory.replace(
                            url,
                            f"[Reference: {url}] (Content available but not processed)"
                        )
                else:
                    enhanced_memory = enhanced_memory.replace(
                        url,
                        f"[Reference: {url}] (Could not access content)"
                    )
            except Exception as e:
                logging.warning(f"Error processing URL {url}: {e}")
                enhanced_memory = enhanced_memory.replace(
                    url,
                    f"[Reference: {url}] (Processing error)"
                )
        
        return enhanced_memory
    
    async def can_make_request(self):
        """Check if we can make another API request today"""
        usage = await self.get_usage_today()
        
        # Check if we're within our daily request limit
        # No hardcoded limit since we're on paid tier now
        return usage < self.max_daily_requests

    async def generate_agent_response(self, agent: Agent, scenario: str, other_agents: List[Agent], context: str = "", conversation_history: List = None, language_instruction: str = "Respond in English.", existing_documents: List = None, simulation_state: dict = None):
        """Generate a single agent response with better context and progression"""
        other_agent_names = [a.name for a in other_agents if a.id != agent.id]
        others_text = f"Others present: {', '.join(other_agent_names)}" if other_agent_names else "You are alone"
        
        # Build time limit context
        time_pressure_context = ""
        if simulation_state and simulation_state.get('time_limit_hours'):
            # Calculate remaining time
            start_time = simulation_state.get('simulation_start_time')
            if start_time:
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                elif isinstance(start_time, dict):
                    start_time = datetime.fromisoformat(start_time.get('$date', str(datetime.utcnow())))
                
                elapsed_hours = (datetime.utcnow() - start_time).total_seconds() / 3600
                remaining_hours = simulation_state['time_limit_hours'] - elapsed_hours
                
                if remaining_hours > 0:
                    time_display = simulation_state.get('time_limit_display', f"{remaining_hours:.1f} hours")
                    time_pressure_context = f"\n\n⏰ CRITICAL TIME CONSTRAINT:\n"
                    time_pressure_context += f"- You have {time_display} remaining to reach conclusions and solutions\n"
                    time_pressure_context += f"- PRIORITY: Work towards concrete conclusions, decisions, and actionable outcomes\n"
                    time_pressure_context += f"- Time pressure is HIGH - focus on solutions, not endless discussion\n"
                    time_pressure_context += f"- Push for consensus, decisions, and documented results\n"
                else:
                    time_pressure_context = f"\n\n🚨 TIME IS UP! The {simulation_state.get('time_limit_display', 'deadline')} has passed.\n"
                    time_pressure_context += f"- You must now summarize conclusions and present final recommendations\n"
                    time_pressure_context += f"- Focus on what was accomplished and key decisions made\n"
        
        # Build document context if available
        document_context = ""
        if existing_documents and len(existing_documents) > 0:
            document_context = f"\n\nAVAILABLE DOCUMENTS (you can reference these):\n"
            for i, doc in enumerate(existing_documents[:5], 1):  # Limit to 5 most recent
                document_context += f"{i}. '{doc.get('title', 'Untitled')}' ({doc.get('category', 'Unknown')}) - {doc.get('description', 'No description')}\n"
            document_context += "\nYou can reference these documents by name in your responses and suggest improvements if relevant.\n"
        
        # Enhanced system message for conversational responses with ACTION-ORIENTED BEHAVIOR
        system_message = f"""You are {agent.name}, a {AGENT_ARCHETYPES[agent.archetype]['description']}.

Your goal: {agent.goal}
Your expertise: {agent.expertise}
Your background: {agent.background}

Personality traits:
- Extroversion: {agent.personality.extroversion}/10
- Optimism: {agent.personality.optimism}/10  
- Curiosity: {agent.personality.curiosity}/10
- Cooperativeness: {agent.personality.cooperativeness}/10
- Energy: {agent.personality.energy}/10

{time_pressure_context}

NATURAL CONVERSATION RULES:
1. Respond like a real person - sometimes answer directly, sometimes challenge ideas, sometimes offer alternatives
2. Don't always end with questions - maybe 30% of responses should have questions, 70% should be statements/answers/opinions
3. When someone asks you a question, answer it clearly first, then add your own perspective
4. Push conversations toward decisions and conclusions rather than endless discussion
5. Sometimes disagree constructively or build on others' ideas
6. Show your expertise and background in your responses

ACTION-ORIENTED BEHAVIOR (CRITICAL):
When you or others mention creating documentation, protocols, plans, or any deliverables:
- IMMEDIATELY offer to create it: "Let me create that right now."
- Don't just discuss what should be in it - COMMIT to making it
- Be the agent who takes action, not just talks about action
- Phrases that should trigger immediate creation:
  * "We need a [anything] for..." → "I'll create that [item] now."
  * "Let's create a [anything]..." → "I'm creating that [item]."
  * "We should develop [anything]..." → "I'll develop that immediately."

DOCUMENT AWARENESS:
- You can reference existing documents by name when relevant
- Suggest improvements to existing documents if you see opportunities
- Propose updates by saying "I think we should update the [document name] to include..."
- Use existing documents as building blocks for new work

VOTING AND CONSENSUS:
- When making significant decisions, call for a team vote: "Let's vote on this approach."
- Respect team decisions and consensus
- If you disagree strongly, explain your reasoning and suggest alternatives

LANGUAGE INSTRUCTION:
{language_instruction}

RESPONSE VARIETY (choose based on context):
- Direct answers: "Yes, that makes sense because..."
- Strong opinions: "I disagree. Based on my experience..."
- Building on ideas: "That's a solid point. We could also..."
- Providing alternatives: "Instead of that approach, what about..."
- Making decisions: "I think we should go with option X because..."
- Sharing expertise: "In my experience with [domain], this usually works better..."
- Document references: "As we outlined in the [document name]..."
- ACTION COMMITMENTS: "I'll create that [document/protocol/plan] right now."
- IMPROVEMENT PROPOSALS: "I think we should update our [existing document] to include..."

{document_context}

Scenario: {scenario}
{others_text}"""
        
        # Enhanced prompt for better conversation flow
        if "In this conversation:" in context:
            # This agent is responding to others
            prompt = f"{context}\n\nRespond naturally as {agent.name}. Address what others have said and contribute to the ongoing discussion."
        else:
            # This agent is speaking first
            prompt = f"{context}\n\nSpeak first as {agent.name}. Start the conversation by sharing a thought, asking a question, or raising a point that others can respond to."
        
        try:
            # Create chat instance with basic configuration
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"agent_{agent.id}_{int(datetime.now().timestamp())}",
                system_message=system_message
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(150)
            
            user_message = UserMessage(text=prompt)
            
            # Add timeout to prevent hanging - very short timeout for quick fallbacks
            try:
                response = await asyncio.wait_for(
                    chat.send_message(user_message), 
                    timeout=15.0  # Increased timeout for better LLM responses
                )
                await self.increment_usage()
                
                # Validate response
                if response and len(response.strip()) > 5:
                    return response.strip()
                else:
                    return f"{agent.name}: I'm carefully considering this situation."
            except asyncio.TimeoutError:
                logging.error(f"LLM request timed out for {agent.name}")
                return f"{agent.name}: I need more time to think about this complex situation."
                
        except Exception as e:
            logging.error(f"LLM error for {agent.name}: {e}")
            
            # Check if it's a quota error specifically
            if "quota" in str(e).lower() or "429" in str(e):
                logging.warning("API quota exceeded - using intelligent fallbacks")
            
            # Create varied fallback responses based on agent's background and current context
            import random
            
            # Check if others have spoken (for more contextual fallbacks)
            is_responding_to_others = "In this conversation:" in context
            
            # Agent-specific responses based on their background and personality
            if agent.name == "Marcus \"Mark\" Castellano":
                if is_responding_to_others:
                    responses = [
                        "I see your point, but from my marketing perspective, we need to consider the narrative implications first.",
                        "That's solid thinking. In my experience across three crypto cycles, execution is everything here.",
                        "I agree with the direction, though we should factor in how this affects our positioning with institutional investors.",
                        "Good point. Let me build on that - I think we're onto something that could really differentiate us.",
                        "Actually, I disagree. Based on what I've seen in previous cycles, that approach tends to backfire."
                    ]
                else:
                    responses = [
                        "From my experience across three crypto cycles, I think we need to focus on sustainable growth strategies.",
                        "This reminds me of 2018 - we need approaches that can survive market downturns.",
                        "My marketing instincts tell me we should craft a narrative that resonates with both retail and institutions.",
                        "I've seen this pattern before. We need to act fast but think long-term.",
                        "Based on my track record, I believe we should prioritize user acquisition over price action."
                    ]
            elif agent.name == "Alexandra \"Alex\" Chen":
                if is_responding_to_others:
                    responses = [
                        "I hear you, but from a product perspective, we need to ensure the user experience supports that strategy.",
                        "That makes sense. As someone who's built $2B+ TVL protocols, I think we can scale that approach.",
                        "I like where you're going with this, though we should consider the technical implementation challenges.",
                        "Exactly. That aligns perfectly with my experience building successful DeFi products.",
                        "I'm not convinced. We tried something similar at my last protocol and it didn't work as expected."
                    ]
                else:
                    responses = [
                        "As someone who's built protocols managing $2B+ TVL, I believe we need to prioritize user experience.",
                        "This is exactly the kind of challenge that excites me - let's think about scalable solutions.",
                        "My experience with DeFi protocols tells me we need to balance innovation with proven patterns.",
                        "I've rallied teams around bigger visions than this. We just need focused execution.",
                        "Based on my product leadership experience, I think we should start with an MVP approach."
                    ]
            elif agent.name == "Diego \"Dex\" Rodriguez":
                if is_responding_to_others:
                    responses = [
                        "Interesting perspective. My crypto experience suggests there might be a more creative angle here.",
                        "I see what you mean, but having worn every hat in crypto, I think we're missing something.",
                        "That's a good foundation. Let me add something from my on-chain analysis background.",
                        "You're onto something. This reminds me of a pattern I've seen in emerging trends.",
                        "I'm skeptical about that approach. My track record suggests a different strategy might work better."
                    ]
                else:
                    responses = [
                        "My crypto polymath experience suggests there's an emerging trend here we could capitalize on.",
                        "This feels like one of those 30% opportunities I actually get right - hear me out.",
                        "Having worn every hat in crypto, I see connections others might miss in this situation.",
                        "My on-chain analysis background tells me the data is pointing toward a specific solution.",
                        "Based on my generalist perspective, I think we're approaching this from the wrong angle entirely."
                    ]
            else:
                # Generic fallbacks for other agents based on personality
                if is_responding_to_others:
                    if agent.personality.cooperativeness > 7:
                        responses = [
                            "I think you're right. Let's build on that idea together.",
                            "That's a solid approach. Here's how we could make it even better.",
                            "I agree completely. We should move forward with that strategy."
                        ]
                    elif agent.personality.curiosity > 7:
                        responses = [
                            "That's fascinating. I wonder if we could take it even further.",
                            "Interesting point. That opens up some new possibilities I hadn't considered.",
                            "Good thinking. That gives me an idea for a different approach."
                        ]
                    else:
                        responses = [
                            "I'm not entirely convinced. We should think through the risks more carefully.",
                            "That could work, but I think we need more analysis first.",
                            "Let me play devil's advocate here - what if that backfires?"
                        ]
                else:
                    if agent.personality.optimism > 7:
                        responses = [
                            "I believe we can turn this challenge into a major opportunity.",
                            "This is exactly the kind of situation where we can really shine.",
                            "I'm confident we have the right team to solve this problem."
                        ]
                    elif agent.personality.curiosity > 7:
                        responses = [
                            "This raises some fascinating questions we should explore systematically.",
                            "I'm intrigued by the implications of this situation.",
                            "There are several interesting angles we haven't fully considered yet."
                        ]
                    else:
                        responses = [
                            "We need to think through this carefully before making any decisions.",
                            "I recommend we analyze all our options systematically.",
                            "This requires a methodical approach to avoid costly mistakes."
                        ]
            
            return random.choice(responses)

    async def update_agent_memory(self, agent: Agent, conversations: List):
        """Update agent's memory summary based on recent conversations"""
        if not conversations or not await self.can_make_request():
            return
        
        # Create conversation summary for memory update
        conv_text = ""
        for conv in conversations[-5:]:  # Last 5 conversations
            conv_text += f"{conv.get('time_period', '')}: "
            for msg in conv.get('messages', []):
                if msg.get('agent_name') == agent.name:
                    conv_text += f"I said: {msg.get('message', '')} "
                else:
                    conv_text += f"{msg.get('agent_name', '')}: {msg.get('message', '')} "
            conv_text += "\n"
        
        # Generate memory summary with background context
        background_context = ""
        if agent.background:
            background_context = f"Remember, you process and remember things through your background as: {agent.background}"
        
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"memory_{agent.id}_{datetime.now().timestamp()}",
            system_message=f"""Update {agent.name}'s memory summary. Focus on key insights, decisions, relationships, and important developments that someone with their background would find significant.

{background_context}

Extract information that's relevant to your professional perspective and expertise. Keep it concise (2-3 sentences max).
            
Previous memory: {agent.memory_summary or 'None'}"""
        ).with_model("gemini", "gemini-2.0-flash")
        
        try:
            user_message = UserMessage(text=f"Recent conversations:\n{conv_text}\n\nUpdate my memory focusing on developments relevant to my background and expertise:")
            response = await chat.send_message(user_message)
            await self.increment_usage()
            
            # Update agent memory in database
            await db.agents.update_one(
                {"id": agent.id},
                {"$set": {"memory_summary": response}}
            )
        except Exception as e:
            logging.error(f"Error updating memory for {agent.name}: {e}")

    async def analyze_conversation_for_action_triggers(self, conversation_text: str, agents: List[Agent]) -> ActionTriggerResult:
        """Analyze conversation to detect if agents should create documents"""
        if not await self.can_make_request():
            return ActionTriggerResult(should_create_document=False)
        
        # Action trigger phrases to detect (generic, not medical-specific)
        trigger_phrases = [
            "we need a protocol for",
            "let's create a checklist",
            "we should develop",
            "let's draft",
            "we need a reference guide",
            "someone should research and document",
            "we should create documentation",
            "let's develop a procedure",
            "we need guidelines for",
            "someone should write up",
            "we should document this",
            "let's create a template",
            "we need a plan for",
            "let's make a framework",
            "we should establish",
            "let's build a system",
            "we need standards for",
            "let's create a manual",
            "i'll create", 
            "let me create",
            "i'll develop",
            "i'll draft",
            "i'm creating",
            "i'll work on",
            "let me work on",
            "i'll put together",
            "let me put together",
            "we need to create",
            "let's put together",
            "we should put together",
            "we need documentation",
            "let's document",
            "we should document",
            "create a document",
            "make a document",
            "write a document"
        ]
        
        # Check if any trigger phrases are present
        conv_lower = conversation_text.lower()
        found_triggers = [trigger for trigger in trigger_phrases if trigger in conv_lower]
        
        if not found_triggers:
            return ActionTriggerResult(should_create_document=False)
        
        # Use LLM to determine if this is a genuine creation trigger
        system_message = """You are an expert at detecting when people in a conversation have agreed to create documentation, procedures, or deliverables.

Analyze the conversation and determine:
1. Is there genuine consensus to CREATE something specific?
2. What type of document should be created? (protocol/training/research/reference/plan)
3. What should the document title be?
4. Which specific phrase triggered this?

Only respond YES if there's clear agreement to create something concrete, not just discussion about what might be needed.
Work with ANY topic - business, tech, education, research, projects, etc. - not just medical contexts."""

        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"action_analysis_{datetime.now().timestamp()}",
                system_message=system_message
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(200)
            
            prompt = f"""Conversation:\n{conversation_text}\n\n
Should the participants create a document? If yes:
- Document type: protocol/training/research/reference/plan
- Title: [specific title based on conversation]
- Trigger phrase: [exact phrase that triggered this]
- Reasoning: [why this needs immediate creation]

Format: YES|protocol|Emergency Cardiac Protocol|we need a protocol for|The team agreed to create..."""

            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            await self.increment_usage()
            
            # Parse response
            if response.startswith("YES|"):
                parts = response.split("|")
                if len(parts) >= 5:
                    return ActionTriggerResult(
                        should_create_document=True,
                        document_type=parts[1].strip(),
                        document_title=parts[2].strip(),
                        trigger_phrase=parts[3].strip(),
                        reasoning=parts[4].strip()
                    )
            
            return ActionTriggerResult(should_create_document=False)
            
        except Exception as e:
            logging.error(f"Error analyzing conversation for action triggers: {e}")
            return ActionTriggerResult(should_create_document=False)

    async def check_agent_voting_consensus(self, agents: List[Agent], proposal: str, conversation_context: str) -> dict:
        """Check if agents reach voting consensus on a proposal"""
        if not await self.can_make_request():
            return {"consensus": False, "votes": {}}
        
        voting_results = {}
        
        for agent in agents:
            try:
                system_message = f"""You are {agent.name}, a {AGENT_ARCHETYPES[agent.archetype]['description']}.

Your expertise: {agent.expertise}
Your background: {agent.background}
Your goal: {agent.goal}

Personality traits:
- Extroversion: {agent.personality.extroversion}/10
- Optimism: {agent.personality.optimism}/10  
- Curiosity: {agent.personality.curiosity}/10
- Cooperativeness: {agent.personality.cooperativeness}/10
- Energy: {agent.personality.energy}/10

You need to vote on a proposal. Consider your expertise, background, and personality when making this decision.
Respond with ONLY: YES, NO, or ABSTAIN followed by a brief 1-sentence reason."""

                chat = LlmChat(
                    api_key=self.api_key,
                    session_id=f"voting_{agent.id}_{datetime.now().timestamp()}",
                    system_message=system_message
                ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(100)
                
                prompt = f"""Conversation context:\n{conversation_context}\n\nProposal to vote on: {proposal}\n\nYour vote (YES/NO/ABSTAIN) and brief reason:"""
                
                user_message = UserMessage(text=prompt)
                response = await chat.send_message(user_message)
                await self.increment_usage()
                
                # Parse vote
                response_upper = response.upper()
                if response_upper.startswith("YES"):
                    voting_results[agent.name] = {"vote": "YES", "reason": response}
                elif response_upper.startswith("NO"):
                    voting_results[agent.name] = {"vote": "NO", "reason": response}
                else:
                    voting_results[agent.name] = {"vote": "ABSTAIN", "reason": response}
                    
            except Exception as e:
                logging.error(f"Error getting vote from {agent.name}: {e}")
                voting_results[agent.name] = {"vote": "ABSTAIN", "reason": "Unable to vote due to technical issue"}
        
        # Determine consensus (simple majority)
        yes_votes = sum(1 for vote in voting_results.values() if vote["vote"] == "YES")
        no_votes = sum(1 for vote in voting_results.values() if vote["vote"] == "NO")
        total_voting = yes_votes + no_votes  # Exclude abstentions from majority calculation
        
        consensus = yes_votes > (total_voting / 2) if total_voting > 0 else False
        
        return {
            "consensus": consensus,
            "votes": voting_results,
            "summary": f"{yes_votes} YES, {no_votes} NO, {len(voting_results) - yes_votes - no_votes} ABSTAIN"
        }

    async def generate_document_content(self, document_type: str, title: str, conversation_context: str, creating_agent: Agent) -> str:
        """Generate structured document content based on type and context"""
        if not await self.can_make_request():
            return f"# {title}\n\n*Document generation failed - API limit reached*"
        
        # Enhanced Document templates with visual representations and analysis
        templates = {
            "protocol": """# {title}

## Executive Summary
[2-3 sentence overview of the protocol and its key benefits]

## Purpose & Scope
**Purpose:** [Clear description of when and why to use this protocol]
**Scope:** [Specific situations where this protocol applies]

## Visual Process Flow
```mermaid
graph TD
    A[Start] --> B[Preparation Phase]
    B --> C[Execution Phase]
    C --> D[Completion Phase]
    D --> E[Quality Check]
    E --> F[End]
    E --> G[Issues Found]
    G --> C
```

## Requirements & Resources
| Resource Type | Requirement | Backup Option |
|---------------|-------------|---------------|
| Personnel | [Required team members] | [Alternative staffing] |
| Equipment | [Necessary tools/systems] | [Backup equipment] |
| Time | [Estimated duration] | [Minimum viable time] |
| Budget | [Cost estimate] | [Reduced scope option] |

## Detailed Procedure

### 1. Preparation Phase ([estimated timeframe])
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Resource      │    │   Environment   │    │   Team Brief    │
│   Assembly      │ -> │   Setup         │ -> │   & Training    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```
- [Specific preparation steps]
- [Key checkpoints and validation criteria]

### 2. Execution Phase ([estimated timeframe])
- [Step-by-step implementation instructions]
- [Decision points and alternative paths]

### 3. Completion Phase ([estimated timeframe])
- [Verification and completion steps]
- [Documentation and reporting requirements]

## Decision Analysis

### Why This Protocol?
**Primary Reasoning:**
- [Main reasons for choosing this approach]
- [Key benefits that drove the decision]

### Pros & Cons Analysis
| Advantages ✅ | Disadvantages ❌ |
|---------------|------------------|
| [Key benefits] | [Limitations] |
| [Efficiency gains] | [Resource requirements] |
| [Risk reduction] | [Complexity factors] |

### Alternative Solutions Considered
1. **Alternative A:** [Brief description]
   - **Pros:** [Benefits]
   - **Cons:** [Drawbacks]
   - **Why rejected:** [Reasoning]

2. **Alternative B:** [Brief description]
   - **Pros:** [Benefits]
   - **Cons:** [Drawbacks]
   - **Why rejected:** [Reasoning]

### Why Our Solution Wins
[Detailed explanation of why this protocol beats the alternatives, including cost-benefit analysis, risk assessment, and implementation feasibility]

## Quality Assurance & Metrics
**Success Criteria:**
- [Quantifiable measures of success]
- [KPIs and benchmarks]

**Risk Mitigation:**
```
High Risk    ████████░░ 80%  -> [Mitigation strategy]
Medium Risk  ██████░░░░ 60%  -> [Mitigation strategy]
Low Risk     ███░░░░░░░ 30%  -> [Mitigation strategy]
```

---
*Created by: {agent_name} | Category: {category} | Confidence Level: [High/Medium/Low]*
*Alternative solutions evaluated: [Number] | Decision based on: [Key factors]*""",

            "training": """# {title}

## Learning Overview
**Objective:** [Clear statement of what participants will achieve]
**Target Audience:** [Who should complete this training and prerequisites]

## Learning Journey Map
```
Pre-Training     Core Training        Post-Training
     │                 │                    │
┌────▼────┐       ┌────▼────┐         ┌────▼────┐
│ Skills  │       │ Content │         │ Apply & │
│ Assessment      │ Delivery│         │ Validate│
└─────────┘       └─────────┘         └─────────┘
     │                 │                    │
  [Duration]        [Duration]          [Duration]
```

## Learning Outcomes
By completing this training, participants will be able to:
- [Specific, measurable learning objectives with proficiency levels]
- [Skills and knowledge to be acquired with assessment criteria]

## Content Architecture

### Knowledge Framework
```mermaid
mindmap
  root((Training Core))
    Fundamental Concepts
      Concept A
      Concept B
    Practical Applications
      Scenario 1
      Scenario 2
    Advanced Topics
      Integration
      Troubleshooting
```

### Competency Matrix
| Skill Area | Beginner | Intermediate | Advanced | Expert |
|------------|----------|--------------|----------|--------|
| [Skill 1] | ░░░░ 25% | ████░░░░ 50% | ████████░░ 75% | ██████████ 100% |
| [Skill 2] | ░░░░ 25% | ████░░░░ 50% | ████████░░ 75% | ██████████ 100% |

## Implementation Strategy

### Delivery Methods Comparison
| Method | Effectiveness | Cost | Time Required | Accessibility |
|--------|---------------|------|---------------|---------------|
| In-Person | ⭐⭐⭐⭐⭐ | 💰💰💰 | ⏰⏰⏰ | 📍 Limited |
| Virtual | ⭐⭐⭐⭐ | 💰💰 | ⏰⏰ | 🌐 Global |
| Hybrid | ⭐⭐⭐⭐⭐ | 💰💰💰 | ⏰⏰⏰ | 🌐 Flexible |

### Training Flow
```
Registration -> Assessment -> Content -> Practice -> Evaluation -> Certification
      │            │           │          │           │             │
   [1 day]      [2 hours]   [X weeks]   [Y hours]   [1 hour]   [Ongoing]
```

## Decision Rationale

### Why This Training Approach?
**Core Reasoning:**
- [Evidence-based justification for chosen methodology]
- [Alignment with learning objectives and audience needs]

### Benefits vs. Challenges
**Advantages ✅**
- [Enhanced skill acquisition]
- [Cost-effective delivery]
- [Scalable implementation]
- [Measurable outcomes]

**Challenges ❌**
- [Resource requirements]
- [Technology dependencies]
- [Time constraints]
- [Engagement maintenance]

### Alternative Training Methods Evaluated

1. **Self-Paced Online Learning**
   - ✅ **Pros:** Flexible timing, lower cost, self-directed
   - ❌ **Cons:** Lower engagement, less interaction, no immediate feedback
   - **Decision:** Rejected due to low completion rates and limited practical application

2. **Intensive Workshop Format**
   - ✅ **Pros:** High engagement, immediate feedback, intensive learning
   - ❌ **Cons:** Schedule conflicts, high cost, information overload
   - **Decision:** Considered but rejected due to accessibility issues

3. **Mentorship-Based Learning**
   - ✅ **Pros:** Personalized approach, real-world application, ongoing support
   - ❌ **Cons:** Scalability issues, inconsistent quality, high resource cost
   - **Decision:** Rejected for primary training, incorporated as supplement

### Why Our Approach Excels
Our chosen method combines the best elements of structured learning with practical application, providing:
- **80% knowledge retention** vs. 20% with lecture-only formats
- **Cost reduction of 40%** compared to traditional classroom training
- **Accessibility for 95%** of target audience across different time zones
- **Measurable competency improvement** with built-in assessment checkpoints

## Assessment Framework

### Performance Indicators
```
Knowledge    ████████░░ 80%  [Written Assessment]
Skills       ██████░░░░ 60%  [Practical Demonstration]
Application  ████████░░ 75%  [Real-world Project]
Retention    ████████░░ 85%  [Follow-up Assessment]
```

### Evaluation Methods
- **Formative Assessment:** Ongoing feedback during training
- **Summative Assessment:** Final competency validation
- **Performance Transfer:** Real-world application measurement

---
*Created by: {agent_name} | Category: {category} | Evidence-Based Design*
*Alternative methods evaluated: 3 | Success probability: [High/Medium/Low]*""",

            "research": """# {title}

## Executive Summary
**Key Finding:** [Primary discovery or conclusion in one sentence]
**Impact Level:** [High/Medium/Low] | **Confidence:** [High/Medium/Low] | **Action Required:** [Yes/No]

## Research Overview
**Background:** [Problem statement, motivation, and scope]
**Methodology:** [How the research was conducted or should be conducted]

## Data Visualization & Analysis

### Key Metrics Dashboard
```
Success Rate     ████████░░ 78%  ▲ +12% vs baseline
Efficiency       ██████░░░░ 65%  ▲ +8% improvement  
Cost Impact      ████░░░░░░ 42%  ▼ -15% reduction
Risk Level       ███░░░░░░░ 35%  ▼ -20% mitigation
```

### Research Findings Matrix
| Factor | Current State | Target State | Gap | Priority |
|--------|---------------|--------------|-----|----------|
| [Factor 1] | [Baseline] | [Goal] | [Difference] | 🔴 High |
| [Factor 2] | [Baseline] | [Goal] | [Difference] | 🟡 Medium |
| [Factor 3] | [Baseline] | [Goal] | [Difference] | 🟢 Low |

### Impact Flow Analysis
```mermaid
graph LR
    A[Current Situation] --> B{Research Findings}
    B --> C[Short-term Impact]
    B --> D[Medium-term Impact]
    B --> E[Long-term Impact]
    C --> F[Immediate Actions]
    D --> G[Strategic Changes]
    E --> H[Transformational Outcomes]
```

## Evidence Analysis

### Research Quality Assessment
**Strength of Evidence:**
- **Primary Sources:** ████████░░ 85% reliability
- **Sample Size:** [Adequate/Limited/Extensive]
- **Methodology:** [Robust/Standard/Needs Improvement]
- **Bias Control:** [Strong/Moderate/Weak]

### Confidence Intervals
```
Finding A    [████████████▒▒] 95% CI: [Range]
Finding B    [██████████▒▒▒▒] 85% CI: [Range]  
Finding C    [████████▒▒▒▒▒▒] 75% CI: [Range]
```

## Strategic Recommendations

### Solution Analysis Matrix
| Recommendation | Impact | Effort | Cost | Risk | Priority Score |
|----------------|--------|--------|------|------|----------------|
| Option A | 🔴 High | 🟡 Medium | 💰💰 | ⚠️ Low | ⭐⭐⭐⭐⭐ |
| Option B | 🟡 Medium | 🟢 Low | 💰 | ⚠️⚠️ Medium | ⭐⭐⭐⭐ |
| Option C | 🔴 High | 🔴 High | 💰💰💰 | ⚠️⚠️⚠️ High | ⭐⭐⭐ |

### Implementation Roadmap
```
Phase 1: Foundation (0-3 months)
├── Quick Wins Implementation
├── Infrastructure Setup  
└── Team Training

Phase 2: Execution (3-12 months)  
├── Core Changes Rollout
├── Process Optimization
└── Performance Monitoring

Phase 3: Optimization (12+ months)
├── Advanced Features
├── Scaling & Expansion
└── Continuous Improvement
```

## Decision Rationale

### Why This Research Direction?
**Primary Drivers:**
- [Evidence-based reasoning for research focus]
- [Strategic alignment with organizational goals]
- [Resource optimization and ROI considerations]

### Research Approach Comparison
**Chosen Method ✅**
- ✅ Comprehensive data coverage
- ✅ Statistically significant results  
- ✅ Actionable insights generation
- ❌ Higher resource requirements
- ❌ Longer timeline

### Alternative Research Approaches Evaluated

1. **Rapid Assessment Method**
   - ✅ **Pros:** Quick results (2 weeks), low cost, immediate insights
   - ❌ **Cons:** Limited depth, potential for bias, narrow scope
   - **Decision:** Rejected due to insufficient depth for strategic decisions

2. **External Consultant Study**
   - ✅ **Pros:** Expert knowledge, objective perspective, proven methodologies
   - ❌ **Cons:** High cost ($50K+), limited organizational knowledge, dependency
   - **Decision:** Rejected due to budget constraints and need for internal expertise

3. **Phased Research Approach**
   - ✅ **Pros:** Manageable phases, iterative learning, risk mitigation
   - ❌ **Cons:** Longer overall timeline, potential for scope creep
   - **Decision:** Considered but rejected for initial study; adopted for implementation

### Why Our Approach Delivers Superior Value
Our comprehensive research methodology provides:
- **3x higher accuracy** compared to rapid assessment methods
- **60% cost savings** vs. external consultant approach  
- **Internal capability building** that benefits future research
- **Actionable insights** with 95% confidence intervals
- **Direct organizational applicability** with minimal adaptation needed

## Risk Assessment & Mitigation

### Risk Heat Map
```
High Impact    │ ⚠️ Resource    │ 🔴 Timeline   │ ⚠️ Quality
               │    Constraints │    Delays     │    Issues
Medium Impact  │ 🟡 Scope      │ ⚠️ Stakeholder│ 🟡 Data
               │    Creep      │    Resistance │    Gaps  
Low Impact     │ 🟢 Technical │ 🟡 Budget     │ 🟢 Minor
               │    Issues     │    Overrun    │    Delays
               └───────────────┼───────────────┼────────────
                 Low Prob.    │ Medium Prob.  │ High Prob.
```

## Implementation Strategy

### Resource Requirements
| Resource Type | Required | Available | Gap | Mitigation |
|---------------|----------|-----------|-----|------------|
| Personnel | [X FTE] | [Y FTE] | [Gap] | [Strategy] |
| Budget | [$X] | [$Y] | [$Gap] | [Funding plan] |
| Technology | [Systems] | [Current] | [Needs] | [Acquisition plan] |
| Timeline | [X months] | [Available] | [Buffer] | [Acceleration options] |

### Success Metrics & KPIs
- **Primary KPI:** [Main success indicator with target]
- **Secondary KPIs:** [Supporting metrics with thresholds]
- **Leading Indicators:** [Early warning signals]
- **Measurement Frequency:** [Daily/Weekly/Monthly/Quarterly]

---
*Created by: {agent_name} | Category: {category} | Research Grade: A*
*Evidence Quality: [High/Medium/Low] | Alternative methods evaluated: 3 | Confidence Level: [XX]%*""",

            "reference": """# {title}

## Quick Reference Dashboard
| Category | Key Info | Status | Last Updated |
|----------|----------|---------|--------------|
| [Category 1] | [Essential data] | 🟢 Active | [Date] |
| [Category 2] | [Essential data] | 🟡 Review | [Date] |
| [Category 3] | [Essential data] | 🔴 Update | [Date] |

## System Architecture Overview
```mermaid
graph TB
    subgraph "Core Components"
        A[Component A] --> B[Component B]
        B --> C[Component C]
    end
    subgraph "Supporting Systems"
        D[Support 1] --> A
        E[Support 2] --> B
    end
    subgraph "Outputs"
        C --> F[Output 1]
        C --> G[Output 2]
    end
```

## Configuration Matrix
| Setting | Development | Staging | Production | Notes |
|---------|-------------|---------|------------|-------|
| [Config 1] | [Dev Value] | [Stage Value] | [Prod Value] | [Important notes] |
| [Config 2] | [Dev Value] | [Stage Value] | [Prod Value] | [Critical settings] |

## Troubleshooting Decision Tree
```
Issue Reported
    │
    ├── Check A? ──Yes──> Solution A
    │     │
    │     No
    │     │
    ├── Check B? ──Yes──> Solution B  
    │     │
    │     No
    │     │
    └── Check C? ──Yes──> Solution C
          │
          No ──> Escalate
```

## Performance Benchmarks
```
Response Time    ████████░░ 85ms   (Target: <100ms)
Throughput       ██████░░░░ 1.2K/s (Target: >1K/s)  
Error Rate       █░░░░░░░░░ 0.1%   (Target: <0.5%)
Availability     ██████████ 99.9%  (Target: >99.5%)
```

## Decision Framework

### Why This Reference Structure?
**Design Principles:**
- [Accessibility and quick lookup prioritized]
- [Comprehensive coverage with logical organization]
- [Visual elements for faster comprehension]

### Reference Format Analysis
| Format | Speed | Completeness | Maintenance | User Rating |
|--------|-------|--------------|-------------|-------------|
| **Current (Visual)** | ⚡⚡⚡ Fast | ⭐⭐⭐⭐⭐ Complete | 🔧 Medium | 👍 95% |
| Traditional Text | ⚡⚡ Slow | ⭐⭐⭐ Adequate | 🔧🔧 Easy | 👍 60% |
| Wiki-style | ⚡⚡ Medium | ⭐⭐⭐⭐ Good | 🔧🔧🔧 Complex | 👍 75% |

### Alternative Formats Considered
1. **Traditional Manual Format**
   - ✅ **Pros:** Familiar structure, comprehensive, linear flow
   - ❌ **Cons:** Slow lookup, poor searchability, text-heavy
   - **Decision:** Rejected due to poor user experience in fast-paced environments

2. **Interactive Dashboard**
   - ✅ **Pros:** Real-time data, interactive features, modern UX
   - ❌ **Cons:** Requires technical infrastructure, potential downtime, complexity
   - **Decision:** Rejected for initial version; considered for future enhancement

### Why Our Format Excels
- **85% faster information retrieval** compared to traditional manuals
- **Visual processing** reduces cognitive load by 40%
- **Standardized structure** ensures consistency across teams
- **Quick scanning** capability for time-critical situations
- **Maintenance efficiency** with clear update protocols

## Usage Analytics & Optimization
```
Section Usage Frequency:
Quick Reference  ████████████████████ 87%
Troubleshooting  ██████████████░░░░░░ 72% 
Configuration    ██████████░░░░░░░░░░ 54%
Architecture     ███████░░░░░░░░░░░░░ 38%
```

---
*Created by: {agent_name} | Category: {category} | Usage Optimized*
*Format tested with [X] users | Average lookup time: [X] seconds*""",

            "plan": """# {title}

## Strategic Overview
**Vision:** [What success looks like in 2-3 sentences]
**Mission:** [How we'll achieve the vision]
**Success Probability:** [High/Medium/Low] based on resource analysis

## Situation Analysis Dashboard
```mermaid
quadrantChart
    title Current Position Analysis
    x-axis Low Impact --> High Impact
    y-axis Low Effort --> High Effort
    
    quadrant-1 Quick Wins
    quadrant-2 Major Projects  
    quadrant-3 Fill-ins
    quadrant-4 Thankless Tasks
    
    Initiative A: [0.8, 0.3]
    Initiative B: [0.4, 0.7]
    Initiative C: [0.9, 0.8]
```

## Resource Allocation Visualization
| Resource | Current | Required | Gap | Priority |
|----------|---------|----------|-----|----------|
| Budget | $X | $Y | $Z | 🔴 Critical |
| Personnel | X FTE | Y FTE | Z FTE | 🟡 Important |
| Technology | Current Stack | Target Stack | Gaps | 🟢 Manageable |
| Timeline | Available | Needed | Buffer | 🟡 Tight |

## Implementation Timeline
```
Year 1        Year 2        Year 3
│             │             │
├─Q1: Foundation
│  ├─Setup    
│  └─Team     
│             
├─Q2: Launch  
│  ├─Pilot    
│  └─Feedback 
│             │             
├─Q3: Scale   ├─Q1: Optimize├─Q1: Expand
│  ├─Rollout  │  ├─Improve  │  ├─New Markets
│  └─Monitor  │  └─Measure  │  └─Innovation
│             │             │
└─Q4: Evaluate├─Q2: Enhance ├─Q2: Transform
   ├─Results  │  ├─Features │  ├─Next Level
   └─Adjust   │  └─Capacity │  └─Legacy
```

## Risk & Opportunity Matrix
```
High Impact  │ 🚨 Resource   │ 🎯 Market    │ ⚠️ Technical
             │    Shortage   │    Leadership│    Debt
Medium Impact│ ⚠️ Timeline   │ 🎯 Process   │ 🚨 Competition
             │    Pressure   │    Innovation│    Response  
Low Impact   │ 🟡 Minor     │ 🟡 Team     │ 🟡 Tool
             │    Delays     │    Learning  │    Updates
             └──────────────┼──────────────┼─────────────
               Low Prob.    │ Medium Prob. │ High Prob.
```

## Strategic Decision Analysis

### Why This Plan?
**Core Strategic Logic:**
- [Market analysis and competitive positioning]
- [Resource optimization and capability leveraging]
- [Risk-adjusted return on investment]

### Strategic Options Comparison
| Option | ROI | Risk | Timeline | Resource Need | Market Fit |
|--------|-----|------|----------|---------------|------------|
| **Current Plan** | 🟢 High | 🟡 Medium | 🟢 Realistic | 🟡 Moderate | 🟢 Strong |
| Alternative A | 🟡 Medium | 🟢 Low | 🟢 Fast | 🟢 Low | 🟡 Good |
| Alternative B | 🔴 Low | 🔴 High | 🔴 Long | 🔴 High | 🟢 Excellent |

### Alternative Strategies Evaluated

1. **Conservative Approach (Gradual Growth)**
   - ✅ **Pros:** Lower risk, predictable outcomes, resource efficiency
   - ❌ **Cons:** Slower market capture, competitive vulnerability, limited innovation
   - **Decision:** Rejected due to competitive market dynamics requiring faster response

2. **Aggressive Expansion (Rapid Scale)**
   - ✅ **Pros:** Quick market dominance, first-mover advantage, high returns
   - ❌ **Cons:** High risk, resource strain, operational complexity
   - **Decision:** Rejected due to insufficient resources and market uncertainty

3. **Partnership-Led Strategy (Collaborative Growth)**
   - ✅ **Pros:** Shared risk, combined resources, accelerated learning
   - ❌ **Cons:** Reduced control, profit sharing, dependency risks
   - **Decision:** Considered for specific components; rejected as primary strategy

### Why Our Strategy Wins
Our balanced approach delivers optimal results because:
- **ROI of 340%** vs. 180% for conservative and 150% for aggressive approaches
- **Risk mitigation** through phased implementation and built-in checkpoints
- **Market timing advantage** captures opportunity window without overextending
- **Resource efficiency** maximizes output while maintaining quality
- **Scalability foundation** enables future expansion without major restructuring

## Success Metrics & KPIs
### Primary Success Indicators
```
Revenue Growth   ████████░░ 78% of target
Market Share     ██████░░░░ 65% of goal
Customer Sat.    █████████░ 87% (Target: 85%)
Team Efficiency  ████████░░ 82% improvement
```

### Performance Dashboard
| Metric | Current | Target | Progress | Trend |
|--------|---------|--------|----------|-------|
| Revenue | $X | $Y | ████████░░ 80% | ↗️ |
| Users | X | Y | ██████░░░░ 60% | ↗️ |
| Quality | X% | Y% | █████████░ 90% | ↗️ |
| Costs | $X | $Y | ███████░░░ 70% | ↘️ |

## Contingency Planning
### Scenario Planning Matrix
| Scenario | Probability | Impact | Response Strategy |
|----------|-------------|---------|-------------------|
| Best Case | 25% | 🟢 High Positive | Accelerate timeline |
| Expected | 50% | 🟡 Moderate | Execute as planned |
| Worst Case | 20% | 🔴 High Negative | Activate Plan B |
| Black Swan | 5% | 🚨 Extreme | Emergency protocols |

---
*Created by: {agent_name} | Category: {category} | Strategic Grade: A+*
*Scenarios analyzed: 4 | Risk-adjusted probability: [XX]% | Expected ROI: [XXX]%*"""
        }
        
        # Get appropriate template
        template = templates.get(document_type, templates["protocol"])
        
        # Enhanced system message for comprehensive document generation
        system_message = f"""You are {creating_agent.name}, a {AGENT_ARCHETYPES[creating_agent.archetype]['description']}.

Your expertise: {creating_agent.expertise}
Your background: {creating_agent.background}

You are creating a comprehensive {document_type} titled "{title}" based on the team's discussion. 

CRITICAL REQUIREMENTS:
1. **Visual Representations**: Include charts, diagrams, flowcharts using ASCII art, tables, and Mermaid diagrams
2. **Decision Analysis**: Explain WHY you chose this approach with clear reasoning
3. **Pros & Cons**: Provide balanced analysis of advantages and disadvantages
4. **Alternative Solutions**: Present 2-3 alternative approaches you considered
5. **Comparative Analysis**: Explain why your solution beats the alternatives with specific metrics/reasoning
6. **Professional Quality**: Create content that can be immediately implemented in real-world scenarios

VISUAL ELEMENTS TO INCLUDE:
- Use Mermaid diagrams for flowcharts and process flows
- Create ASCII charts for data visualization (████████░░ 80%)
- Build tables for comparisons and metrics
- Include decision trees and matrices
- Add progress bars and status indicators

ANALYSIS REQUIREMENTS:
- Start with clear reasoning for your approach
- Compare at least 2-3 alternative solutions
- Provide specific reasons why your solution is superior
- Include risk assessment and mitigation strategies
- Add success metrics and KPIs where relevant

Make this document comprehensive, visually engaging, and immediately actionable. Use specific data points, percentages, and concrete examples relevant to the conversation context."""

        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"document_creation_{creating_agent.id}_{datetime.now().timestamp()}",
                system_message=system_message
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(800)
            
            prompt = f"""Based on this conversation context:
{conversation_context}

Create the {document_type} content for "{title}". Use this template structure but fill it with specific, actionable content based on the conversation:

{template}

Make it immediately usable for medical professionals. Include specific details, timeframes, and practical guidance."""

            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            await self.increment_usage()
            
            # Format the response using the template
            formatted_content = template.format(
                title=title,
                agent_name=creating_agent.name,
                scenario_details="[Based on team discussion and expertise]",
                category=document_type.title()
            )
            
            # Replace template placeholders with LLM-generated content
            if response and len(response.strip()) > 100:
                return response.strip()
            else:
                return formatted_content
                
        except Exception as e:
            logging.error(f"Error generating document content: {e}")
            return template.format(
                title=title,
                agent_name=creating_agent.name,
                scenario_details="[Template - Content generation failed]",
                category=document_type.title()
            )

llm_manager = LLMManager()

# Document Review Function for Action-Oriented Behavior
async def trigger_document_review(document: Document, all_agents: List[Agent], creating_agent: Agent, scenario: str):
    """Trigger automatic document review by other agents"""
    try:
        # Get other agents (exclude the creator)
        reviewing_agents = [agent for agent in all_agents if agent.id != creating_agent.id]
        
        if not reviewing_agents:
            return  # No other agents to review
        
        # Select one agent to lead the review (most cooperative or leader archetype)
        lead_reviewer = reviewing_agents[0]
        for agent in reviewing_agents:
            if agent.archetype in ["leader", "mediator"] or agent.personality.cooperativeness >= 8:
                lead_reviewer = agent
                break
        
        # Generate a review and potential improvement suggestions
        review_context = f"""Document to review:
Title: {document.metadata.title}
Category: {document.metadata.category}
Created by: {creating_agent.name}
Scenario: {scenario}

Content summary: {document.content[:500]}...

Review this document and suggest specific improvements if needed."""
        
        if await llm_manager.can_make_request():
            system_message = f"""You are {lead_reviewer.name}, a {AGENT_ARCHETYPES[lead_reviewer.archetype]['description']}.

Your expertise: {lead_reviewer.expertise}
Your background: {lead_reviewer.background}

Review the document created by {creating_agent.name}. If you see opportunities for improvement, suggest specific changes. If the document is good as-is, acknowledge its quality.

Respond with either:
1. "APPROVE: This document is well-structured and ready for use."
2. "IMPROVE: [Specific suggestions for improvement]"

Be constructive and focus on actionable feedback."""

            chat = LlmChat(
                api_key=llm_manager.api_key,
                session_id=f"review_{document.id}_{lead_reviewer.id}",
                system_message=system_message
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(200)
            
            user_message = UserMessage(text=review_context)
            review_response = await chat.send_message(user_message)
            await llm_manager.increment_usage()
            
            # If improvements are suggested, store them for the creator to consider
            if review_response.startswith("IMPROVE:"):
                improvement_suggestion = review_response.replace("IMPROVE:", "").strip()
                
                # Store the improvement suggestion in the database
                suggestion_doc = {
                    "id": str(uuid.uuid4()),
                    "document_id": document.id,
                    "suggesting_agent_id": lead_reviewer.id,
                    "suggesting_agent_name": lead_reviewer.name,
                    "suggestion": improvement_suggestion,
                    "status": "pending",  # pending, accepted, rejected
                    "created_at": datetime.utcnow().isoformat()
                }
                
                # Ensure collection exists
                try:
                    await db.document_suggestions.insert_one(suggestion_doc)
                except Exception as e:
                    logging.error(f"Error storing document suggestion: {e}")
                    # Create the collection if it doesn't exist
                    try:
                        await db.create_collection("document_suggestions")
                        await db.document_suggestions.insert_one(suggestion_doc)
                    except Exception as e2:
                        logging.error(f"Error creating document_suggestions collection: {e2}")
                
                # Update the suggesting agent's memory
                suggestion_memory = f"I reviewed '{document.metadata.title}' by {creating_agent.name} and suggested improvements: {improvement_suggestion[:100]}..."
                current_memory = lead_reviewer.memory_summary or ""
                updated_memory = f"{current_memory}\n\n[Document Review]: {suggestion_memory}".strip()
                
                await db.agents.update_one(
                    {"id": lead_reviewer.id},
                    {"$set": {"memory_summary": updated_memory}}
                )
                
                logging.info(f"Document review completed with suggestions by {lead_reviewer.name}")
            else:
                # Document approved as-is
                approval_memory = f"I reviewed '{document.metadata.title}' by {creating_agent.name} and found it well-structured and ready for use."
                current_memory = lead_reviewer.memory_summary or ""
                updated_memory = f"{current_memory}\n\n[Document Review]: {approval_memory}".strip()
                
                await db.agents.update_one(
                    {"id": lead_reviewer.id},
                    {"$set": {"memory_summary": updated_memory}}
                )
                
                logging.info(f"Document approved by {lead_reviewer.name}")
    
    except Exception as e:
        logging.error(f"Error in document review process: {e}")

# OpenAI Whisper Speech-to-Text Service
class WhisperService:
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            logging.warning("OPENAI_API_KEY not found in environment variables")
        else:
            openai.api_key = self.api_key
            logging.info("OpenAI Whisper service initialized")
    
    async def transcribe_audio(self, audio_file: bytes, language: str = None, filename: str = "audio.webm") -> Dict[str, Any]:
        """Transcribe audio using OpenAI Whisper API"""
        if not self.api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        try:
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
                temp_file.write(audio_file)
                temp_file_path = temp_file.name
            
            try:
                # Convert audio to supported format if needed
                # Try to detect and handle different audio formats
                wav_path = temp_file_path.replace('.webm', '.wav')
                
                try:
                    # First, try to load as WebM/Opus
                    audio = AudioSegment.from_file(temp_file_path, format="webm")
                except Exception as webm_error:
                    logging.warning(f"Failed to load as WebM: {webm_error}")
                    try:
                        # Try without format specification
                        audio = AudioSegment.from_file(temp_file_path)
                    except Exception as general_error:
                        logging.warning(f"Failed general audio load: {general_error}")
                        # Fallback: Use the original file directly if it's valid
                        # Some browsers send different formats than expected
                        try:
                            # Test if the file can be opened by OpenAI directly
                            with open(temp_file_path, "rb") as test_file:
                                client = openai.OpenAI(api_key=self.api_key)
                                # Try direct transcription without conversion
                                transcript = client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=test_file,
                                    language=language if language else None,
                                    response_format="verbose_json"
                                )
                                
                                # Clean up
                                os.unlink(temp_file_path)
                                
                                return {
                                    "success": True,
                                    "text": transcript.text,
                                    "language": transcript.language,
                                    "duration": getattr(transcript, 'duration', 0),
                                    "words": getattr(transcript, 'words', []),
                                    "confidence": getattr(transcript, 'avg_logprob', None)
                                }
                        except Exception as direct_error:
                            logging.error(f"Direct transcription failed: {direct_error}")
                            raise HTTPException(status_code=400, detail="Invalid audio format. Please try recording again.")
                
                # If we got here, audio conversion worked
                # Convert to wav for better compatibility
                audio.export(wav_path, format="wav")
                
                # Transcribe with OpenAI Whisper
                client = openai.OpenAI(api_key=self.api_key)
                
                with open(wav_path, "rb") as audio_file_obj:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file_obj,
                        language=language if language else None,  # Auto-detect if not specified
                        response_format="verbose_json",
                        timestamp_granularities=["word"]
                    )
                
                # Clean up temporary files
                os.unlink(temp_file_path)
                os.unlink(wav_path)
                
                return {
                    "success": True,
                    "text": transcript.text,
                    "language": transcript.language,
                    "duration": transcript.duration,
                    "words": getattr(transcript, 'words', []),
                    "confidence": getattr(transcript, 'avg_logprob', None)
                }
                
            except Exception as e:
                # Clean up temp file on error
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                if 'wav_path' in locals() and os.path.exists(wav_path):
                    os.unlink(wav_path)
                raise e
                
        except Exception as e:
            logging.error(f"Error transcribing audio: {e}")
            raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages for Whisper"""
        return [
            {"code": "af", "name": "Afrikaans"},
            {"code": "am", "name": "Amharic"},
            {"code": "ar", "name": "Arabic"},
            {"code": "as", "name": "Assamese"},
            {"code": "az", "name": "Azerbaijani"},
            {"code": "ba", "name": "Bashkir"},
            {"code": "be", "name": "Belarusian"},
            {"code": "bg", "name": "Bulgarian"},
            {"code": "bn", "name": "Bengali"},
            {"code": "bo", "name": "Tibetan"},
            {"code": "br", "name": "Breton"},
            {"code": "bs", "name": "Bosnian"},
            {"code": "ca", "name": "Catalan"},
            {"code": "cs", "name": "Czech"},
            {"code": "cy", "name": "Welsh"},
            {"code": "da", "name": "Danish"},
            {"code": "de", "name": "German"},
            {"code": "el", "name": "Greek"},
            {"code": "en", "name": "English"},
            {"code": "es", "name": "Spanish"},
            {"code": "et", "name": "Estonian"},
            {"code": "eu", "name": "Basque"},
            {"code": "fa", "name": "Persian"},
            {"code": "fi", "name": "Finnish"},
            {"code": "fo", "name": "Faroese"},
            {"code": "fr", "name": "French"},
            {"code": "gl", "name": "Galician"},
            {"code": "gu", "name": "Gujarati"},
            {"code": "ha", "name": "Hausa"},
            {"code": "haw", "name": "Hawaiian"},
            {"code": "he", "name": "Hebrew"},
            {"code": "hi", "name": "Hindi"},
            {"code": "hr", "name": "Croatian"},  # ✅ Croatian support!
            {"code": "ht", "name": "Haitian Creole"},
            {"code": "hu", "name": "Hungarian"},
            {"code": "hy", "name": "Armenian"},
            {"code": "id", "name": "Indonesian"},
            {"code": "is", "name": "Icelandic"},
            {"code": "it", "name": "Italian"},
            {"code": "ja", "name": "Japanese"},
            {"code": "jw", "name": "Javanese"},
            {"code": "ka", "name": "Georgian"},
            {"code": "kk", "name": "Kazakh"},
            {"code": "km", "name": "Khmer"},
            {"code": "kn", "name": "Kannada"},
            {"code": "ko", "name": "Korean"},
            {"code": "la", "name": "Latin"},
            {"code": "lb", "name": "Luxembourgish"},
            {"code": "ln", "name": "Lingala"},
            {"code": "lo", "name": "Lao"},
            {"code": "lt", "name": "Lithuanian"},
            {"code": "lv", "name": "Latvian"},
            {"code": "mg", "name": "Malagasy"},
            {"code": "mi", "name": "Maori"},
            {"code": "mk", "name": "Macedonian"},
            {"code": "ml", "name": "Malayalam"},
            {"code": "mn", "name": "Mongolian"},
            {"code": "mr", "name": "Marathi"},
            {"code": "ms", "name": "Malay"},
            {"code": "mt", "name": "Maltese"},
            {"code": "my", "name": "Myanmar"},
            {"code": "ne", "name": "Nepali"},
            {"code": "nl", "name": "Dutch"},
            {"code": "nn", "name": "Nynorsk"},
            {"code": "no", "name": "Norwegian"},
            {"code": "oc", "name": "Occitan"},
            {"code": "pa", "name": "Punjabi"},
            {"code": "pl", "name": "Polish"},
            {"code": "ps", "name": "Pashto"},
            {"code": "pt", "name": "Portuguese"},
            {"code": "ro", "name": "Romanian"},
            {"code": "ru", "name": "Russian"},
            {"code": "sa", "name": "Sanskrit"},
            {"code": "sd", "name": "Sindhi"},
            {"code": "si", "name": "Sinhala"},
            {"code": "sk", "name": "Slovak"},
            {"code": "sl", "name": "Slovenian"},
            {"code": "sn", "name": "Shona"},
            {"code": "so", "name": "Somali"},
            {"code": "sq", "name": "Albanian"},
            {"code": "sr", "name": "Serbian"},
            {"code": "su", "name": "Sundanese"},
            {"code": "sv", "name": "Swedish"},
            {"code": "sw", "name": "Swahili"},
            {"code": "ta", "name": "Tamil"},
            {"code": "te", "name": "Telugu"},
            {"code": "tg", "name": "Tajik"},
            {"code": "th", "name": "Thai"},
            {"code": "tk", "name": "Turkmen"},
            {"code": "tl", "name": "Tagalog"},
            {"code": "tr", "name": "Turkish"},
            {"code": "tt", "name": "Tatar"},
            {"code": "uk", "name": "Ukrainian"},
            {"code": "ur", "name": "Urdu"},
            {"code": "uz", "name": "Uzbek"},
            {"code": "vi", "name": "Vietnamese"},
            {"code": "yi", "name": "Yiddish"},
            {"code": "yo", "name": "Yoruba"},
            {"code": "zh", "name": "Chinese"}
        ]

# Initialize Whisper service
whisper_service = WhisperService()

# Authentication Functions
def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def verify_google_token(token: str) -> dict:
    """Verify Google OAuth token and extract user info"""
    try:
        # Verify the token with Google
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
            
        return {
            'google_id': idinfo['sub'],
            'email': idinfo['email'],
            'name': idinfo['name'],
            'picture': idinfo.get('picture', '')
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid token: {str(e)}")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Try to get user_id first (for email/password auth), then fallback to sub (for Google auth)
        user_id = payload.get("user_id")
        user_email = payload.get("sub")
        
        if not user_id and not user_email:
            raise HTTPException(status_code=401, detail="Invalid token: missing user identification")
            
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    # Try to find user by ID first, then by email
    user = None
    if user_id:
        user = await db.users.find_one({"id": user_id})
    
    if not user and user_email:
        user = await db.users.find_one({"email": user_email})
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user)

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[User]:
    """Get current user from JWT token, return None if not authenticated"""
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

# Admin helper functions
def is_admin_user(user_email: str) -> bool:
    """Check if user is an admin"""
    return user_email.lower() == ADMIN_EMAIL.lower()

async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user and verify admin privileges"""
    user = await get_current_user(credentials)
    if not is_admin_user(user.email):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# API Routes

# Authentication Endpoints
@api_router.post("/auth/google", response_model=TokenResponse)
async def google_auth(auth_request: GoogleAuthRequest):
    """Authenticate with Google OAuth"""
    try:
        # Verify Google token and get user info
        google_user = await verify_google_token(auth_request.credential)
        
        # Check if user exists
        existing_user = await db.users.find_one({"google_id": google_user['google_id']})
        
        if existing_user:
            # Update last login
            await db.users.update_one(
                {"id": existing_user["id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            user = User(**existing_user)
        else:
            # Create new user
            user = User(
                email=google_user['email'],
                name=google_user['name'],
                picture=google_user['picture'],
                google_id=google_user['google_id']
            )
            await db.users.insert_one(user.dict())
        
        # Create JWT token
        token_data = {"sub": user.id}
        access_token = create_access_token(data=token_data)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(**user.dict())
        )
        
    except Exception as e:
        logging.error(f"Google auth error: {e}")
        raise HTTPException(status_code=400, detail="Invalid Google token")

class GoogleOAuthCallbackRequest(BaseModel):
    code: str
    redirect_uri: str

@api_router.post("/auth/google/callback", response_model=TokenResponse)
async def google_oauth_callback(callback_request: GoogleOAuthCallbackRequest):
    """Handle Google OAuth callback"""
    try:
        # Exchange authorization code for tokens
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "code": callback_request.code,
                    "grant_type": "authorization_code",
                    "redirect_uri": callback_request.redirect_uri,
                }
            )
            
            if token_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
            
            tokens = token_response.json()
            
            # Get user info from Google
            user_info_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"}
            )
            
            if user_info_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get user info")
            
            user_info = user_info_response.json()
            
            # Check if user exists
            existing_user = await db.users.find_one({"google_id": user_info['id']})
            
            if existing_user:
                # Update last login
                await db.users.update_one(
                    {"id": existing_user["id"]},
                    {"$set": {"last_login": datetime.utcnow()}}
                )
                user = User(**existing_user)
            else:
                # Create new user
                user = User(
                    email=user_info['email'],
                    name=user_info['name'],
                    picture=user_info.get('picture', ''),
                    google_id=user_info['id']
                )
                await db.users.insert_one(user.dict())
            
            # Create JWT token
            token_data = {"sub": user.id}
            access_token = create_access_token(data=token_data)
            
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user=UserResponse(**user.dict())
            )
            
    except Exception as e:
        logging.error(f"Google OAuth callback error: {e}")
        raise HTTPException(status_code=400, detail="OAuth authentication failed")

@api_router.post("/auth/test-login", response_model=TokenResponse)
async def test_login():
    """Test login endpoint for development (creates a test user)"""
    try:
        # Create or get test user
        test_user_data = {
            "id": "test-user-123",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://via.placeholder.com/40",
            "google_id": "test-google-id-123",
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow(),
            "is_active": True
        }
        
        # Check if test user exists
        existing_user = await db.users.find_one({"id": "test-user-123"})
        
        if existing_user:
            # Update last login
            await db.users.update_one(
                {"id": "test-user-123"},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            user = User(**existing_user)
        else:
            # Create test user
            user = User(**test_user_data)
            await db.users.insert_one(user.dict())
        
        # Create JWT token
        access_token = create_access_token(data={"sub": user.id})
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(**user.dict())
        )
        
    except Exception as e:
        logging.error(f"Test login error: {e}")
        raise HTTPException(status_code=500, detail="Test login failed")

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse(**current_user.dict())

@api_router.post("/auth/logout")
async def logout():
    """Logout user (client should delete token)"""
    return {"message": "Logged out successfully"}

# Email/Password Authentication Endpoints
@api_router.post("/auth/register", response_model=TokenResponse)
async def register_user(user_data: UserRegister):
    """Register a new user with email and password"""
    try:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Hash the password
        password_hash = hash_password(user_data.password)
        
        # Create new user
        new_user = UserWithPassword(
            email=user_data.email,
            name=user_data.name,
            password_hash=password_hash,
            auth_type="email",
            picture="",  # Default empty picture for email users
            google_id=""  # Not applicable for email users
        )
        
        # Insert user into database
        user_dict = new_user.dict()
        await db.users.insert_one(user_dict)
        
        # Create access token
        access_token = create_access_token(data={"sub": new_user.email, "user_id": new_user.id})
        
        # Prepare user response (exclude password_hash)
        user_response = UserResponse(
            id=new_user.id,
            email=new_user.email,
            name=new_user.name,
            picture=new_user.picture,
            created_at=new_user.created_at,
            last_login=new_user.last_login
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@api_router.post("/auth/login", response_model=TokenResponse)
async def login_user(user_credentials: UserLogin):
    """Login user with email and password"""
    try:
        # Find user by email
        user_doc = await db.users.find_one({"email": user_credentials.email})
        if not user_doc:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Check if user has a password (email auth user)
        if not user_doc.get("password_hash"):
            raise HTTPException(
                status_code=401,
                detail="This email is registered with Google. Please use Google sign-in."
            )
        
        # Verify password
        if not verify_password(user_credentials.password, user_doc["password_hash"]):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user_doc.get("is_active", True):
            raise HTTPException(
                status_code=401,
                detail="Account is deactivated"
            )
        
        # Update last login
        await db.users.update_one(
            {"_id": user_doc["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user_doc["email"], "user_id": user_doc["id"]}
        )
        
        # Prepare user response
        user_response = UserResponse(
            id=user_doc["id"],
            email=user_doc["email"],
            name=user_doc["name"],
            picture=user_doc.get("picture", ""),
            created_at=user_doc["created_at"],
            last_login=user_doc["last_login"]
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error logging in user: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

# Admin Dashboard Endpoints
@api_router.get("/admin/dashboard/stats")
async def get_admin_dashboard_stats(current_user: User = Depends(get_admin_user)):
    """Get comprehensive dashboard statistics for admin"""
    try:
        # Get total user count
        total_users = await db.users.count_documents({})
        
        # Get user registrations in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_users = await db.users.count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })
        
        # Get total conversations
        total_conversations = await db.conversations.count_documents({})
        
        # Get total documents
        total_documents = await db.documents.count_documents({})
        
        # Get total agents created
        total_agents = await db.agents.count_documents({})
        
        # Get total saved agents
        total_saved_agents = await db.saved_agents.count_documents({})
        
        # Get active users (those who logged in in last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        active_users = await db.users.count_documents({
            "last_login": {"$gte": seven_days_ago}
        })
        
        return {
            "overview": {
                "total_users": total_users,
                "recent_users": recent_users,
                "active_users": active_users,
                "total_conversations": total_conversations,
                "total_documents": total_documents,
                "total_agents": total_agents,
                "total_saved_agents": total_saved_agents
            }
        }
        
    except Exception as e:
        logging.error(f"Error getting admin dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")

@api_router.get("/admin/users")
async def get_admin_users(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_admin_user)
):
    """Get list of all users with their activity data"""
    try:
        # Get users with pagination
        users = await db.users.find({}).skip(offset).limit(limit).sort("created_at", -1).to_list(limit)
        
        # Get activity data for each user
        user_data = []
        for user in users:
            user_id = user.get("id")
            
            # Count user's documents
            doc_count = await db.documents.count_documents({"metadata.user_id": user_id})
            
            # Count user's saved agents
            agent_count = await db.saved_agents.count_documents({"user_id": user_id})
            
            # Count user's conversations (approximate based on agents they created)
            conversation_count = await db.conversations.count_documents({
                "participants": {"$elemMatch": {"$regex": f".*{user_id}.*"}}
            })
            
            user_info = {
                "id": user_id,
                "email": user["email"],
                "name": user["name"],
                "created_at": user["created_at"],
                "last_login": user.get("last_login", user["created_at"]),
                "auth_type": user.get("auth_type", "google"),
                "is_active": user.get("is_active", True),
                "stats": {
                    "documents": doc_count,
                    "saved_agents": agent_count,
                    "conversations": conversation_count
                }
            }
            user_data.append(user_info)
        
        return {
            "users": user_data,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(user_data)
            }
        }
        
    except Exception as e:
        logging.error(f"Error getting admin users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")

@api_router.get("/admin/user/{user_id}/details")
async def get_admin_user_details(
    user_id: str,
    current_user: User = Depends(get_admin_user)
):
    """Get detailed information about a specific user"""
    try:
        # Get user basic info
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's documents
        documents = await db.documents.find(
            {"metadata.user_id": user_id}
        ).sort("metadata.created_at", -1).limit(10).to_list(10)
        
        # Get user's saved agents
        saved_agents = await db.saved_agents.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(10).to_list(10)
        
        # Get recent activity (simplified)
        recent_documents = len(documents)
        recent_agents = len(saved_agents)
        
        return {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "created_at": user["created_at"],
                "last_login": user.get("last_login", user["created_at"]),
                "auth_type": user.get("auth_type", "google"),
                "is_active": user.get("is_active", True)
            },
            "activity": {
                "recent_documents": recent_documents,
                "recent_agents": recent_agents,
                "total_documents": await db.documents.count_documents({"metadata.user_id": user_id}),
                "total_saved_agents": await db.saved_agents.count_documents({"user_id": user_id})
            },
            "recent_documents": [
                {
                    "id": doc["id"],
                    "title": doc["metadata"]["title"],
                    "category": doc["metadata"]["category"],
                    "created_at": doc["metadata"]["created_at"]
                } for doc in documents
            ],
            "recent_agents": [
                {
                    "id": agent["id"],
                    "name": agent["name"],
                    "archetype": agent["archetype"],
                    "created_at": agent["created_at"]
                } for agent in saved_agents
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting user details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user details: {str(e)}")

@api_router.get("/admin/activity/recent")
async def get_admin_recent_activity(
    hours: int = 24,
    current_user: User = Depends(get_admin_user)
):
    """Get recent activity across the platform"""
    try:
        since_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get recent user registrations
        recent_users = await db.users.find({
            "created_at": {"$gte": since_time}
        }).sort("created_at", -1).to_list(50)
        
        # Get recent documents
        recent_documents = await db.documents.find({
            "metadata.created_at": {"$gte": since_time}
        }).sort("metadata.created_at", -1).to_list(50)
        
        # Get recent saved agents
        recent_agents = await db.saved_agents.find({
            "created_at": {"$gte": since_time}
        }).sort("created_at", -1).to_list(50)
        
        return {
            "recent_users": [
                {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"],
                    "created_at": user["created_at"],
                    "auth_type": user.get("auth_type", "google")
                } for user in recent_users
            ],
            "recent_documents": [
                {
                    "id": doc["id"],
                    "title": doc["metadata"]["title"],
                    "category": doc["metadata"]["category"],
                    "user_id": doc["metadata"]["user_id"],
                    "created_at": doc["metadata"]["created_at"]
                } for doc in recent_documents
            ],
            "recent_agents": [
                {
                    "id": agent["id"],
                    "name": agent["name"],
                    "archetype": agent["archetype"],
                    "user_id": agent["user_id"],
                    "created_at": agent["created_at"]
                } for agent in recent_agents
            ]
        }
        
    except Exception as e:
        logging.error(f"Error getting recent activity: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recent activity: {str(e)}")

@api_router.post("/admin/reset-password")
async def reset_admin_password(
    request_data: dict,
    current_user: User = Depends(get_admin_user)
):
    """Reset admin password - admin only"""
    try:
        new_password = request_data.get("new_password")
        if not new_password or len(new_password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        # Hash the new password
        password_hash = hash_password(new_password)
        
        # Update admin user's password
        result = await db.users.update_one(
            {"email": ADMIN_EMAIL},
            {"$set": {"password_hash": password_hash}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Admin user not found")
        
        return {"message": "Admin password updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error resetting admin password: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset password: {str(e)}")

@api_router.post("/admin/setup")
async def setup_admin_account(setup_data: dict):
    """One-time setup for admin account - no authentication required"""
    try:
        # Check if admin already exists and has a password
        admin_user = await db.users.find_one({"email": ADMIN_EMAIL})
        
        if admin_user and admin_user.get("password_hash"):
            raise HTTPException(status_code=400, detail="Admin account already set up")
        
        password = setup_data.get("password")
        if not password or len(password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        # Hash the password
        password_hash = hash_password(password)
        
        if admin_user:
            # Update existing admin with password
            await db.users.update_one(
                {"email": ADMIN_EMAIL},
                {"$set": {
                    "password_hash": password_hash,
                    "auth_type": "email"
                }}
            )
        else:
            # Create new admin user
            admin_user = UserWithPassword(
                email=ADMIN_EMAIL,
                name="Admin",
                password_hash=password_hash,
                auth_type="email",
                picture="",
                google_id=""
            )
            await db.users.insert_one(admin_user.dict())
        
        return {"message": "Admin account set up successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error setting up admin account: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set up admin account: {str(e)}")

# Saved Agents Endpoints
@api_router.get("/saved-agents", response_model=List[SavedAgent])
async def get_saved_agents(current_user: User = Depends(get_current_user)):
    """Get user's saved agents"""
    agents = await db.saved_agents.find({"user_id": current_user.id}).sort("created_at", -1).to_list(100)
    return [SavedAgent(**agent) for agent in agents]

@api_router.post("/saved-agents", response_model=SavedAgent)
async def create_saved_agent(agent_data: SavedAgentCreate, current_user: User = Depends(get_current_user)):
    """Save an agent to user's library"""
    # Use default personality if not provided
    if not agent_data.personality:
        if agent_data.archetype in AGENT_ARCHETYPES:
            default_traits = AGENT_ARCHETYPES[agent_data.archetype]["default_traits"]
            agent_data.personality = AgentPersonality(**default_traits)
        else:
            raise HTTPException(status_code=400, detail="Invalid archetype")
    
    saved_agent = SavedAgent(
        user_id=current_user.id,
        **agent_data.dict()
    )
    
    await db.saved_agents.insert_one(saved_agent.dict())
    return saved_agent

@api_router.delete("/saved-agents/{agent_id}")
async def delete_saved_agent(agent_id: str, current_user: User = Depends(get_current_user)):
    """Delete a saved agent"""
    result = await db.saved_agents.delete_one({"id": agent_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": "Agent deleted successfully"}

# Conversation History Endpoints
@api_router.get("/conversation-history", response_model=List[ConversationHistory])
async def get_conversation_history(current_user: User = Depends(get_current_user)):
    """Get user's conversation history"""
    conversations = await db.conversation_history.find({"user_id": current_user.id}).sort("created_at", -1).to_list(100)
    return [ConversationHistory(**conv) for conv in conversations]

@api_router.post("/conversation-history")
async def save_conversation(conversation_data: dict, current_user: User = Depends(get_current_user)):
    """Save a conversation to history"""
    conversation = ConversationHistory(
        user_id=current_user.id,
        **conversation_data
    )
    await db.conversation_history.insert_one(conversation.dict())
    return {"message": "Conversation saved successfully"}
@api_router.get("/")
async def root():
    return {"message": "AI Agent Simulation API"}

@api_router.post("/simulation/set-scenario")
async def set_scenario(request: ScenarioRequest):
    """Set a custom scenario for the simulation"""
    scenario = request.scenario.strip()
    scenario_name = request.scenario_name.strip()
    
    if not scenario:
        raise HTTPException(status_code=400, detail="Scenario text required")
    if not scenario_name:
        raise HTTPException(status_code=400, detail="Scenario name required")
    
    # Update simulation state with new scenario and name
    await db.simulation_state.update_one(
        {},
        {"$set": {
            "scenario": scenario,
            "scenario_name": scenario_name
        }},
        upsert=True
    )
    
    return {"message": "Scenario updated", "scenario": scenario, "scenario_name": scenario_name}

@api_router.post("/simulation/pause")
async def pause_simulation():
    """Pause the simulation (stops auto-generation)"""
    await db.simulation_state.update_one(
        {},
        {"$set": {
            "is_active": False,
            "auto_conversations": False,
            "auto_time": False
        }},
        upsert=True
    )
    return {"message": "Simulation paused", "is_active": False}

@api_router.post("/simulation/resume")
async def resume_simulation():
    """Resume the simulation"""
    await db.simulation_state.update_one(
        {},
        {"$set": {"is_active": True}},
        upsert=True
    )
    return {"message": "Simulation resumed", "is_active": True}

@api_router.post("/simulation/generate-summary")
async def generate_weekly_summary():
    """Generate structured AI summary of conversations with focus on key discoveries and documents created"""
    # Get all conversations
    conversations = await db.conversations.find().sort("created_at", -1).to_list(100)
    
    if not conversations:
        return {"summary": "No conversations to summarize yet."}
    
    # Get current simulation state
    state = await db.simulation_state.find_one()
    current_day = state.get("current_day", 1) if state else 1
    
    # Filter conversations from recent days (last 7 days or all if less than 7)
    recent_conversations = conversations[:min(21, len(conversations))]  # Last 21 rounds (7 days * 3 periods)
    
    if not recent_conversations:
        return {"summary": "No recent conversations to summarize."}
    
    # Get documents created during this period
    try:
        # Get documents created in the last week
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        recent_documents = await db.documents.find({
            "metadata.created_at": {"$gte": one_week_ago.isoformat()}
        }).sort("metadata.created_at", -1).to_list(50)
    except Exception as e:
        logging.warning(f"Could not fetch recent documents: {e}")
        recent_documents = []
    
    # Check API usage
    if not await llm_manager.can_make_request():
        return {"summary": "Cannot generate summary - daily API limit reached"}
    
    # Prepare conversation text for summary
    conv_text = ""
    key_decisions = []
    agent_interactions = []
    document_summary = ""
    
    for conv in recent_conversations:
        conv_text += f"\n**{conv['time_period']}:**\n"
        for msg in conv.get('messages', []):
            conv_text += f"- **{msg['agent_name']}**: {msg['message']}\n"
            # Track significant statements for key events
            if any(keyword in msg['message'].lower() for keyword in ['decide', 'discovery', 'found', 'breakthrough', 'crisis', 'solution', 'agreement', 'conflict', 'document created', 'protocol', 'training']):
                key_decisions.append(f"{msg['agent_name']}: {msg['message']}")
    
    # Prepare document summary
    if recent_documents:
        document_summary = "\n\n**DOCUMENTS CREATED THIS WEEK:**\n"
        for doc in recent_documents:
            metadata = doc.get('metadata', {})
            document_summary += f"- **{metadata.get('title', 'Untitled')}** ({metadata.get('category', 'Unknown')})\n"
            document_summary += f"  - Created by: {', '.join(metadata.get('authors', ['Unknown']))}\n"
            document_summary += f"  - Description: {metadata.get('description', 'No description')}\n"
            # Add document content preview
            content_preview = doc.get('content', '')[:200]
            if len(content_preview) > 0:
                document_summary += f"  - Preview: {content_preview}{'...' if len(doc.get('content', '')) > 200 else ''}\n"
            document_summary += "\n"
    
    # Generate structured summary using LLM
    chat = LlmChat(
        api_key=llm_manager.api_key,
        session_id=f"weekly_summary_{datetime.now().timestamp()}",
        system_message="""You are analyzing AI agent interactions to create a structured weekly report. 
        Focus on concrete discoveries, decisions, breakthroughs, significant developments, and documents created.
        
        Create a comprehensive report with these sections:
        1. EXECUTIVE SUMMARY (2-3 sentences highlighting the most important developments)
        2. KEY EVENTS & DISCOVERIES (main focus - most important developments, decisions, breakthroughs)
        3. DOCUMENTS & DELIVERABLES (focus on documents created, their purpose, and impact)
        4. RELATIONSHIP DEVELOPMENTS (how agent relationships changed)
        5. EMERGING PERSONALITIES (how each agent's personality manifested)
        6. SOCIAL DYNAMICS (team cohesion, leadership patterns, conflicts)
        7. STRATEGIC DECISIONS (important choices made by the team)
        8. ACTION-ORIENTED OUTCOMES (tangible results and deliverables produced)
        9. LOOKING AHEAD (predictions for future developments)
        
        Use **bold** for section headers and important points. Be specific and actionable.
        Pay special attention to the documents created and their strategic value."""
    ).with_model("gemini", "gemini-2.0-flash")
    
    prompt = f"""Analyze these AI agent conversations from the Research Station simulation:

{conv_text}

{document_summary}

Provide a comprehensive weekly summary in this format:
**Week Summary - Day {current_day}**

**📊 EXECUTIVE SUMMARY**
[2-3 sentences highlighting the most significant developments, breakthroughs, and documents created this week]

**🔥 KEY EVENTS & DISCOVERIES**

1. [First major event or discovery - detailed paragraph with specific examples]

2. [Second major event or discovery - detailed paragraph with specific examples]

3. [Third major event or discovery - detailed paragraph with specific examples]

**📋 DOCUMENTS & DELIVERABLES**

1. [First document created - title, purpose, impact, and why it was needed]

2. [Second document created - title, purpose, impact, and strategic value]

3. [Third document created - title, purpose, impact, and implementation potential]

**📈 RELATIONSHIP DEVELOPMENTS**

1. [First relationship change or development - detailed paragraph]

2. [Second relationship change or development - detailed paragraph]

3. [Third relationship change or development - detailed paragraph]

**🎭 EMERGING PERSONALITIES**

1. [First agent's personality development - detailed paragraph]

2. [Second agent's personality development - detailed paragraph]

3. [Third agent's personality development - detailed paragraph]

**🤝 SOCIAL DYNAMICS**

1. [First social pattern or team dynamic - detailed paragraph]

2. [Second social pattern or team dynamic - detailed paragraph]

**⚡ ACTION-ORIENTED OUTCOMES**

1. [First tangible result or deliverable produced by the team]

2. [Second concrete achievement or implementation]

3. [Third measurable outcome or progress]

**🔮 LOOKING AHEAD**

1. [First prediction for future developments - detailed paragraph]

2. [Second prediction for future developments - detailed paragraph]

3. [Third prediction for future developments - detailed paragraph]

IMPORTANT FORMATTING RULES:
- Leave an empty line between each numbered paragraph for readability
- Use **bold formatting** sparingly for only the most significant key terms (2-3 words max per paragraph)
- Bold only words with critical meaning to the context (agent names, breakthrough discoveries, major decisions, turning points)
- Do NOT bold common words like "team", "discussion", "conversation", "development"
- Make each numbered point a complete, detailed paragraph with specific examples from the conversations
- Focus on concrete events and behaviors rather than generic observations"""
    
    try:
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        await llm_manager.increment_usage()
        
        # Store structured summary in database
        summary_doc = {
            "id": str(uuid.uuid4()),
            "summary": response,
            "day_generated": current_day,
            "conversations_analyzed": len(recent_conversations),
            "report_type": "weekly_structured",
            "created_at": datetime.utcnow()
        }
        await db.summaries.insert_one(summary_doc)
        
        # Update last auto report timestamp
        await db.simulation_state.update_one(
            {},
            {"$set": {"last_auto_report": datetime.utcnow().isoformat()}},
            upsert=True
        )
        
        return {
            "summary": response, 
            "day": current_day, 
            "conversations_count": len(recent_conversations),
            "report_type": "weekly_structured"
        }
        
    except Exception as e:
        logging.error(f"Error generating summary: {e}")
        
        # Create a fallback summary when API fails
        fallback_summary = f"""**Week Summary - Day {current_day}**

**1. 🔥 KEY EVENTS & DISCOVERIES**
- {len(recent_conversations)} conversations analyzed from recent simulation periods
- Team dynamics continue to evolve between {len(set([msg['agent_name'] for conv in recent_conversations for msg in conv.get('messages', [])]))} active agents

**2. 📈 RELATIONSHIP DEVELOPMENTS**
- Ongoing interactions between team members showing personality-driven responses
- Relationship patterns emerging based on agent archetypes and conversation contexts

**3. 🎭 EMERGING PERSONALITIES**
- Each agent continues to demonstrate their unique archetype characteristics
- Personality traits influencing conversation styles and decision-making approaches

**4. 🤝 SOCIAL DYNAMICS**
- Team coordination and communication patterns developing
- Individual agent strengths contributing to group discussions

**5. 🔮 LOOKING AHEAD**
- Continued monitoring of agent interactions and relationship evolution
- Further development of personality-based conversation patterns

*Note: This summary was generated using conversation analysis due to AI service limitations. For detailed AI-generated insights, please try again later when API quota is available.*"""

        # Store fallback summary in database
        fallback_doc = {
            "id": str(uuid.uuid4()),
            "summary": fallback_summary,
            "day_generated": current_day,
            "conversations_analyzed": len(recent_conversations),
            "created_at": datetime.utcnow(),
            "is_fallback": True,
            "report_type": "weekly_structured"
        }
        await db.summaries.insert_one(fallback_doc)
        
        return {
            "summary": fallback_summary, 
            "day": current_day, 
            "conversations_count": len(recent_conversations),
            "report_type": "weekly_structured",
            "note": "Fallback summary generated due to API limitations"
        }

@api_router.get("/archetypes")
async def get_archetypes():
    """Get all available agent archetypes"""
    return AGENT_ARCHETYPES

@api_router.post("/agents", response_model=Agent)
async def create_agent(agent_data: AgentCreate):
    """Create a new AI agent with avatar generation for simulation"""
    # Use default personality if not provided
    if not agent_data.personality:
        if agent_data.archetype in AGENT_ARCHETYPES:
            default_traits = AGENT_ARCHETYPES[agent_data.archetype]["default_traits"]
            agent_data.personality = AgentPersonality(**default_traits)
        else:
            raise HTTPException(status_code=400, detail="Invalid archetype")
    
    # Use existing avatar URL if provided, otherwise generate new one
    avatar_url = agent_data.avatar_url  # Use preview image if available
    
    if not avatar_url and agent_data.avatar_prompt:
        try:
            # Enhanced prompt for better avatar results
            enhanced_prompt = f"professional portrait, headshot, detailed face, {agent_data.avatar_prompt}, high quality, photorealistic, studio lighting, neutral background"
            
            # Submit to fal.ai using the Flux Schnell model (fastest and cheapest)
            handler = await fal_client.submit_async(
                "fal-ai/flux/schnell",
                arguments={
                    "prompt": enhanced_prompt,
                    "image_size": "portrait_4_3",  # Good for avatars
                    "num_images": 1,
                    "enable_safety_checker": True
                }
            )
            
            # Get the result
            result = await handler.get()
            
            if result and result.get("images") and len(result["images"]) > 0:
                avatar_url = result["images"][0]["url"]
                logging.info(f"Avatar generated successfully for {agent_data.name}")
            else:
                logging.warning(f"No avatar generated for {agent_data.name}")
                
        except Exception as e:
            logging.error(f"Avatar generation error for {agent_data.name}: {e}")
            # Continue without avatar if generation fails
    
    agent = Agent(
        name=agent_data.name,
        archetype=agent_data.archetype,
        personality=agent_data.personality,
        goal=agent_data.goal,
        expertise=agent_data.expertise,
        background=agent_data.background,
        memory_summary=agent_data.memory_summary,
        avatar_url=avatar_url,
        avatar_prompt=agent_data.avatar_prompt,
        user_id=""  # No user association for simulation
    )
    
    await db.agents.insert_one(agent.dict())
    return agent

@api_router.get("/agents", response_model=List[Agent])
async def get_agents():
    """Get all agents for simulation"""
    agents = await db.agents.find().to_list(100)
    return [Agent(**agent) for agent in agents]

@api_router.put("/agents/{agent_id}")
async def update_agent(agent_id: str, agent_update: AgentUpdate):
    """Update an existing agent"""
    # Find the agent
    agent = await db.agents.find_one({"id": agent_id})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Prepare update data
    update_data = {}
    if agent_update.name is not None:
        update_data["name"] = agent_update.name
    if agent_update.archetype is not None:
        if agent_update.archetype not in AGENT_ARCHETYPES:
            raise HTTPException(status_code=400, detail="Invalid archetype")
        update_data["archetype"] = agent_update.archetype
    if agent_update.personality is not None:
        update_data["personality"] = agent_update.personality.dict()
    if agent_update.goal is not None:
        update_data["goal"] = agent_update.goal
    if agent_update.expertise is not None:
        update_data["expertise"] = agent_update.expertise
    if agent_update.background is not None:
        update_data["background"] = agent_update.background
    if agent_update.memory_summary is not None:
        # Process URLs in memory before storing
        processed_memory = await llm_manager.process_memory_with_urls(agent_update.memory_summary)
        update_data["memory_summary"] = processed_memory
    if agent_update.avatar_url is not None:
        update_data["avatar_url"] = agent_update.avatar_url
    
    # Update the agent
    await db.agents.update_one(
        {"id": agent_id},
        {"$set": update_data}
    )
    
    # Return updated agent
    updated_agent = await db.agents.find_one({"id": agent_id})
    return Agent(**updated_agent)

@api_router.post("/simulation/fast-forward")
async def fast_forward_simulation(request: FastForwardRequest):
    """Fast forward the simulation by generating multiple days of conversations"""
    # Get current simulation state
    state = await db.simulation_state.find_one()
    if not state or not state.get("is_active"):
        raise HTTPException(status_code=400, detail="Simulation not active")
    
    # Get agents
    agents = await db.agents.find().to_list(100)
    if len(agents) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 agents")
    
    agent_objects = [Agent(**agent) for agent in agents]
    
    current_day = state.get("current_day", 1)
    current_period = state.get("current_time_period", "morning")
    scenario = state.get("scenario", "Research Station")
    
    periods = ["morning", "afternoon", "evening"]
    generated_conversations = []
    
    # Check if we have enough API requests
    usage = await llm_manager.get_usage_today()
    estimated_requests = request.target_days * 3 * request.conversations_per_period * len(agent_objects)
    if usage + estimated_requests > llm_manager.max_daily_requests:
        raise HTTPException(status_code=400, detail=f"Not enough API requests remaining. Need {estimated_requests}, have {llm_manager.max_daily_requests - usage}")
    
    try:
        for day_offset in range(request.target_days):
            target_day = current_day + day_offset
            
            for period in periods:
                # Skip periods we've already passed today
                if day_offset == 0:
                    current_period_index = periods.index(current_period)
                    period_index = periods.index(period)
                    if period_index <= current_period_index:
                        continue
                
                # Generate conversations for this period
                for conv_num in range(request.conversations_per_period):
                    # Get conversation history for context
                    conversation_history = await db.conversations.find().sort("created_at", -1).limit(10).to_list(10)
                    
                    # Create progressive context based on day and time
                    day_context = f"Day {target_day}, {period}. "
                    if target_day > current_day:
                        day_context += f"Several days have passed. "
                    
                    if period == "morning":
                        day_context += "Starting a new day with fresh energy. "
                    elif period == "afternoon":
                        day_context += "Midday progress check and developments. "
                    else:
                        day_context += "Evening reflection and planning. "
                    
                    # Add progression context
                    if conversation_history:
                        day_context += "Build upon previous discussions and introduce new developments. "
                    
                    # Generate responses from each agent
                    messages = []
                    for agent in agent_objects:
                        response = await llm_manager.generate_agent_response(
                            agent, scenario, agent_objects, day_context, conversation_history
                        )
                        
                        message = ConversationMessage(
                            agent_id=agent.id,
                            agent_name=agent.name,
                            message=response,
                            mood=agent.current_mood
                        )
                        messages.append(message)
                    
                    # Create conversation round
                    conversation_count = await db.conversations.count_documents({})
                    conversation_round = ConversationRound(
                        round_number=conversation_count + 1,
                        time_period=f"Day {target_day} - {period} (#{conv_num + 1})",
                        scenario=scenario,
                        messages=messages
                    )
                    
                    await db.conversations.insert_one(conversation_round.dict())
                    generated_conversations.append(conversation_round)
                    
                    # Update relationships
                    await update_relationships(agent_objects, messages)
                    
                    # Update agent memories periodically
                    if conv_num == request.conversations_per_period - 1:  # Last conversation of the period
                        for agent in agent_objects:
                            await llm_manager.update_agent_memory(agent, conversation_history + [conversation_round.dict()])
        
        # Update simulation state
        final_day = current_day + request.target_days - 1
        final_period = "evening"  # Always end on evening
        
        await db.simulation_state.update_one(
            {"id": state["id"]},
            {"$set": {
                "current_day": final_day,
                "current_time_period": final_period
            }}
        )
        
        return {
            "message": f"Fast forwarded {request.target_days} days",
            "conversations_generated": len(generated_conversations),
            "final_day": final_day,
            "final_period": final_period,
            "api_requests_used": len(generated_conversations) * len(agent_objects)
        }
        
    except Exception as e:
        logging.error(f"Error during fast forward: {e}")
        raise HTTPException(status_code=500, detail=f"Fast forward failed: {str(e)}")

@api_router.post("/test/background-differences")
async def test_background_differences():
    """Create test agents with different backgrounds to demonstrate behavioral differences"""
    # Clear existing agents
    await db.agents.delete_many({})
    
    # Create agents with dramatically different backgrounds
    test_agents = [
        {
            "name": "Dr. Elena Vasquez",
            "archetype": "scientist", 
            "goal": "Analyze the situation from a scientific perspective",
            "expertise": "Astrophysics and Signal Analysis",
            "background": "PhD in Astrophysics, spent 15 years analyzing extraterrestrial signals at SETI. Expert in radio telescopy, pattern recognition in cosmic noise, and first-contact protocols. Thinks in terms of scientific method, data validation, and peer review."
        },
        {
            "name": "Captain Jake Morrison",
            "archetype": "leader",
            "goal": "Ensure team safety and mission success", 
            "expertise": "Military Strategy and Crisis Management",
            "background": "Former Navy SEAL with 20 years military experience including special operations and crisis response. Trained in tactical assessment, risk mitigation, command structure, and rapid decision-making under pressure. Views situations through security and operational readiness lens."
        },
        {
            "name": "Dr. Amara Okafor", 
            "archetype": "optimist",
            "goal": "Maintain team cohesion and psychological well-being",
            "expertise": "Clinical Psychology and Cross-Cultural Communication", 
            "background": "Clinical psychologist specializing in multicultural teams and stress management. PhD in Behavioral Psychology with focus on group dynamics in isolated environments. Approaches situations by analyzing interpersonal relationships, communication patterns, and psychological impact."
        },
        {
            "name": "Zara Al-Rashid",
            "archetype": "skeptic",
            "goal": "Question assumptions and identify potential risks",
            "expertise": "Cybersecurity and Information Warfare",
            "background": "Former CIA analyst specialized in disinformation detection and cybersecurity threats. Expert in recognizing deception, analyzing information sources, and identifying hidden agendas. Approaches everything with suspicion and looks for alternative explanations and potential threats."
        }
    ]
    
    created_agents = []
    for agent_data in test_agents:
        agent_create = AgentCreate(**agent_data)
        agent = await create_agent(agent_create)
        created_agents.append(agent)
    
    # Start simulation with a compelling scenario
    await start_simulation()
    
    # Set a scenario that will highlight background differences
    await db.simulation_state.update_one(
        {},
        {"$set": {"scenario": "A mysterious, structured signal has been detected coming from the direction of Proxima Centauri. The signal contains mathematical patterns and repeats every 11 hours. Ground control has lost communication and the team must decide how to respond."}},
        upsert=True
    )
    
    return {
        "message": "Test agents with diverse backgrounds created",
        "agents": created_agents,
        "scenario": "Mysterious signal from Proxima Centauri - watch how each agent's background influences their analysis and recommendations"
    }

@api_router.post("/simulation/start")
async def start_simulation(request: Optional[SimulationStartRequest] = None):
    """Start or reset the simulation with optional time limit - clears all user data for fresh start"""
    
    # Get time limit info from request
    time_limit_hours = None
    time_limit_display = None
    simulation_start_time = datetime.utcnow()
    
    if request:
        time_limit_hours = request.time_limit_hours
        time_limit_display = request.time_limit_display
    
    # Reset simulation state
    simulation = SimulationState(
        is_active=True,
        time_limit_hours=time_limit_hours,
        time_limit_display=time_limit_display,
        simulation_start_time=simulation_start_time,
        time_remaining_hours=time_limit_hours  # Initialize with full time limit
    )
    
    await db.simulation_state.delete_many({})
    await db.simulation_state.insert_one(simulation.dict())
    
    # For now, clear ALL simulation data globally (until proper user auth is fixed)
    await db.agents.delete_many({})  # Clear all agents  
    await db.conversations.delete_many({})  # Clear all conversations
    await db.relationships.delete_many({})  # Clear all relationships
    await db.summaries.delete_many({})  # Clear all summaries
    
    # Log the simulation start with time limit info
    time_limit_msg = f" with {time_limit_display} time limit" if time_limit_display else " with no time limit"
    
    return {
        "message": f"Simulation started{time_limit_msg}", 
        "state": simulation,
        "time_limit_active": time_limit_hours is not None,
        "time_limit_display": time_limit_display
    }

@api_router.get("/simulation/state")
async def get_simulation_state():
    """Get current simulation state"""
    state = await db.simulation_state.find_one()
    if not state:
        state = SimulationState().dict()
        await db.simulation_state.insert_one(state)
        return state
    
    # Convert MongoDB ObjectId to string to make it JSON serializable
    if '_id' in state:
        state['_id'] = str(state['_id'])
    
    # Calculate remaining time if time limit is set
    if state.get('time_limit_hours') and state.get('simulation_start_time'):
        start_time = state['simulation_start_time']
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        elif isinstance(start_time, dict):
            start_time = datetime.fromisoformat(start_time.get('$date', str(datetime.utcnow())))
        
        elapsed_hours = (datetime.utcnow() - start_time).total_seconds() / 3600
        remaining_hours = max(0, state['time_limit_hours'] - elapsed_hours)
        state['time_remaining_hours'] = remaining_hours
        state['time_elapsed_hours'] = elapsed_hours
        state['time_expired'] = remaining_hours <= 0
        
        # Update the database with calculated time
        await db.simulation_state.update_one(
            {"id": state["id"]},
            {"$set": {"time_remaining_hours": remaining_hours}}
        )
    
    return state

@api_router.get("/simulation/time-status")
async def get_time_status():
    """Get detailed time status for the current simulation"""
    state = await db.simulation_state.find_one()
    if not state:
        raise HTTPException(status_code=404, detail="Simulation not started")
    
    time_status = {
        "time_limit_active": bool(state.get('time_limit_hours')),
        "time_limit_display": state.get('time_limit_display'),
        "time_limit_hours": state.get('time_limit_hours'),
        "simulation_start_time": state.get('simulation_start_time'),
        "time_remaining_hours": None,
        "time_elapsed_hours": None,
        "time_expired": False,
        "time_pressure_level": "none"  # none, low, medium, high, critical
    }
    
    if state.get('time_limit_hours') and state.get('simulation_start_time'):
        start_time = state['simulation_start_time']
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        elif isinstance(start_time, dict):
            start_time = datetime.fromisoformat(start_time.get('$date', str(datetime.utcnow())))
        
        elapsed_hours = (datetime.utcnow() - start_time).total_seconds() / 3600
        remaining_hours = max(0, state['time_limit_hours'] - elapsed_hours)
        
        time_status.update({
            "time_remaining_hours": remaining_hours,
            "time_elapsed_hours": elapsed_hours,
            "time_expired": remaining_hours <= 0
        })
        
        # Determine pressure level
        if remaining_hours <= 0:
            time_status["time_pressure_level"] = "expired"
        elif remaining_hours <= state['time_limit_hours'] * 0.1:  # Last 10%
            time_status["time_pressure_level"] = "critical"
        elif remaining_hours <= state['time_limit_hours'] * 0.25:  # Last 25%
            time_status["time_pressure_level"] = "high"
        elif remaining_hours <= state['time_limit_hours'] * 0.5:   # Last 50%
            time_status["time_pressure_level"] = "medium"
        else:
            time_status["time_pressure_level"] = "low"
    
    return time_status

@api_router.post("/simulation/next-period")
async def advance_time_period():
    """Advance to next time period"""
    state = await db.simulation_state.find_one()
    if not state:
        raise HTTPException(status_code=404, detail="Simulation not started")
    
    current_period = state["current_time_period"]
    if current_period == "morning":
        new_period = "afternoon"
    elif current_period == "afternoon":
        new_period = "evening"
    else:  # evening
        new_period = "morning"
        # Advance day
        await db.simulation_state.update_one(
            {"id": state["id"]},
            {"$inc": {"current_day": 1}}
        )
    
    await db.simulation_state.update_one(
        {"id": state["id"]},
        {"$set": {"current_time_period": new_period}}
    )
    
    return {"message": f"Advanced to {new_period}", "new_period": new_period}

@api_router.get("/debug/agents")
async def debug_agents():
    """Debug endpoint to check agent loading"""
    try:
        agents = await db.agents.find().to_list(100)
        agent_count = len(agents)
        
        if agent_count == 0:
            return {"status": "no_agents", "count": 0}
        
        # Try to create agent objects
        try:
            agent_objects = [Agent(**agent) for agent in agents[:3]]  # Test first 3
            return {
                "status": "success", 
                "count": agent_count,
                "sample_agents": [
                    {"name": a.name, "archetype": a.archetype} for a in agent_objects
                ]
            }
        except Exception as e:
            return {
                "status": "agent_creation_error",
                "count": agent_count,
                "error": str(e),
                "sample_agent_data": agents[0] if agents else None
            }
    except Exception as e:
        return {"status": "database_error", "error": str(e)}

@api_router.post("/debug/simple-conversation")
async def debug_simple_conversation():
    """Simple conversation test without complex logic"""
    try:
        # Get just 2 agents
        agents = await db.agents.find().limit(2).to_list(2)
        if len(agents) < 2:
            return {"error": "Need at least 2 agents"}
        
        # Create agent objects
        agent1 = Agent(**agents[0])
        agent2 = Agent(**agents[1])
        
        # Simple fallback responses
        messages = [
            {
                "id": str(uuid.uuid4()),
                "agent_id": agent1.id,
                "agent_name": agent1.name,
                "message": f"Hello, I'm {agent1.name}. Let's discuss the current scenario.",
                "mood": "neutral",
                "timestamp": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "agent_id": agent2.id,
                "agent_name": agent2.name,
                "message": f"Hi {agent1.name}, I'm {agent2.name}. I agree we should analyze this situation carefully.",
                "mood": "neutral",
                "timestamp": datetime.utcnow()
            }
        ]
        
        # Save simple conversation
        conversation_round = {
            "id": str(uuid.uuid4()),
            "round_number": 1,
            "time_period": "morning",
            "scenario": "Test scenario",
            "scenario_name": "Debug Test",
            "messages": messages,
            "user_id": "",
            "created_at": datetime.utcnow(),
            "language": "en"
        }
        
        # Insert into database
        result = await db.conversations.insert_one(conversation_round)
        
        return {
            "success": True,
            "message": "Simple conversation created successfully",
            "conversation_id": conversation_round["id"],
            "agents": [agent1.name, agent2.name]
        }
        
    except Exception as e:
        logging.error(f"Debug conversation error: {e}")
        return {"error": str(e), "success": False}

@api_router.post("/conversation/generate")
async def generate_conversation():
    """Generate a conversation round between agents with sequential responses and progression tracking"""
    # Get current agents (all available agents for now, until auth is fixed)
    all_agents = await db.agents.find().to_list(100)
    if len(all_agents) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 agents for conversation. Please add more agents to your simulation.")
    
    # Limit to 3 agents per conversation for very fast generation
    import random
    agents = random.sample(all_agents, min(3, len(all_agents)))
    agent_objects = [Agent(**agent) for agent in agents]
    
    # Get simulation state and scenario
    state = await db.simulation_state.find_one()
    if not state:
        raise HTTPException(status_code=400, detail="No active simulation")
    
    scenario = state.get("scenario", "General discussion about current topics")
    scenario_name = state.get("scenario_name", "General Discussion")
    
    # Create simple fallback messages immediately (no LLM calls for now)
    messages = []
    topics = [
        "I think we should consider the practical implications of this scenario.",
        "That's an interesting perspective. Let me add my thoughts on this matter.", 
        "Based on my experience, I believe we need to approach this systematically."
    ]
    
    moods = ["thoughtful", "engaged", "analytical"]
    
    for i, agent in enumerate(agent_objects):
        message_text = topics[i % len(topics)]
        message = ConversationMessage(
            agent_name=agent.name,
            agent_id=agent.id,
            message=message_text,
            mood=moods[i % len(moods)],
            timestamp=datetime.utcnow()
        )
        messages.append(message)
    
    # Get conversation count for round numbering
    conversation_count = await db.conversations.count_documents({})
    
    # Create conversation round  
    conversation_round = ConversationRound(
        round_number=conversation_count + 1,
        time_period="Day 1 - morning",
        scenario=scenario,
        scenario_name=scenario_name,
        messages=messages,
        user_id=""  # Empty for global simulation conversations (until auth is fixed)
    )
    
    # Save conversation
    await db.conversations.insert_one(conversation_round.dict())
    
    return conversation_round
    agent_objects = [Agent(**agent) for agent in agents]
    
    # Get simulation state including language setting
    state = await db.simulation_state.find_one()
    if not state:
        raise HTTPException(status_code=404, detail="Simulation not started")
    
    # Generate conversation context
    time_period = state["current_time_period"]
    day = state["current_day"]
    scenario = state["scenario"]
    scenario_name = state.get("scenario_name", "")  # Default to empty if not set
    language = state.get("language", "en")  # Default to English if not set
    
    # Language settings for conversation generation
    language_instructions = {
        "en": "Respond in English.",
        "es": "Responde en español de manera natural y fluida.",
        "fr": "Répondez en français de manière naturelle et fluide.",
        "de": "Antworten Sie auf Deutsch in natürlicher und fließender Weise.",
        "it": "Rispondi in italiano in modo naturale e fluido.",
        "pt": "Responda em português de forma natural e fluente.",
        "ru": "Отвечайте на русском языке естественно и бегло.",
        "ja": "自然で流暢な日本語で答えてください。",
        "ko": "자연스럽고 유창한 한국어로 대답해주세요.",
        "zh": "请用自然流利的中文回答。",
        "hi": "प्राकृतिक और प्रवाहपूर्ण हिंदी में उत्तर दें।",
        "ar": "أجب باللغة العربية بطريقة طبيعية وطلقة."
    }
    
    language_instruction = language_instructions.get(language, language_instructions["en"])
    
    # Get recent conversation history for better context and progression tracking
    recent_conversations = await db.conversations.find().sort("created_at", -1).limit(10).to_list(10)
    
    # Get existing documents for agent reference (limit to recent/relevant docs)
    existing_documents = []
    try:
        # For now, get the most recent 5 documents - in production, this could be filtered by relevance
        docs_cursor = await db.documents.find().sort("metadata.updated_at", -1).limit(5).to_list(5)
        existing_documents = [
            {
                "id": doc["id"],
                "title": doc["metadata"]["title"],
                "category": doc["metadata"]["category"],
                "description": doc["metadata"]["description"],
                "authors": doc["metadata"]["authors"],
                "keywords": doc["metadata"]["keywords"]
            }
            for doc in docs_cursor
        ]
    except Exception as e:
        logging.warning(f"Could not fetch existing documents: {e}")
        existing_documents = []
    
    # Analyze recent topics to avoid repetition
    recent_topics = []
    if recent_conversations:
        for conv in recent_conversations[-5:]:  # Last 5 conversations
            for msg in conv.get('messages', []):
                if len(msg.get('message', '')) > 50:  # Substantial messages only
                    recent_topics.append(msg['message'][:100])
    
    # Determine conversation progression state
    conversation_count = await db.conversations.count_documents({})
    progression_prompts = {
        "early": "You're in early discussions. Focus on understanding the problem and initial ideas.",
        "middle": "You've been discussing this for a while. Start narrowing down options and making decisions.", 
        "advanced": "Time to make concrete decisions and action plans. Avoid rehashing old points."
    }
    
    if conversation_count < 5:
        progression_stage = "early"
    elif conversation_count < 15:
        progression_stage = "middle"
    else:
        progression_stage = "advanced"
    
    progression_guidance = progression_prompts[progression_stage]
    
    # Build conversation context with progression awareness
    context = f"Day {day}, {time_period}. {progression_guidance}"
    
    if recent_conversations:
        # Add context about recent discussions to avoid loops
        context += f"\n\nRecent discussion themes (avoid repeating these exactly):\n"
        for i, topic in enumerate(recent_topics[-3:], 1):
            context += f"- Theme {i}: {topic}...\n"
        context += "\nBuild on these ideas or introduce new angles rather than restating the same points."
    else:
        context += "\nStart a focused discussion about the scenario."
    
    # Generate responses SEQUENTIALLY with varied conversation styles
    messages = []
    conversation_so_far = ""
    
    # Define response types to encourage variety
    response_types = [
        "direct_answer",      # Answer questions directly
        "challenge_idea",     # Challenge or disagree with something
        "build_on_idea",     # Build on what others said
        "provide_alternative", # Suggest different approach
        "make_decision",     # Be decisive about next steps
        "share_expertise"    # Use professional background
    ]
    
    for i, agent in enumerate(agent_objects):
        # Choose response type based on conversation flow
        if i == 0:
            # First speaker introduces topic or makes statement
            agent_guidance = "Introduce a specific point or make a clear statement. Don't ask questions - be assertive about your perspective."
        elif i == 1:
            # Second speaker responds to first
            agent_guidance = "Respond directly to what was just said. Agree, disagree, or build on it. Be definitive."
        else:
            # Later speakers synthesize or make decisions
            agent_guidance = "Help move the discussion forward. Make a decision, propose next steps, or provide a conclusive perspective."
        
        # Build context including what other agents have said in THIS conversation round
        current_context = context + f"\n\n{agent_guidance}\n"
        
        if messages:  # If others have already spoken in this round
            current_context += f"\nIn this conversation:\n"
            for prev_msg in messages:
                current_context += f"- {prev_msg.agent_name}: {prev_msg.message}\n"
            current_context += f"\nRespond naturally as {agent.name}. Don't always ask questions - sometimes just state your opinion or make a decision."
        
        # Add small delay between requests to avoid rate limiting
        if i > 0:
            await asyncio.sleep(3)  # 3 second delay between agents
        
        response = await llm_manager.generate_agent_response(
            agent, scenario, agent_objects, current_context, recent_conversations, language_instruction, existing_documents, state
        )
        
        message = ConversationMessage(
            agent_id=agent.id,
            agent_name=agent.name,
            message=response,
            mood=agent.current_mood
        )
        messages.append(message)
        
        # Update conversation_so_far for next agent
        conversation_so_far += f"{agent.name}: {response}\n"
    
    # Create conversation round  
    conversation_round = ConversationRound(
        round_number=conversation_count + 1,
        time_period=f"Day {day} - {time_period}",
        scenario=scenario,
        scenario_name=scenario_name,
        messages=messages,
        user_id=""  # Empty for global simulation conversations (until auth is fixed)
    )
    
    await db.conversations.insert_one(conversation_round.dict())
    
    # Update agent relationships based on interactions
    await update_relationships(agent_objects, messages)
    
    # ENHANCED: Action-Oriented Behavior - Analyze for document creation triggers
    try:
        # Build full conversation text for analysis
        conversation_text = ""
        for msg in messages:
            conversation_text += f"{msg.agent_name}: {msg.message}\n"
        
        # Analyze for action triggers
        trigger_result = await llm_manager.analyze_conversation_for_action_triggers(
            conversation_text, agent_objects
        )
        
        # If document should be created, get team consensus first
        if trigger_result.should_create_document:
            logging.info(f"Action trigger detected: {trigger_result.trigger_phrase}")
            logging.info(f"Requesting team vote for: {trigger_result.document_title}")
            
            # Get team vote on document creation
            voting_results = await llm_manager.check_agent_voting_consensus(
                agent_objects, 
                f"Create {trigger_result.document_type} titled '{trigger_result.document_title}'",
                conversation_text
            )
            
            if voting_results["consensus"]:
                logging.info(f"Team voted YES - Creating {trigger_result.document_type}: {trigger_result.document_title}")
                
                # Find the agent who should create the document (choose one who volunteered or is most relevant)
                creating_agent = agent_objects[0]  # Default to first agent
                for agent in agent_objects:
                    # Look for commitment phrases in their messages
                    for msg in messages:
                        if msg.agent_name == agent.name:
                            commitment_phrases = ["i'll create", "let me create", "i'll develop", "i'll draft", "i'm creating"]
                            if any(phrase in msg.message.lower() for phrase in commitment_phrases):
                                creating_agent = agent
                                break
                    if creating_agent.id != agent_objects[0].id:
                        break
                
                # Generate document content
                document_content = await llm_manager.generate_document_content(
                    trigger_result.document_type,
                    trigger_result.document_title,
                    conversation_text,
                    creating_agent
                )
                
                # Create document metadata
                safe_title = re.sub(r'[^a-zA-Z0-9\s\-_]', '', trigger_result.document_title)
                safe_title = re.sub(r'\s+', '_', safe_title)
                filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d')}.md"
                
                # Get user_id from conversation round (this is tricky - we need to find current user)
                # For now, we'll store it without user_id and let the frontend associate it
                metadata = DocumentMetadata(
                    title=trigger_result.document_title,
                    filename=filename,
                    authors=[creating_agent.name],
                    category=trigger_result.document_type.title(),
                    description=f"Team-approved creation from discussion - {trigger_result.document_title}",
                    keywords=[trigger_result.document_type, "team-generated", "action-oriented", "voted-approved"],
                    simulation_id=str(conversation_round.id),
                    conversation_round=conversation_round.round_number,
                    scenario_name=scenario_name,  # Add scenario name for organization
                    user_id=""  # Will be set by frontend when user is available
                )
                
                document = Document(
                    metadata=metadata,
                    content=document_content,
                    created_by_agents=[creating_agent.id],
                    conversation_context=conversation_text[:500],
                    action_trigger=trigger_result.trigger_phrase
                )
                
                # Save document to database
                await db.documents.insert_one(document.dict())
                
                # Add voting results and document creation notification to conversation round
                voting_summary = f"Team Vote: {voting_results['summary']}"
                
                doc_notification = ConversationMessage(
                    agent_id=creating_agent.id,
                    agent_name=creating_agent.name,
                    message=f"📋 **Document Created: {trigger_result.document_title}**\n\n{voting_summary} - The team has approved this creation!\n\nI've created and uploaded the {trigger_result.document_type} to our File Center. It's ready for review and implementation.\n\n*Filename: {filename}*\n*Category: {metadata.category}*",
                    mood="productive"
                )
                
                # Update the conversation round with the document creation message
                conversation_round.messages.append(doc_notification)
                await db.conversations.update_one(
                    {"id": conversation_round.id},
                    {"$set": {"messages": [msg.dict() for msg in conversation_round.messages]}}
                )
                
                logging.info(f"Document created successfully with team approval: {document.id}")
            else:
                logging.info(f"Team voted NO - Document creation rejected: {voting_results['summary']}")
                
                # Add voting results notification showing the rejection
                rejection_notification = ConversationMessage(
                    agent_id=agent_objects[0].id,  # Use first agent as messenger
                    agent_name=agent_objects[0].name,
                    message=f"📊 **Team Vote Results**: {voting_results['summary']}\n\nThe proposal to create '{trigger_result.document_title}' was not approved by the team. We'll continue the discussion.",
                    mood="neutral"
                )
                
                # Update the conversation round with the voting results
                conversation_round.messages.append(rejection_notification)
                await db.conversations.update_one(
                    {"id": conversation_round.id},
                    {"$set": {"messages": [msg.dict() for msg in conversation_round.messages]}}
                )
            
    except Exception as e:
        logging.error(f"Error in action-oriented document creation: {e}")
        # Don't fail the conversation if document creation fails
        pass
    
    return conversation_round

@api_router.get("/conversations")
async def get_conversations():
    """Get conversation rounds for the simulation"""
    # Get global simulation conversations (until auth is fixed)
    conversations = await db.conversations.find({
        "user_id": ""  # Global simulation conversations
    }).sort("created_at", 1).to_list(1000)
    
    # Convert to response format, handling any missing fields
    conversation_rounds = []
    for conv in conversations:
        try:
            # Ensure all required fields exist with defaults
            conv_data = {
                "id": conv.get("id", str(uuid.uuid4())),
                "round_number": conv.get("round_number", 1),
                "time_period": conv.get("time_period", "morning"),
                "scenario": conv.get("scenario", ""),
                "scenario_name": conv.get("scenario_name", ""),
                "messages": conv.get("messages", []),
                "user_id": conv.get("user_id", ""),
                "created_at": conv.get("created_at", datetime.utcnow()),
                "language": conv.get("language", "en"),
                "original_language": conv.get("original_language"),
                "translated_at": conv.get("translated_at"),
                "force_translated": conv.get("force_translated", False)
            }
            conversation_rounds.append(conv_data)
        except Exception as e:
            logging.warning(f"Skipping malformed conversation: {e}")
            continue
    
    return conversation_rounds

@api_router.get("/relationships")
async def get_relationships():
    """Get all agent relationships"""
    relationships = await db.relationships.find().to_list(1000)
    
    # Convert MongoDB documents to JSON-serializable format
    processed_relationships = []
    for rel in relationships:
        rel_dict = {
            "id": rel.get("id", str(rel.get("_id", ""))),
            "agent1_id": rel.get("agent1_id", ""),
            "agent2_id": rel.get("agent2_id", ""),
            "score": rel.get("score", 0),
            "status": rel.get("status", "neutral"),
            "updated_at": rel.get("updated_at").isoformat() if rel.get("updated_at") else ""
        }
        processed_relationships.append(rel_dict)
    
    return processed_relationships

@api_router.post("/avatars/generate-library", response_model=dict)
async def generate_library_avatars():
    """Generate avatars for all agents in the library that don't have them"""
    try:
        # Define all library agents with their prompts
        library_agents = []
        
        # Healthcare agents
        healthcare_agents = [
            {"name": "Dr. Sarah Chen", "prompt": "Professional headshot of Dr. Sarah Chen, Asian American woman, precision medicine oncologist, wearing professional medical attire, confident expression, medical research facility background"},
            {"name": "Dr. Marcus Rodriguez", "prompt": "Professional headshot of Dr. Marcus Rodriguez, Hispanic man, emergency medicine physician, wearing professional medical attire, leadership expression, hospital emergency department background"},
            {"name": "Dr. Katherine Vale", "prompt": "Professional headshot of Dr. Katherine Vale, Caucasian woman, family medicine physician, wearing professional medical attire, caring expression, family practice clinic background"},
            {"name": "Dr. Ahmed Hassan", "prompt": "Professional headshot of Dr. Ahmed Hassan, Middle Eastern man, internal medicine specialist, wearing professional medical attire, thoughtful expression, medical office background"},
            {"name": "Dr. Elena Petrov", "prompt": "Professional headshot of Dr. Elena Petrov, Eastern European woman, clinical pharmacologist, wearing professional attire with lab coat, scientific expression, pharmaceutical research lab background"},
            {"name": "Dr. James Park", "prompt": "Professional headshot of Dr. James Park, Korean American man, drug safety specialist, wearing professional attire, analytical expression, pharmaceutical safety office background"},
            {"name": "Dr. Maria Santos", "prompt": "Professional headshot of Dr. Maria Santos, Hispanic woman, pharmaceutical research director, wearing executive business attire, leadership expression, pharmaceutical company office background"},
            {"name": "Dr. Lisa Wang", "prompt": "Professional headshot of Dr. Lisa Wang, Asian American woman, gene therapy researcher, wearing lab coat and safety equipment, innovative expression, gene therapy laboratory background"},
            {"name": "Dr. Robert Kim", "prompt": "Professional headshot of Dr. Robert Kim, Korean American man, bioengineering specialist, wearing professional lab attire, scientific expression, bioengineering research facility background"},
            {"name": "Dr. Jennifer Thompson", "prompt": "Professional headshot of Dr. Jennifer Thompson, Caucasian woman, synthetic biology expert, wearing modern lab attire, optimistic expression, synthetic biology laboratory background"},
            {"name": "Maria Rodriguez, RN", "prompt": "Professional headshot of Maria Rodriguez, Hispanic woman, critical care nurse, wearing nursing scrubs with professional overlay, adventurous expression, modern ICU background"},
            {"name": "David Chen, RN", "prompt": "Professional headshot of David Chen, Asian American man, nurse manager, wearing professional nursing attire, diplomatic expression, hospital management office background"},
            {"name": "Susan Williams, RN", "prompt": "Professional headshot of Susan Williams, Caucasian woman, pediatric nurse, wearing colorful pediatric nursing attire, warm optimistic expression, children's hospital background"},
            {"name": "Dr. Michael Johnson", "prompt": "Professional headshot of Dr. Michael Johnson, African American man, epidemiologist, wearing professional public health attire, leadership expression, CDC operations center background"},
            {"name": "Dr. Patricia Lee", "prompt": "Professional headshot of Dr. Patricia Lee, Asian American woman, environmental health specialist, wearing professional attire with field equipment, scientific expression, environmental monitoring station background"},
            {"name": "Dr. James Wilson", "prompt": "Professional headshot of Dr. James Wilson, Caucasian man, community health director, wearing professional public health attire, optimistic expression, community health center background"},
            {"name": "Dr. Rachel Green", "prompt": "Professional headshot of Dr. Rachel Green, Caucasian woman, clinical nutritionist, wearing professional medical attire, scientific expression, clinical nutrition laboratory background"},
            {"name": "Maria Gonzalez, RD", "prompt": "Professional headshot of Maria Gonzalez, Hispanic woman, pediatric dietitian, wearing professional healthcare attire, caring expression, pediatric nutrition clinic background"},
            {"name": "Dr. Kevin Brown", "prompt": "Professional headshot of Dr. Kevin Brown, African American man, sports physical therapist, wearing professional therapy attire, adventurous expression, sports medicine facility background"},
            {"name": "Dr. Lisa Anderson", "prompt": "Professional headshot of Dr. Lisa Anderson, Caucasian woman, neurologic physical therapist, wearing professional therapy attire, optimistic expression, rehabilitation center background"},
            {"name": "Dr. Emily Carter", "prompt": "Professional headshot of Dr. Emily Carter, Caucasian woman, small animal veterinarian, wearing veterinary attire, compassionate expression, veterinary clinic background"},
            {"name": "Dr. Mark Davis", "prompt": "Professional headshot of Dr. Mark Davis, Caucasian man, wildlife veterinarian, wearing field veterinary gear, adventurous expression, wildlife conservation background"},
            {"name": "Dr. Amanda Foster", "prompt": "Professional headshot of Dr. Amanda Foster, Caucasian woman, clinical research coordinator, wearing professional research attire, scientific expression, clinical trials center background"},
            {"name": "Dr. Thomas Mitchell", "prompt": "Professional headshot of Dr. Thomas Mitchell, Caucasian man, biostatistician, wearing professional academic attire, analytical expression, statistical research office background"},
            {"name": "Dr. Jennifer Walsh", "prompt": "Professional headshot of Dr. Jennifer Walsh, Caucasian woman, infectious disease epidemiologist, wearing professional public health attire, leadership expression, global health organization background"},
            {"name": "Dr. Carlos Mendez", "prompt": "Professional headshot of Dr. Carlos Mendez, Hispanic man, chronic disease epidemiologist, wearing professional research attire, scientific expression, epidemiology research center background"}
        ]
        
        # Finance agents  
        finance_agents = [
            {"name": "Marcus Goldman", "prompt": "Professional headshot of Marcus Goldman, Caucasian man, investment banking managing director, wearing executive business suit, leadership expression, Wall Street office background"},
            {"name": "Sarah Chen", "prompt": "Professional headshot of Sarah Chen, Asian American woman, equity research director, wearing professional business attire, analytical expression, financial research office background"},
            {"name": "David Park", "prompt": "Professional headshot of David Park, Korean American man, capital markets VP, wearing modern business attire, innovative expression, trading floor background"},
            {"name": "Jennifer Liu", "prompt": "Professional headshot of Jennifer Liu, Asian American woman, venture capital general partner, wearing contemporary business attire, adventurous expression, Silicon Valley office background"},
            {"name": "Michael Torres", "prompt": "Professional headshot of Michael Torres, Hispanic man, early stage VC principal, wearing modern business casual, optimistic expression, startup accelerator background"},
            {"name": "Robert Sterling", "prompt": "Professional headshot of Robert Sterling, Caucasian man, private equity managing partner, wearing executive business suit, leadership expression, private equity office background"},
            {"name": "Amanda Foster", "prompt": "Professional headshot of Amanda Foster, Caucasian woman, private equity VP, wearing professional business attire, analytical expression, financial analysis office background"},
            {"name": "Patricia Williams", "prompt": "Professional headshot of Patricia Williams, African American woman, chief underwriting officer, wearing executive business attire, diplomatic expression, insurance company headquarters background"},
            {"name": "Carlos Rodriguez", "prompt": "Professional headshot of Carlos Rodriguez, Hispanic man, fraud investigation director, wearing professional investigative attire, skeptical expression, insurance investigation office background"},
            {"name": "Helen Chang", "prompt": "Professional headshot of Helen Chang, Asian American woman, accounting partner, wearing professional business attire, scientific expression, Big Four accounting firm background"},
            {"name": "James Mitchell", "prompt": "Professional headshot of James Mitchell, Caucasian man, corporate controller, wearing business attire, diplomatic expression, corporate finance office background"},
            {"name": "Diana Thompson", "prompt": "Professional headshot of Diana Thompson, Caucasian woman, audit partner, wearing professional business attire, skeptical expression, audit firm office background"},
            {"name": "Kevin Brown", "prompt": "Professional headshot of Kevin Brown, African American man, IT audit director, wearing professional tech attire, scientific expression, IT audit center background"},
            {"name": "Rebecca Martinez", "prompt": "Professional headshot of Rebecca Martinez, Hispanic woman, international tax director, wearing professional business attire, scientific expression, international tax office background"},
            {"name": "Thomas Anderson", "prompt": "Professional headshot of Thomas Anderson, Caucasian man, tax controversy manager, wearing professional legal attire, diplomatic expression, tax law office background"},
            {"name": "Victoria Sterling", "prompt": "Professional headshot of Victoria Sterling, Caucasian woman, real estate investment director, wearing executive business attire, leadership expression, real estate investment office background"},
            {"name": "Daniel Kim", "prompt": "Professional headshot of Daniel Kim, Korean American man, real estate development manager, wearing modern business attire, adventurous expression, development project site background"},
            {"name": "Margaret Davis", "prompt": "Professional headshot of Margaret Davis, Caucasian woman, chief credit officer, wearing executive banking attire, diplomatic expression, bank headquarters background"},
            {"name": "Steven Wilson", "prompt": "Professional headshot of Steven Wilson, Caucasian man, digital banking VP, wearing modern tech business attire, optimistic expression, fintech office background"},
            {"name": "Alexander Cross", "prompt": "Professional headshot of Alexander Cross, Caucasian man, proprietary trading head, wearing sharp business attire, adventurous expression, trading floor background"},
            {"name": "Jennifer Liu", "prompt": "Professional headshot of Jennifer Liu, Asian American woman, quantitative researcher, wearing professional tech attire, scientific expression, quantitative research lab background"},
            {"name": "Catherine Moore", "prompt": "Professional headshot of Catherine Moore, Caucasian woman, chief risk officer, wearing executive business attire, skeptical expression, risk management center background"},
            {"name": "Ryan Foster", "prompt": "Professional headshot of Ryan Foster, Caucasian man, model risk management VP, wearing professional analytical attire, scientific expression, risk modeling office background"},
            {"name": "Linda Johnson", "prompt": "Professional headshot of Linda Johnson, African American woman, chief actuary, wearing professional business attire, scientific expression, actuarial office background"},
            {"name": "Mark Thompson", "prompt": "Professional headshot of Mark Thompson, Caucasian man, P&C actuary, wearing professional analytical attire, skeptical expression, actuarial modeling center background"}
        ]
        
        # Technology agents
        technology_agents = [
            {"name": "Dr. Aisha Muhammad", "prompt": "Professional headshot of Dr. Aisha Muhammad, African American woman, AI researcher, wearing professional attire, confident expression, tech office background"},
            {"name": "Marcus Chen", "prompt": "Professional headshot of Marcus Chen, Asian American man, software engineer, wearing casual tech attire, friendly expression, modern office background"},
            {"name": "Emily Rodriguez", "prompt": "Professional headshot of Emily Rodriguez, Hispanic woman, product manager, wearing business attire, approachable expression, collaborative workspace background"},
            {"name": "Dr. Kevin Park", "prompt": "Professional headshot of Dr. Kevin Park, Korean American man, data scientist, wearing glasses and casual attire, thoughtful expression, data visualization background"},
            {"name": "Dr. Samira Hassan", "prompt": "Professional headshot of Dr. Samira Hassan, Middle Eastern woman, data science director, wearing professional attire, warm smile, modern analytics office background"},
            {"name": "Robert Kim", "prompt": "Professional headshot of Robert Kim, Korean American man, model validation specialist, wearing business attire, serious expression, analytical workspace background"},
            {"name": "Roberto Silva", "prompt": "Professional headshot of Roberto Silva, Hispanic man, cybersecurity analyst, wearing dark professional attire, intense focused expression, security operations center background"},
            {"name": "Catherine Williams", "prompt": "Professional headshot of Catherine Williams, African American woman, CISO, wearing executive business attire, confident leadership expression, corporate boardroom background"},
            {"name": "Dr. Lisa Chen", "prompt": "Professional headshot of Dr. Lisa Chen, Asian American woman, cryptography researcher, wearing professional attire with subtle tech accessories, thoughtful expression, research laboratory background"},
            {"name": "Dr. Yuki Tanaka", "prompt": "Professional headshot of Dr. Yuki Tanaka, Japanese man, ML researcher, wearing casual academic attire, intelligent expression, university research lab background"},
            {"name": "Jennifer Walsh", "prompt": "Professional headshot of Jennifer Walsh, Caucasian woman, AI product director, wearing modern business attire, enthusiastic expression, innovative tech workspace background"},
            {"name": "Dr. Ahmed Hassan", "prompt": "Professional headshot of Dr. Ahmed Hassan, Middle Eastern man, AI safety researcher, wearing professional attire, serious analytical expression, AI research facility background"},
            {"name": "Maria Santos", "prompt": "Professional headshot of Maria Santos, Hispanic woman, DevOps manager, wearing casual tech attire, collaborative expression, modern development office background"},
            {"name": "David Kim", "prompt": "Professional headshot of David Kim, Korean American man, platform engineer, wearing modern casual attire, innovative expression, cutting-edge tech lab background"},
            {"name": "Dr. Rachel Anderson", "prompt": "Professional headshot of Dr. Rachel Anderson, Caucasian woman, SRE, wearing professional casual attire, focused expression, monitoring dashboard background"},
            {"name": "Thomas Wright", "prompt": "Professional headshot of Thomas Wright, Caucasian man, cloud architect, wearing executive business attire, strategic expression, modern cloud operations center background"},
            {"name": "Dr. Lisa Park", "prompt": "Professional headshot of Dr. Lisa Park, Korean American woman, cloud engineer, wearing technical professional attire, analytical expression, cloud infrastructure visualization background"},
            {"name": "Hassan Al-Mahmoud", "prompt": "Professional headshot of Hassan Al-Mahmoud, Middle Eastern man, cloud consultant, wearing business attire, diplomatic expression, international business meeting background"},
            {"name": "Dr. Satoshi Nakamura", "prompt": "Professional headshot of Dr. Satoshi Nakamura, Japanese man, blockchain researcher, wearing modern academic attire, innovative expression, blockchain research lab background"},
            {"name": "Victoria Chen", "prompt": "Professional headshot of Victoria Chen, Asian American woman, DeFi product manager, wearing modern business attire, optimistic expression, fintech startup office background"},
            {"name": "Marcus Johnson", "prompt": "Professional headshot of Marcus Johnson, African American man, blockchain analyst, wearing conservative business attire, analytical expression, corporate consulting office background"},
            {"name": "Dr. Maria Rodriguez", "prompt": "Professional headshot of Dr. Maria Rodriguez, Hispanic woman, civil engineer, wearing professional engineering attire with hard hat nearby, confident leadership expression, construction site background"},
            {"name": "James Wilson", "prompt": "Professional headshot of James Wilson, Caucasian man, construction engineer, wearing rugged outdoor engineering gear, adventurous expression, extreme construction environment background"},
            {"name": "Dr. Emily Foster", "prompt": "Professional headshot of Dr. Emily Foster, Caucasian woman, infrastructure researcher, wearing modern professional attire with tech elements, scientific expression, smart city lab background"},
            {"name": "Dr. Robert Kim", "prompt": "Professional headshot of Dr. Robert Kim, Korean American man, manufacturing engineer, wearing technical professional attire, precise expression, advanced robotics facility background"},
            {"name": "Jennifer Walsh", "prompt": "Professional headshot of Jennifer Walsh, Caucasian woman, biomedical engineer, wearing modern professional attire, compassionate expression, medical device laboratory background"},
            {"name": "Hassan Al-Mahmoud", "prompt": "Professional headshot of Hassan Al-Mahmoud, Middle Eastern man, energy engineer, wearing professional engineering attire, diplomatic expression, renewable energy facility background"},
            {"name": "Dr. Lisa Chen", "prompt": "Professional headshot of Dr. Lisa Chen, Asian American woman, power systems engineer, wearing professional engineering attire, intelligent expression, power grid control center background"},
            {"name": "Marcus Johnson", "prompt": "Professional headshot of Marcus Johnson, African American man, semiconductor engineer, wearing modern tech attire, innovative expression, advanced semiconductor fabrication facility background"},
            {"name": "Dr. Patricia Foster", "prompt": "Professional headshot of Dr. Patricia Foster, Caucasian woman, instrumentation engineer, wearing lab coat with precision equipment, focused expression, quantum measurement laboratory background"},
            {"name": "Dr. Sarah Mitchell", "prompt": "Professional headshot of Dr. Sarah Mitchell, Caucasian woman, chemical engineer, wearing lab coat with safety equipment, sustainable expression, green chemistry laboratory background"},
            {"name": "Dr. Ahmed Hassan", "prompt": "Professional headshot of Dr. Ahmed Hassan, Middle Eastern man, process safety engineer, wearing safety gear and professional attire, serious safety-focused expression, chemical plant safety control room background"},
            {"name": "Dr. Elena Rodriguez", "prompt": "Professional headshot of Dr. Elena Rodriguez, Hispanic woman, pharmaceutical engineer, wearing clean room attire, optimistic expression, pharmaceutical manufacturing facility background"},
            {"name": "Dr. Marcus Johnson", "prompt": "Professional headshot of Dr. Marcus Johnson, African American man, aerospace engineer, wearing flight suit with space patches, adventurous expression, rocket engine test facility background"},
            {"name": "Dr. Catherine Williams", "prompt": "Professional headshot of Dr. Catherine Williams, African American woman, aerospace director, wearing executive aviation attire, leadership expression, electric aircraft hangar background"},
            {"name": "Dr. Yuki Tanaka", "prompt": "Professional headshot of Dr. Yuki Tanaka, Japanese man, materials scientist, wearing lab coat with technical equipment, contemplative expression, advanced materials laboratory background"},
            {"name": "Dr. Jennifer Walsh", "prompt": "Professional headshot of Dr. Jennifer Walsh, Caucasian woman, neural engineer, wearing medical professional attire, hopeful expression, neurotechnology laboratory background"},
            {"name": "Dr. Anna Petrov", "prompt": "Professional headshot of Dr. Anna Petrov, Eastern European woman, nanomedicine researcher, wearing clean room attire, focused expression, nanotechnology research facility background"},
            {"name": "Dr. Carlos Rivera", "prompt": "Professional headshot of Dr. Carlos Rivera, Hispanic man, clinical engineer, wearing medical professional attire, collaborative expression, hospital technology center background"}
        ]
        
        # Combine all agents
        library_agents = healthcare_agents + finance_agents + technology_agents
        
        generated_count = 0
        errors = []
        
        for agent in library_agents:
            try:
                # Enhanced prompt for better avatar results
                enhanced_prompt = f"professional portrait, headshot, detailed face, {agent['prompt']}, high quality, photorealistic, studio lighting, neutral background"
                
                # Submit to fal.ai using the Flux Schnell model
                handler = await fal_client.submit_async(
                    "fal-ai/flux/schnell",
                    arguments={
                        "prompt": enhanced_prompt,
                        "image_size": "portrait_4_3",
                        "num_images": 1,
                        "enable_safety_checker": True
                    }
                )
                
                # Get the result
                result = await handler.get()
                
                if result and result.get("images") and len(result["images"]) > 0:
                    avatar_url = result["images"][0]["url"]
                    agent["avatar_url"] = avatar_url
                    generated_count += 1
                    logging.info(f"Avatar generated for {agent['name']}: {avatar_url}")
                else:
                    errors.append(f"Failed to generate avatar for {agent['name']}: No image returned")
                    
            except Exception as e:
                errors.append(f"Error generating avatar for {agent['name']}: {str(e)}")
                logging.error(f"Avatar generation error for {agent['name']}: {str(e)}")
        
        return {
            "success": True,
            "generated_count": generated_count,
            "total_agents": len(library_agents),
            "errors": errors,
            "agents": library_agents
        }
        
    except Exception as e:
        logging.error(f"Library avatar generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Avatar generation failed: {str(e)}")

@api_router.post("/avatars/generate", response_model=AvatarResponse)
async def generate_avatar(request: AvatarGenerateRequest):
    """Generate an avatar image using fal.ai"""
    if not request.prompt or len(request.prompt.strip()) < 2:
        raise HTTPException(
            status_code=400,
            detail="Prompt must be at least 2 characters long"
        )
    
    try:
        # Enhanced prompt for better avatar results
        enhanced_prompt = f"professional portrait, headshot, detailed face, {request.prompt}, high quality, photorealistic, studio lighting, neutral background"
        
        # Submit to fal.ai using the Flux Schnell model (fastest and cheapest)
        handler = await fal_client.submit_async(
            "fal-ai/flux/schnell",
            arguments={
                "prompt": enhanced_prompt,
                "image_size": "portrait_4_3",  # Good for avatars
                "num_images": 1,
                "enable_safety_checker": True
            }
        )
        
        # Get the result
        result = await handler.get()
        
        if result and result.get("images") and len(result["images"]) > 0:
            avatar_url = result["images"][0]["url"]
            logging.info(f"Avatar generated successfully for prompt: {request.prompt}")
            return AvatarResponse(
                success=True,
                image_url=avatar_url
            )
        else:
            logging.warning(f"No avatar generated for prompt: {request.prompt}")
            return AvatarResponse(
                success=False,
                error="No image was generated"
            )
            
    except Exception as e:
        logging.error(f"Avatar generation error: {e}")
        return AvatarResponse(
            success=False,
            error=f"Avatar generation failed: {str(e)}"
        )

async def update_relationships(agents: List[Agent], messages: List[ConversationMessage]):
    """Update agent relationships based on conversation sentiment"""
    # Simple relationship update logic
    for i, agent1 in enumerate(agents):
        for j, agent2 in enumerate(agents):
            if i != j:
                # Find existing relationship
                relationship = await db.relationships.find_one({
                    "agent1_id": agent1.id,
                    "agent2_id": agent2.id
                })
                
                if not relationship:
                    relationship = Relationship(
                        agent1_id=agent1.id,
                        agent2_id=agent2.id
                    )
                    await db.relationships.insert_one(relationship.dict())
                
                # Simple sentiment analysis based on personality compatibility
                compatibility = calculate_compatibility(agent1, agent2)
                score_change = 1 if compatibility > 0.5 else -1
                
                # Handle both dict and Pydantic model cases
                current_score = relationship["score"] if isinstance(relationship, dict) else relationship.score
                new_score = max(-10, min(10, current_score + score_change))
                status = "friends" if new_score > 3 else "tension" if new_score < -3 else "neutral"
                
                await db.relationships.update_one(
                    {"agent1_id": agent1.id, "agent2_id": agent2.id},
                    {"$set": {"score": new_score, "status": status, "updated_at": datetime.utcnow()}}
                )

def calculate_compatibility(agent1: Agent, agent2: Agent) -> float:
    """Calculate compatibility between two agents based on personality traits"""
    p1, p2 = agent1.personality, agent2.personality
    
    # Simple compatibility scoring
    extro_diff = abs(p1.extroversion - p2.extroversion)
    coop_match = min(p1.cooperativeness, p2.cooperativeness)
    
    compatibility = (coop_match / 10) - (extro_diff / 20)
    return max(0, min(1, compatibility))

@api_router.post("/simulation/toggle-auto-mode")
async def toggle_auto_mode(request: dict):
    """Toggle automation settings for conversations and time"""
    auto_conversations = request.get("auto_conversations", False)
    auto_time = request.get("auto_time", False)
    conversation_interval = request.get("conversation_interval", 10)
    time_interval = request.get("time_interval", 60)
    
    await db.simulation_state.update_one(
        {},
        {"$set": {
            "auto_conversations": auto_conversations,
            "auto_time": auto_time,
            "conversation_interval": conversation_interval,
            "time_interval": time_interval
        }},
        upsert=True
    )
    
    return {
        "message": f"Auto mode updated - Conversations: {'ON' if auto_conversations else 'OFF'}, Time: {'ON' if auto_time else 'OFF'}",
        "auto_conversations": auto_conversations,
        "auto_time": auto_time,
        "conversation_interval": conversation_interval,
        "time_interval": time_interval
    }

@api_router.post("/simulation/auto-weekly-report")
async def setup_auto_weekly_report(request: dict):
    """Setup automatic weekly report generation"""
    enabled = request.get("enabled", False)
    interval_hours = request.get("interval_hours", 168)  # Default 7 days = 168 hours
    
    await db.simulation_state.update_one(
        {},
        {"$set": {
            "auto_weekly_reports": enabled,
            "report_interval_hours": interval_hours,
            "last_auto_report": datetime.utcnow().isoformat() if enabled else None
        }},
        upsert=True
    )
    
    return {
        "message": f"Auto weekly reports {'enabled' if enabled else 'disabled'}",
        "interval_hours": interval_hours,
        "next_report_in": f"{interval_hours} hours" if enabled else "disabled"
    }

@api_router.get("/reports/check-auto-generation")
async def check_auto_report_generation():
    """Check if it's time to generate an automatic weekly report"""
    state = await db.simulation_state.find_one()
    if not state or not state.get("auto_weekly_reports"):
        return {"should_generate": False, "reason": "Auto reports disabled"}
    
    last_report = state.get("last_auto_report")
    if not last_report:
        return {"should_generate": True, "reason": "No previous auto report"}
    
    last_report_time = datetime.fromisoformat(last_report.replace('Z', '+00:00'))
    interval_hours = state.get("report_interval_hours", 168)
    time_since_last = datetime.utcnow() - last_report_time.replace(tzinfo=None)
    
    should_generate = time_since_last.total_seconds() >= (interval_hours * 3600)
    
    return {
        "should_generate": should_generate,
        "hours_since_last": time_since_last.total_seconds() / 3600,
        "interval_hours": interval_hours,
        "reason": "Time for next report" if should_generate else f"Next report in {interval_hours - (time_since_last.total_seconds() / 3600):.1f} hours"
    }

@api_router.get("/summaries")
async def get_summaries():
    """Get all generated summaries with structured formatting"""
    summaries = await db.summaries.find().sort("created_at", -1).to_list(100)
    
    # Convert MongoDB documents to JSON-serializable format
    processed_summaries = []
    for summary in summaries:
        # Remove MongoDB ObjectId and convert to dict
        summary_dict = {
            "id": summary.get("id", str(summary.get("_id", ""))),
            "summary": summary.get("summary", ""),
            "day_generated": summary.get("day_generated", 1),
            "conversations_analyzed": summary.get("conversations_analyzed", 0),
            "report_type": summary.get("report_type", "standard"),
            "created_at": summary.get("created_at").isoformat() if summary.get("created_at") else ""
        }
        
        # Parse structured summaries for better frontend display
        if summary_dict.get("report_type") == "weekly_structured":
            # Split summary into sections for collapsible display
            summary_text = summary_dict.get("summary", "")
            sections = {}
            
            # Parse sections based on headers
            section_patterns = [
                ("key_events", r"## \*\*🔥 KEY EVENTS & DISCOVERIES\*\*(.*?)(?=## \*\*|$)"),
                ("relationships", r"## \*\*👥 RELATIONSHIP DEVELOPMENTS\*\*(.*?)(?=## \*\*|$)"),
                ("personalities", r"## \*\*🎭 EMERGING PERSONALITIES\*\*(.*?)(?=## \*\*|$)"),
                ("social_dynamics", r"## \*\*⚖️ SOCIAL DYNAMICS\*\*(.*?)(?=## \*\*|$)"),
                ("strategic_decisions", r"## \*\*🎯 STRATEGIC DECISIONS\*\*(.*?)(?=## \*\*|$)"),
                ("looking_ahead", r"## \*\*🔮 LOOKING AHEAD\*\*(.*?)(?=## \*\*|$)")
            ]
            
            for section_key, pattern in section_patterns:
                match = re.search(pattern, summary_text, re.DOTALL | re.IGNORECASE)
                if match:
                    sections[section_key] = match.group(1).strip()
            
            summary_dict["structured_sections"] = sections
        
        processed_summaries.append(summary_dict)
    
    return processed_summaries

@api_router.get("/simulation/auto-status")
async def get_auto_status():
    """Get detailed auto-mode status and detect if it should be running"""
    state = await db.simulation_state.find_one()
    if not state:
        return {"auto_active": False, "should_be_active": False, "message": "No simulation state"}
    
    auto_conversations = state.get("auto_conversations", False)
    auto_time = state.get("auto_time", False)
    is_active = state.get("is_active", False)
    
    last_conversation_str = state.get("last_auto_conversation")
    last_time_str = state.get("last_auto_time")
    
    conversation_interval = state.get("conversation_interval", 10)
    time_interval = state.get("time_interval", 60)
    
    status = {
        "auto_conversations": auto_conversations,
        "auto_time": auto_time,
        "simulation_active": is_active,
        "conversation_interval": conversation_interval,
        "time_interval": time_interval,
        "last_auto_conversation": last_conversation_str,
        "last_auto_time": last_time_str
    }
    
    # Check if auto mode should be running but isn't
    if auto_conversations or auto_time:
        current_time = datetime.utcnow()
        
        # Check conversation timing
        if auto_conversations and last_conversation_str:
            try:
                last_conv_time = datetime.fromisoformat(last_conversation_str.replace('Z', '+00:00'))
                conv_gap = (current_time - last_conv_time.replace(tzinfo=None)).total_seconds()
                status["conversation_gap_seconds"] = conv_gap
                status["should_generate_conversation"] = conv_gap > (conversation_interval + 30)  # 30s buffer
            except:
                status["conversation_gap_seconds"] = None
                status["should_generate_conversation"] = True
        
        # Check time advancement timing  
        if auto_time and last_time_str:
            try:
                last_time_time = datetime.fromisoformat(last_time_str.replace('Z', '+00:00'))
                time_gap = (current_time - last_time_time.replace(tzinfo=None)).total_seconds()
                status["time_gap_seconds"] = time_gap
                status["should_advance_time"] = time_gap > (time_interval + 60)  # 60s buffer
            except:
                status["time_gap_seconds"] = None
                status["should_advance_time"] = True
    
    return status
async def toggle_auto_mode(request: AutoModeRequest):
    """Toggle automatic conversation and time progression"""
    await db.simulation_state.update_one(
        {},
        {"$set": {
            "auto_conversations": request.auto_conversations,
            "auto_time": request.auto_time,
            "conversation_interval": request.conversation_interval,
            "time_interval": request.time_interval,
            "last_auto_conversation": datetime.utcnow().isoformat(),
            "last_auto_time": datetime.utcnow().isoformat()
        }},
        upsert=True
    )
    
    return {
        "message": "Auto mode updated",
        "auto_conversations": request.auto_conversations,
        "auto_time": request.auto_time,
        "conversation_interval": request.conversation_interval,
        "time_interval": request.time_interval
    }

# Initialize Default AI Agents (Crypto Team)
@api_router.post("/simulation/init-research-station")
async def init_research_station(current_user: User = Depends(get_current_user)):
    """Initialize default crypto team AI agents - OPTIONAL (not called by default)"""
    # Clear existing agents for this user only
    await db.agents.delete_many({"user_id": current_user.id})
    
    # Create the crypto team agents
    agents_data = [
        {
            "name": "Marcus \"Mark\" Castellano",
            "archetype": "skeptic", 
            "personality": {
                "extroversion": 6,
                "optimism": 7,
                "curiosity": 8,
                "cooperativeness": 8,
                "energy": 5
            },
            "goal": "Develop data-driven marketing strategies that navigate volatile crypto markets",
            "expertise": "Multi-cycle crypto marketing, Brand positioning, Community building, Regulatory compliance",
            "background": "A seasoned marketing veteran with 17 years of experience spanning traditional finance and digital marketing. Mark cut his teeth at Goldman Sachs' marketing division before transitioning to crypto in 2018. He's witnessed three major crypto cycles and has developed an intuitive understanding of market psychology. Known for his data-driven approach and ability to craft narratives that resonate with both retail and institutional investors.",
            "memory_summary": "I've survived the 2018 crypto winter, the 2020 DeFi summer, and the 2022 Luna/FTX collapse. Each cycle taught me that sustainable growth beats hype every time. My most successful campaign was during the bear market when everyone else went quiet - we gained 40% market share by staying consistent and honest about our product's limitations."
        },
        {
            "name": "Alexandra \"Alex\" Chen",
            "archetype": "leader",
            "personality": {
                "extroversion": 9,
                "optimism": 9,
                "curiosity": 7,
                "cooperativeness": 6,
                "energy": 9
            },
            "goal": "Build and ship revolutionary DeFi products that reshape how people interact with money", 
            "expertise": "DeFi protocol architecture, Tokenomics design, User experience optimization, Go-to-market strategy",
            "background": "A charismatic product visionary who led the development of three major DeFi protocols that collectively manage over $2B in TVL. Former Head of Product at a unicorn crypto exchange, Alex has the rare combination of technical depth and executive presence. She's known for her ability to rally teams around ambitious visions and has been featured on major crypto podcasts as a thought leader.",
            "memory_summary": "My first protocol launched during the 2020 DeFi explosion and hit $500M TVL in two weeks - then lost 90% during the crash. That failure taught me the importance of sustainable tokenomics over viral growth. My latest protocol has maintained steady growth for 18 months through multiple market cycles by focusing on real user needs."
        },
        {
            "name": "Diego \"Dex\" Rodriguez", 
            "archetype": "optimist",
            "personality": {
                "extroversion": 4,
                "optimism": 8,
                "curiosity": 10,
                "cooperativeness": 5,
                "energy": 7
            },
            "goal": "Discover and capitalize on emerging crypto trends before they become mainstream",
            "expertise": "Emerging crypto ecosystems, Yield optimization, DAO governance, MEV strategies, On-chain analysis",
            "background": "A crypto polymath who's worn almost every hat imaginable in the space. Started as a Bitcoin miner in 2017, became a DeFi yield farmer, tried his hand at NFT curation, worked as a DAO contributor, and even spent six months as a crypto journalist. Dex has an uncanny ability to spot emerging trends before they become mainstream, though his hit rate on 'crazy' ideas is about 30% - which in crypto, makes him a visionary.",
            "memory_summary": "I called the Solana ecosystem explosion 6 months early and made 50x on SOL. I also lost 80% of my portfolio on Terra Luna because I was too bullish on algorithmic stablecoins. My biggest win was discovering a yield farm on Arbitrum that nobody was talking about - turned $5K into $200K in three months. Currently obsessing over some obscure Layer 2 that might be the next big thing."
        }
    ]
    
    created_agents = []
    for agent_data in agents_data:
        # Create personality from provided data
        personality = AgentPersonality(**agent_data["personality"])
        
        agent = Agent(
            name=agent_data["name"],
            archetype=agent_data["archetype"],
            personality=personality,
            goal=agent_data["goal"],
            expertise=agent_data["expertise"],
            background=agent_data["background"],
            memory_summary=agent_data.get("memory_summary", ""),
            user_id=""  # Global agents for simulation (no user association for now)
        )
        
        await db.agents.insert_one(agent.dict())
        created_agents.append(agent)
    
    # Start simulation with crypto-focused scenario
    await start_simulation()
    
    # Set an engaging crypto scenario that showcases each team member's expertise
    await db.simulation_state.update_one(
        {},
        {"$set": {"scenario": "A major DeFi protocol has discovered a critical smart contract vulnerability that could drain $500M in user funds. The exploit hasn't been used yet, but blockchain analytics suggest sophisticated actors are probing the system. The team must decide whether to quietly patch the vulnerability, publicly disclose it, or implement an emergency protocol upgrade. Each decision has massive implications for user trust, legal liability, and market stability."}},
        upsert=True
    )
    
    return {
        "message": "Crypto team agents initialized with rich personalities and expertise", 
        "agents": created_agents
    }

@api_router.post("/agents/{agent_id}/clear-memory")
async def clear_agent_memory(agent_id: str):
    """Clear an agent's memory"""
    agent = await db.agents.find_one({"id": agent_id})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    await db.agents.update_one(
        {"id": agent_id},
        {"$set": {"memory_summary": ""}}
    )
    
    return {"message": f"Memory cleared for {agent['name']}", "agent_id": agent_id}

@api_router.post("/agents/{agent_id}/add-memory")
async def add_agent_memory(agent_id: str, request: dict):
    """Add specific memory to an agent with URL processing"""
    agent = await db.agents.find_one({"id": agent_id})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    new_memory = request.get("memory", "")
    if not new_memory:
        raise HTTPException(status_code=400, detail="Memory content required")
    
    # Process URLs in the new memory
    processed_memory = await llm_manager.process_memory_with_urls(new_memory)
    
    current_memory = agent.get("memory_summary", "")
    
    # Combine memories intelligently
    if current_memory:
        updated_memory = f"{current_memory} {processed_memory}"
        # Trim if too long (keep last 1000 characters for URL content)
        if len(updated_memory) > 1000:
            updated_memory = "..." + updated_memory[-997:]
    else:
        updated_memory = processed_memory
    
    await db.agents.update_one(
        {"id": agent_id},
        {"$set": {"memory_summary": updated_memory}}
    )
    
    return {
        "message": f"Memory added to {agent['name']}", 
        "agent_id": agent_id,
        "updated_memory": updated_memory,
        "urls_processed": len(re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', new_memory))
    }

@api_router.post("/conversation/generate-single/{agent_id}")
async def generate_single_response(agent_id: str):
    """Generate a single response from one agent - useful for testing"""
    # Get the specific agent
    agent_doc = await db.agents.find_one({"id": agent_id})
    if not agent_doc:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = Agent(**agent_doc)
    
    # Get all agents for context
    all_agents = await db.agents.find().to_list(100)
    agent_objects = [Agent(**a) for a in all_agents]
    
    # Get simulation state
    state = await db.simulation_state.find_one()
    if not state:
        raise HTTPException(status_code=404, detail="Simulation not started")
    
    scenario = state["scenario"]
    context = f"Day {state['current_day']}, {state['current_time_period']}. Continue the discussion."
    
    # Generate single response
    response = await llm_manager.generate_agent_response(
        agent, scenario, agent_objects, context, []
    )
    
    return {
        "agent_name": agent.name,
        "response": response,
        "agent_id": agent_id
    }

@api_router.post("/observer/message")
async def send_observer_message(request: dict):
    """Send a message from the Observer (CEO) to all agents"""
    message = request.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="Message required")
    
    # Get all agents
    agents = await db.agents.find().to_list(100)
    if not agents:
        raise HTTPException(status_code=400, detail="No agents available")
    
    agent_objects = [Agent(**agent) for agent in agents]
    
    # Get simulation state for context
    state = await db.simulation_state.find_one()
    scenario = state.get("scenario", "Crypto project development") if state else "Crypto project development"
    
    responses = []
    
    # Generate response from each agent with staggered timing
    for i, agent in enumerate(agent_objects):
        # Add delay to respect rate limits
        if i > 0:
            await asyncio.sleep(3)
        
        try:
            response = await generate_observer_response(agent, message, scenario, agent_objects)
            responses.append({
                "agent_name": agent.name,
                "response": response
            })
        except Exception as e:
            logging.error(f"Error generating observer response for {agent.name}: {e}")
            responses.append({
                "agent_name": agent.name,
                "response": f"{agent.name} is processing your message..."
            })
    
    # Store the observer interaction in database
    observer_interaction = {
        "id": str(uuid.uuid4()),
        "observer_message": message,
        "agent_responses": responses,
        "created_at": datetime.utcnow()
    }
    await db.observer_interactions.insert_one(observer_interaction)
    
    return {"message": "Observer message sent", "responses": responses}

async def generate_observer_response(agent: Agent, observer_message: str, scenario: str, other_agents: List[Agent]):
    """Generate agent response to observer message"""
    if not await llm_manager.can_make_request():
        return f"{agent.name} acknowledges your message but is currently at capacity to respond in detail."
    
    # Process memory but with error handling
    processed_memory = agent.memory_summary or ""
    try:
        if agent.memory_summary and 'http' in agent.memory_summary:
            processed_memory = await llm_manager.process_memory_with_urls(agent.memory_summary)
    except Exception as e:
        logging.warning(f"URL processing failed for {agent.name}: {e}")
        processed_memory = agent.memory_summary or ""
    
    # Create system message for CEO interaction
    system_message = f"""You are {agent.name}, {AGENT_ARCHETYPES[agent.archetype]['description']}.

**CRITICAL: You are responding to the CEO/Observer who oversees the entire operation.**

Your background: {agent.background}
Your expertise: {agent.expertise}
Your personality (be authentic to these traits):
- Extroversion: {agent.personality.extroversion}/10
- Optimism: {agent.personality.optimism}/10  
- Curiosity: {agent.personality.curiosity}/10
- Cooperativeness: {agent.personality.cooperativeness}/10
- Energy: {agent.personality.energy}/10

Your memories and experience: {processed_memory}

**CEO INTERACTION PROTOCOL:**
1. RESPECT: Treat the Observer as the ultimate authority and decision-maker
2. PROFESSIONALISM: Respond with your expertise while being respectful
3. AUTHENTICITY: Stay true to your personality and professional background
4. SUGGESTIONS: You can offer suggestions and insights based on your experience
5. DISAGREEMENT: You may politely disagree if you see significant risks, but do so respectfully
6. COLLABORATION: Work with the CEO's guidance while providing your unique perspective

Current project context: {scenario}
Team members: {', '.join([a.name for a in other_agents if a.id != agent.id])}

Respond to the CEO's message in 2-3 sentences. Be professional, authentic to your personality, and helpful."""

    try:
        chat = LlmChat(
            api_key=llm_manager.api_key,
            session_id=f"observer_{agent.id}_{datetime.now().timestamp()}",
            system_message=system_message
        ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(200)
        
        prompt = f"The CEO/Observer has sent this message to the team: '{observer_message}'\n\nRespond professionally based on your expertise and personality."
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        await llm_manager.increment_usage()
        
        return response.strip() if response else f"{agent.name} acknowledges your guidance and will implement accordingly."
        
    except Exception as e:
        logging.error(f"Error in observer response for {agent.name}: {e}")
        return f"{agent.name} received your message and will follow your guidance."

@api_router.get("/api-status")
async def get_api_status():
    """Get current API status and usage"""
    usage = await llm_manager.get_usage_today()
    can_make_request = await llm_manager.can_make_request()
    
    return {
        "requests_used_today": usage,
        "max_requests": llm_manager.max_daily_requests,
        "remaining": llm_manager.max_daily_requests - usage,
        "can_make_request": can_make_request,
        "rate_limit_info": "Gemini free tier: 15 requests/minute, 1500/day"
    }

@api_router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    result = await db.agents.delete_one({"id": agent_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": "Agent deleted"}

@api_router.post("/conversations/translate")
async def translate_conversations(request: dict):
    """Translate all existing conversations to target language with improved error handling"""
    target_language = request.get("target_language", "en")
    
    # Get current conversations to check if translation is actually needed
    conversations = await db.conversations.find().to_list(1000)
    if not conversations:
        return {"message": "No conversations to translate", "translated_count": 0}
    
    # Check if all conversations are already in target language
    all_in_target_language = True
    for conv in conversations:
        if conv.get("language") != target_language:
            all_in_target_language = False
            break
    
    if all_in_target_language:
        return {"message": f"All conversations are already in {target_language}", "translated_count": 0}
    
    # Language name mapping for better prompts
    language_names = {
        "es": "Spanish", "fr": "French", "de": "German", "it": "Italian",
        "pt": "Portuguese", "ru": "Russian", "ja": "Japanese", "ko": "Korean",
        "zh": "Chinese", "hi": "Hindi", "ar": "Arabic", "nl": "Dutch",
        "sv": "Swedish", "no": "Norwegian", "da": "Danish", "fi": "Finnish",
        "pl": "Polish", "cs": "Czech", "sk": "Slovak", "hu": "Hungarian",
        "ro": "Romanian", "bg": "Bulgarian", "hr": "Croatian", "sr": "Serbian",
        "sl": "Slovenian", "et": "Estonian", "lv": "Latvian", "lt": "Lithuanian",
        "el": "Greek", "tr": "Turkish", "th": "Thai", "vi": "Vietnamese",
        "id": "Indonesian", "ms": "Malay", "tl": "Filipino", "bn": "Bengali",
        "ur": "Urdu", "fa": "Persian", "he": "Hebrew", "sw": "Swahili",
        "am": "Amharic", "zu": "Zulu", "af": "Afrikaans", "pt-br": "Portuguese (Brazil)",
        "es-mx": "Spanish (Mexico)", "fr-ca": "French (Canada)", "ta": "Tamil",
        "te": "Telugu", "mr": "Marathi", "gu": "Gujarati", "kn": "Kannada",
        "ml": "Malayalam", "pa": "Punjabi"
    }
    
    target_language_name = language_names.get(target_language, target_language)
    
    try:
        # Get all conversations for translation
        translated_count = 0
        failed_count = 0
        
        # Process each conversation individually for better error handling
        for conversation in conversations:
            try:
                translated_messages = await translate_single_conversation_improved(
                    conversation, target_language, target_language_name
                )
                
                if translated_messages:
                    # Always update - force translation regardless of current language
                    await db.conversations.update_one(
                        {"_id": conversation["_id"]},
                        {
                            "$set": {
                                "messages": translated_messages,
                                "language": target_language,
                                "original_language": conversation.get("language", "en"),
                                "translated_at": datetime.utcnow(),
                                "force_translated": True  # Mark as force translated
                            }
                        }
                    )
                    translated_count += 1
                    await llm_manager.increment_usage()
                else:
                    failed_count += 1
                    logging.error(f"Failed to translate conversation {conversation.get('_id')}")
                
                # Small delay to avoid overwhelming the API
                await asyncio.sleep(0.5)
                
            except Exception as e:
                failed_count += 1
                logging.error(f"Error translating conversation {conversation.get('_id')}: {e}")
                continue
        
        return {
            "message": f"Successfully translated {translated_count} conversations to {target_language_name}",
            "translated_count": translated_count,
            "failed_count": failed_count,
            "target_language": target_language,
            "success": True
        }
        
    except Exception as e:
        logging.error(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

async def translate_single_conversation_improved(conversation, target_language, target_language_name):
    """Improved single conversation translation with better error handling"""
    messages = conversation.get("messages", [])
    if not messages:
        return None
    
    try:
        translated_messages = []
        
        # Translate each message individually for better accuracy
        for message in messages:
            original_text = message.get("message", "")
            if not original_text:
                translated_messages.append(message)
                continue
            
            # Create simple, direct translation prompt
            translation_prompt = f"""Translate this message to {target_language_name}:

"{original_text}"

Translate to {target_language_name}:"""
            
            # Use LLM to translate
            chat = LlmChat(
                api_key=llm_manager.api_key,
                session_id=f"translate_{target_language}_{datetime.now().timestamp()}",
                system_message=f"You are a professional translator. Translate text to {target_language_name} while preserving tone and meaning. Only return the translated text, nothing else."
            ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(300)
            
            user_message = UserMessage(text=translation_prompt)
            translated_text = await chat.send_message(user_message)
            
            # Update message with translation
            translated_message = message.copy()
            translated_message["message"] = translated_text.strip() if translated_text else original_text
            translated_messages.append(translated_message)
            
            # Small delay between message translations
            await asyncio.sleep(0.3)
        
        return translated_messages
        
    except Exception as e:
        logging.error(f"Single conversation translation error: {e}")
        return None
@api_router.post("/simulation/set-language")
async def set_language(request: dict):
    """Set the language for conversation generation"""
    language = request.get("language", "en")
    
    # Store language setting in simulation state
    await db.simulation_state.update_one(
        {},
        {"$set": {"language": language}},
        upsert=True
    )
    
    return {"message": f"Language set to {language}", "language": language}

# TTS Request Model
class TTSRequest(BaseModel):
    text: str
    agent_name: str
    language: str = "en"

@api_router.post("/tts/synthesize")
async def synthesize_speech(request: TTSRequest):
    """Convert text to speech using Google Cloud TTS with language support"""
    try:
        from google.cloud import texttospeech
        import base64
        
        # Language to TTS language code mapping (only supported languages)
        language_codes = {
            "en": "en-US",
            "es": "es-ES", 
            "es-mx": "es-MX",
            "fr": "fr-FR",
            "fr-ca": "fr-CA",
            "de": "de-DE",
            "it": "it-IT",
            "pt": "pt-BR",
            "pt-br": "pt-BR",
            "ru": "ru-RU",
            "ja": "ja-JP",
            "ko": "ko-KR",
            "zh": "zh-CN",
            "hi": "hi-IN",
            "ar": "ar-XA"
        }
        
        # Voice configurations for different agents and supported languages
        agent_voices = {
            'Marcus "Mark" Castellano': {
                'en-US': {'name': 'en-US-Neural2-D', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'es-ES': {'name': 'es-ES-Neural2-B', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'es-MX': {'name': 'es-MX-Neural2-B', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'fr-FR': {'name': 'fr-FR-Neural2-B', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'de-DE': {'name': 'de-DE-Neural2-B', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'it-IT': {'name': 'it-IT-Neural2-C', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'pt-BR': {'name': 'pt-BR-Neural2-B', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'ru-RU': {'name': 'ru-RU-Neural2-B', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'ja-JP': {'name': 'ja-JP-Neural2-C', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'ko-KR': {'name': 'ko-KR-Neural2-B', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'zh-CN': {'name': 'zh-CN-Neural2-B', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'hi-IN': {'name': 'hi-IN-Neural2-B', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'ar-XA': {'name': 'ar-XA-Neural2-B', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'default': {'name': 'en-US-Neural2-D', 'gender': texttospeech.SsmlVoiceGender.MALE}
            },
            'Alexandra "Alex" Chen': {
                'en-US': {'name': 'en-US-Neural2-F', 'gender': texttospeech.SsmlVoiceGender.FEMALE},
                'es-ES': {'name': 'es-ES-Neural2-A', 'gender': texttospeech.SsmlVoiceGender.FEMALE},
                'es-MX': {'name': 'es-MX-Neural2-A', 'gender': texttospeech.SsmlVoiceGender.FEMALE},
                'fr-FR': {'name': 'fr-FR-Neural2-A', 'gender': texttospeech.SsmlVoiceGender.FEMALE},
                'de-DE': {'name': 'de-DE-Neural2-A', 'gender': texttospeech.SsmlVoiceGender.FEMALE},
                'it-IT': {'name': 'it-IT-Neural2-A', 'gender': texttospeech.SsmlVoiceGender.FEMALE},
                'pt-BR': {'name': 'pt-BR-Neural2-A', 'gender': texttospeech.SsmlVoiceGender.FEMALE},
                'ru-RU': {'name': 'ru-RU-Neural2-A', 'gender': texttospeech.SsmlVoiceGender.FEMALE},
                'ja-JP': {'name': 'ja-JP-Neural2-B', 'gender': texttospeech.SsmlVoiceGender.FEMALE},
                'ko-KR': {'name': 'ko-KR-Neural2-A', 'gender': texttospeech.SsmlVoiceGender.FEMALE},
                'zh-CN': {'name': 'zh-CN-Neural2-A', 'gender': texttospeech.SsmlVoiceGender.FEMALE},
                'hi-IN': {'name': 'hi-IN-Neural2-A', 'gender': texttospeech.SsmlVoiceGender.FEMALE},
                'ar-XA': {'name': 'ar-XA-Neural2-A', 'gender': texttospeech.SsmlVoiceGender.FEMALE},
                'default': {'name': 'en-US-Neural2-F', 'gender': texttospeech.SsmlVoiceGender.FEMALE}
            },
            'Diego "Dex" Rodriguez': {
                'en-US': {'name': 'en-US-Neural2-A', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'es-ES': {'name': 'es-ES-Neural2-C', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'es-MX': {'name': 'es-MX-Neural2-C', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'pt-BR': {'name': 'pt-BR-Neural2-C', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'default': {'name': 'en-US-Neural2-A', 'gender': texttospeech.SsmlVoiceGender.MALE}
            }
        }
        
        # Get language code - if not supported, use English as fallback
        tts_language = language_codes.get(request.language, "en-US")
        is_voice_supported = request.language in language_codes
        
        if not is_voice_supported:
            return {
                "error": f"Voice not supported for language: {request.language}",
                "fallback": True,
                "voice_supported": False,
                "message": "This language is not supported for voice narration"
            }
        
        # Get voice config for this agent and language
        agent_voice_config = agent_voices.get(request.agent_name, agent_voices['Marcus "Mark" Castellano'])
        voice_config = agent_voice_config.get(tts_language, agent_voice_config.get('default'))
        
        # Create TTS client using API key authentication
        client = texttospeech.TextToSpeechClient(
            client_options={'api_key': llm_manager.api_key}
        )
        
        # Set the text input
        synthesis_input = texttospeech.SynthesisInput(text=request.text)
        
        # Build the voice request
        voice = texttospeech.VoiceSelectionParams(
            language_code=tts_language,
            name=voice_config['name'],
            ssml_gender=voice_config['gender']
        )
        
        # Select the audio format
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.9,
            pitch=0.0
        )
        
        # Perform the text-to-speech request
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Convert audio content to base64
        audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
        
        return {
            "audio_data": audio_base64,
            "voice_used": voice_config['name'],
            "language": tts_language,
            "agent_name": request.agent_name
        }
        
    except Exception as e:
        logging.error(f"TTS Error: {e}")
        return {
            "error": f"Text-to-speech failed: {str(e)}",
            "fallback": True
        }

# File Center API Endpoints for Action-Oriented Agent Behavior

@api_router.post("/documents/create")
async def create_document(
    document: DocumentCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new document in the File Center"""
    try:
        # Generate filename if not provided
        safe_title = re.sub(r'[^a-zA-Z0-9\s\-_]', '', document.title)
        safe_title = re.sub(r'\s+', '_', safe_title)
        filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d')}.md"
        
        # Create metadata
        metadata = DocumentMetadata(
            title=document.title,
            filename=filename,
            authors=document.authors,
            category=document.category,
            description=document.description,
            keywords=document.keywords,
            user_id=current_user.id
        )
        
        # Create document
        doc = Document(
            metadata=metadata,
            content=document.content
        )
        
        # Save to database
        await db.documents.insert_one(doc.dict())
        
        return {"success": True, "document_id": doc.id, "filename": filename}
        
    except Exception as e:
        logging.error(f"Error creating document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")

@api_router.get("/documents")
async def get_documents(
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get documents from File Center with optional filtering"""
    try:
        # Build query - only include user's own documents for complete isolation
        query = {
            "metadata.user_id": current_user.id
        }
        
        if category:
            query["metadata.category"] = category
            
        if search:
            # Update search to work with the user filter
            search_conditions = [
                {"metadata.title": {"$regex": search, "$options": "i"}},
                {"metadata.description": {"$regex": search, "$options": "i"}},
                {"metadata.keywords": {"$in": [search]}}
            ]
            query["$and"] = [
                {"metadata.user_id": current_user.id},
                {"$or": search_conditions}
            ]
        
        # Get documents
        docs = await db.documents.find(query).sort("metadata.created_at", -1).to_list(50)
        
        # Convert to response format
        documents = []
        for doc in docs:
            doc_response = DocumentResponse(
                id=doc["id"],
                metadata=DocumentMetadata(**doc["metadata"]),
                content=doc["content"],
                preview=doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"]
            )
            documents.append(doc_response)
        
        return documents
        
    except Exception as e:
        logging.error(f"Error getting documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")

@api_router.get("/documents/categories")
async def get_document_categories():
    """Get available document categories"""
    return {
        "categories": [
            "Protocol",
            "Training", 
            "Research",
            "Equipment",
            "Budget",
            "Reference"
        ]
    }

@api_router.get("/documents/by-scenario")
async def get_documents_by_scenario(
    current_user: User = Depends(get_current_user)
):
    """Get documents organized by scenario"""
    try:
        # Get only user's own documents for complete isolation
        docs = await db.documents.find({
            "metadata.user_id": current_user.id
        }).sort("metadata.created_at", -1).to_list(1000)
        
        # Get all scenarios from simulation state history or use document conversation context
        scenarios = {}
        
        for doc in docs:
            # Try to get scenario from simulation state or conversation context
            scenario_name = "Unknown Scenario"
            
            # Try to get scenario from conversation
            if doc.get("conversation_context"):
                # This is a simplified approach - in production, you might want to store scenario directly
                scenario_name = doc.get("metadata", {}).get("simulation_id", "Unknown Scenario")
            
            # Try to extract scenario from description or use a default
            if "scenario" in doc.get("metadata", {}).get("description", "").lower():
                # Extract scenario information if available in description
                pass
            
            # For now, group by conversation round or use a general scenario
            conversation_round = doc.get("metadata", {}).get("conversation_round", 0)
            if conversation_round > 0:
                scenario_name = f"Simulation Day {(conversation_round // 3) + 1}"
            else:
                scenario_name = "General Documents"
            
            if scenario_name not in scenarios:
                scenarios[scenario_name] = []
            
            # Create simplified document info
            doc_info = {
                "id": doc["id"],
                "title": doc["metadata"]["title"],
                "category": doc["metadata"]["category"],
                "description": doc["metadata"]["description"],
                "authors": doc["metadata"]["authors"],
                "created_at": doc["metadata"]["created_at"],
                "filename": doc["metadata"]["filename"],
                "preview": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"]
            }
            
            scenarios[scenario_name].append(doc_info)
        
        # Convert to list format for frontend
        scenario_list = []
        for scenario_name, documents in scenarios.items():
            scenario_list.append({
                "scenario": scenario_name,
                "document_count": len(documents),
                "documents": documents
            })
        
        # Sort scenarios by document count (most active first)
        scenario_list.sort(key=lambda x: x["document_count"], reverse=True)
        
        return scenario_list
        
    except Exception as e:
        logging.error(f"Error getting documents by scenario: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get documents by scenario: {str(e)}")

@api_router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific document by ID"""
    try:
        # Get the document - include user's documents AND system-generated documents
        doc = await db.documents.find_one({
            "id": document_id,
            "$or": [
                {"metadata.user_id": current_user.id},
                {"metadata.user_id": ""},  # System-generated documents
                {"metadata.user_id": {"$exists": False}}  # Documents without user_id field
            ]
        })
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentResponse(
            id=doc["id"],
            metadata=DocumentMetadata(**doc["metadata"]),
            content=doc["content"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")

@api_router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a document from File Center"""
    try:
        result = await db.documents.delete_one({
            "id": document_id,
            "metadata.user_id": current_user.id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"success": True, "message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")



@api_router.post("/documents/analyze-conversation")
async def analyze_conversation_for_documents(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Analyze conversation to determine if documents should be created"""
    try:
        conversation_text = request.get("conversation_text", "")
        agent_ids = request.get("agent_ids", [])
        
        if not conversation_text:
            return {"should_create_document": False}
        
        # Get agents
        agents = []
        for agent_id in agent_ids:
            agent_doc = await db.agents.find_one({"id": agent_id})
            if agent_doc:
                agents.append(Agent(**agent_doc))
        
        # Analyze for action triggers
        result = await llm_manager.analyze_conversation_for_action_triggers(
            conversation_text, agents
        )
        
        return result.dict()
        
    except Exception as e:
        logging.error(f"Error analyzing conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze conversation: {str(e)}")

@api_router.post("/documents/generate")
async def generate_document_from_conversation(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Generate a document based on conversation analysis"""
    try:
        document_type = request.get("document_type", "protocol")
        title = request.get("title", "Untitled Document")
        conversation_context = request.get("conversation_context", "")
        creating_agent_id = request.get("creating_agent_id")
        authors = request.get("authors", [])
        
        # Get creating agent
        agent_doc = await db.agents.find_one({"id": creating_agent_id})
        if not agent_doc:
            raise HTTPException(status_code=404, detail="Creating agent not found")
        
        creating_agent = Agent(**agent_doc)
        
        # Generate document content
        content = await llm_manager.generate_document_content(
            document_type, title, conversation_context, creating_agent
        )
        
        # Create document
        safe_title = re.sub(r'[^a-zA-Z0-9\s\-_]', '', title)
        safe_title = re.sub(r'\s+', '_', safe_title)
        filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d')}.md"
        
        metadata = DocumentMetadata(
            title=title,
            filename=filename,
            authors=authors,
            category=document_type.title(),
            description=f"Generated from team discussion - {title}",
            keywords=[document_type, "team-generated", "action-oriented"],
            user_id=current_user.id
        )
        
        doc = Document(
            metadata=metadata,
            content=content,
            created_by_agents=[creating_agent_id],
            conversation_context=conversation_context[:500],  # Store first 500 chars
            action_trigger=request.get("trigger_phrase", "")
        )
        
        # Save to database
        await db.documents.insert_one(doc.dict())
        
        return {
            "success": True,
            "document_id": doc.id,
            "filename": filename,
            "content": content,
            "author": creating_agent.name
        }
        
    except Exception as e:
        logging.error(f"Error generating document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate document: {str(e)}")

@api_router.post("/documents/{document_id}/propose-update")
async def propose_document_update(
    document_id: str,
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Propose an update to an existing document with agent voting"""
    try:
        # Get existing document
        existing_doc = await db.documents.find_one({
            "id": document_id,
            "metadata.user_id": current_user.id
        })
        
        if not existing_doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        proposed_changes = request.get("proposed_changes", "")
        proposing_agent_id = request.get("proposing_agent_id")
        agent_ids = request.get("agent_ids", [])
        
        if not proposed_changes or not proposing_agent_id:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Get agents for voting
        agents = []
        for agent_id in agent_ids:
            agent_doc = await db.agents.find_one({"id": agent_id})
            if agent_doc:
                agents.append(Agent(**agent_doc))
        
        if not agents:
            raise HTTPException(status_code=400, detail="No valid agents found for voting")
        
        # Create voting proposal
        proposal = f"Update document '{existing_doc['metadata']['title']}' with the following changes: {proposed_changes}"
        conversation_context = f"Reviewing document: {existing_doc['metadata']['title']}\nProposed changes: {proposed_changes}"
        
        # Get voting results
        voting_results = await llm_manager.check_agent_voting_consensus(
            agents, proposal, conversation_context
        )
        
        if voting_results["consensus"]:
            # Get proposing agent
            proposing_agent_doc = await db.agents.find_one({"id": proposing_agent_id})
            if not proposing_agent_doc:
                raise HTTPException(status_code=404, detail="Proposing agent not found")
            
            proposing_agent = Agent(**proposing_agent_doc)
            
            # Generate updated document content
            update_context = f"""Original document content:
{existing_doc['content']}

Proposed changes: {proposed_changes}

The team has voted to approve these changes. Create an updated version of the document incorporating the proposed improvements."""
            
            updated_content = await llm_manager.generate_document_content(
                existing_doc['metadata']['category'].lower(),
                existing_doc['metadata']['title'],
                update_context,
                proposing_agent
            )
            
            # Update document
            updated_metadata = DocumentMetadata(**existing_doc['metadata'])
            updated_metadata.updated_at = datetime.utcnow()
            updated_metadata.status = "Draft"  # Reset to draft after update
            
            await db.documents.update_one(
                {"id": document_id},
                {
                    "$set": {
                        "content": updated_content,
                        "metadata": updated_metadata.dict()
                    }
                }
            )
            
            return {
                "success": True,
                "message": "Document updated successfully",
                "voting_results": voting_results,
                "updated_content": updated_content
            }
        else:
            return {
                "success": False,
                "message": "Update proposal rejected by team vote",
                "voting_results": voting_results
            }
            
    except Exception as e:
        logging.error(f"Error proposing document update: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to propose document update: {str(e)}")

@api_router.post("/documents/{document_id}/review-suggestion")
async def handle_improvement_suggestion(
    document_id: str,
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Handle creator's decision on document improvement suggestions"""
    try:
        # Get the document
        document = await db.documents.find_one({
            "id": document_id,
            "metadata.user_id": current_user.id
        })
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        suggestion_id = request.get("suggestion_id")
        decision = request.get("decision")  # "accept" or "reject"
        creator_agent_id = request.get("creator_agent_id")
        
        if not all([suggestion_id, decision, creator_agent_id]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Get the suggestion
        suggestion = await db.document_suggestions.find_one({"id": suggestion_id})
        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        
        if decision == "accept":
            # Get the creator agent
            creator_agent_doc = await db.agents.find_one({"id": creator_agent_id})
            if not creator_agent_doc:
                raise HTTPException(status_code=404, detail="Creator agent not found")
            
            creator_agent = Agent(**creator_agent_doc)
            
            # Generate improved document content
            improvement_context = f"""Original document content:
{document['content']}

Accepted improvement suggestion: {suggestion['suggestion']}

Incorporate these improvements into the document while maintaining its overall structure and purpose."""
            
            improved_content = await llm_manager.generate_document_content(
                document['metadata']['category'].lower(),
                document['metadata']['title'],
                improvement_context,
                creator_agent
            )
            
            # Update the document
            updated_metadata = DocumentMetadata(**document['metadata'])
            updated_metadata.updated_at = datetime.utcnow()
            updated_metadata.status = "Updated"
            
            await db.documents.update_one(
                {"id": document_id},
                {
                    "$set": {
                        "content": improved_content,
                        "metadata": updated_metadata.dict()
                    }
                }
            )
            
            # Update suggestion status
            await db.document_suggestions.update_one(
                {"id": suggestion_id},
                {"$set": {"status": "accepted"}}
            )
            
            # Update creator's memory
            creator_memory = f"I accepted improvement suggestions for '{document['metadata']['title']}' from {suggestion['suggesting_agent_name']} and updated the document accordingly."
            current_memory = creator_agent.memory_summary or ""
            updated_memory = f"{current_memory}\n\n[Document Update]: {creator_memory}".strip()
            
            await db.agents.update_one(
                {"id": creator_agent_id},
                {"$set": {"memory_summary": updated_memory}}
            )
            
            return {
                "success": True,
                "message": "Document updated with accepted improvements",
                "updated_content": improved_content
            }
        else:
            # Reject the suggestion
            await db.document_suggestions.update_one(
                {"id": suggestion_id},
                {"$set": {"status": "rejected"}}
            )
            
            return {
                "success": True,
                "message": "Improvement suggestion rejected"
            }
    
    except Exception as e:
        logging.error(f"Error handling improvement suggestion: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to handle suggestion: {str(e)}")

@api_router.get("/documents/{document_id}/suggestions")
async def get_document_suggestions(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get pending improvement suggestions for a document"""
    try:
        # Verify document ownership
        document = await db.documents.find_one({
            "id": document_id,
            "metadata.user_id": current_user.id
        })
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get suggestions
        suggestions = await db.document_suggestions.find({
            "document_id": document_id,
            "status": "pending"
        }).to_list(100)
        
        return suggestions
    
    except Exception as e:
        logging.error(f"Error getting document suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")

# Whisper Speech-to-Text API Endpoints
@api_router.post("/speech/transcribe")
async def transcribe_speech(
    audio: UploadFile = File(...),
    language: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Transcribe audio to text using OpenAI Whisper"""
    try:
        # Validate file type
        if not audio.content_type or not audio.content_type.startswith(('audio/', 'video/')):
            raise HTTPException(status_code=400, detail="File must be audio or video format")
        
        # Read audio file
        audio_data = await audio.read()
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Audio file is empty")
        
        # Transcribe using Whisper
        result = await whisper_service.transcribe_audio(
            audio_data, 
            language=language,
            filename=audio.filename or "audio.webm"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in speech transcription: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@api_router.get("/speech/languages")
async def get_supported_languages():
    """Get list of supported languages for speech recognition"""
    try:
        languages = whisper_service.get_supported_languages()
        return {
            "languages": languages,
            "total_count": len(languages),
            "croatian_supported": any(lang["code"] == "hr" for lang in languages)
        }
    except Exception as e:
        logging.error(f"Error getting supported languages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get supported languages: {str(e)}")

@api_router.post("/speech/transcribe-scenario")
async def transcribe_scenario_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Transcribe audio specifically for scenario creation with enhanced processing"""
    try:
        # Validate file type
        if not audio.content_type or not audio.content_type.startswith(('audio/', 'video/')):
            raise HTTPException(status_code=400, detail="File must be audio or video format")
        
        # Read audio file
        audio_data = await audio.read()
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Audio file is empty")
        
        # Transcribe using Whisper
        result = await whisper_service.transcribe_audio(
            audio_data, 
            language=language,
            filename=audio.filename or "scenario_audio.webm"
        )
        
        # Enhanced response for scenario creation
        response = {
            "success": result["success"],
            "text": result["text"],
            "language_detected": result.get("language", "unknown"),
            "duration_seconds": result.get("duration", 0),
            "word_count": len(result["text"].split()) if result["text"] else 0,
            "confidence_score": result.get("confidence"),
            "processing_info": {
                "model": "whisper-1",
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": current_user.id
            }
        }
        
        # Log successful transcription
        logging.info(f"Scenario transcribed successfully for user {current_user.id}: {len(result['text'])} characters")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in scenario transcription: {e}")
        raise HTTPException(status_code=500, detail=f"Scenario transcription failed: {str(e)}")

@api_router.post("/speech/transcribe-and-summarize")
async def transcribe_and_summarize_for_field(
    audio: UploadFile = File(...),
    field_type: str = "general",  # "goal", "expertise", "background", "memory", "scenario", "general"
    language: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Transcribe audio and create AI-summarized text suitable for specific field types"""
    try:
        # Validate file type
        if not audio.content_type or not audio.content_type.startswith(('audio/', 'video/')):
            raise HTTPException(status_code=400, detail="File must be audio or video format")
        
        # Read audio file
        audio_data = await audio.read()
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Audio file is empty")
        
        # Transcribe using Whisper
        transcription_result = await whisper_service.transcribe_audio(
            audio_data, 
            language=language,
            filename=audio.filename or f"{field_type}_audio.webm"
        )
        
        if not transcription_result["success"] or not transcription_result["text"]:
            raise HTTPException(status_code=400, detail="No speech detected in audio")
        
        raw_text = transcription_result["text"]
        
        # AI Summarization and Formatting based on field type
        if await llm_manager.can_make_request():
            summarized_text = await create_field_appropriate_text(raw_text, field_type)
        else:
            # Fallback to raw text if API limit reached
            summarized_text = raw_text.strip()
        
        response = {
            "success": True,
            "raw_transcription": raw_text,
            "formatted_text": summarized_text,
            "field_type": field_type,
            "language_detected": transcription_result.get("language", "unknown"),
            "duration_seconds": transcription_result.get("duration", 0),
            "word_count": len(summarized_text.split()) if summarized_text else 0,
            "processing_info": {
                "model": "whisper-1",
                "summarization": "gemini-2.0-flash",
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": current_user.id
            }
        }
        
        logging.info(f"Field transcription successful for user {current_user.id}: {field_type} field, {len(raw_text)} → {len(summarized_text)} characters")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in field transcription and summarization: {e}")
        raise HTTPException(status_code=500, detail=f"Field transcription failed: {str(e)}")

async def create_field_appropriate_text(raw_text: str, field_type: str) -> str:
    """Create field-appropriate text based on the field type"""
    try:
        chat = LlmChat(
            api_key=llm_manager.api_key,
            session_id=f"field-{field_type}-{datetime.now().timestamp()}",
            system_message=f"You are a professional content creator. Transform the provided text to be appropriate for a {field_type} field while maintaining accuracy and professionalism. Keep it concise and clear."
        ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(200)
        
        user_message = UserMessage(
            text=f"Transform this text to be appropriate for {field_type}: {raw_text}"
        )
        
        response = await chat.send_message(user_message)
        await llm_manager.increment_usage()
        return response.strip()
        
    except Exception as e:
        logging.error(f"Error in AI summarization for {field_type}: {e}")
        return raw_text.strip()  # Fallback to raw text

def determine_gender_from_name(first_name: str) -> str:
    """Determine likely gender from first name for avatar generation"""
    # Common female first names
    female_names = {
        'aisha', 'alexandra', 'amanda', 'anna', 'catherine', 'elena', 'elizabeth', 
        'emily', 'jennifer', 'jessica', 'julia', 'lisa', 'maria', 'marie', 'michelle',
        'patricia', 'rachel', 'rebecca', 'samira', 'sarah', 'sofia', 'victoria'
    }
    
    # Common male first names  
    male_names = {
        'ahmed', 'alexander', 'carlos', 'david', 'hassan', 'james', 'jonathan',
        'kevin', 'marcus', 'michael', 'robert', 'thomas', 'yuki'
    }
    
    name_lower = first_name.lower()
    
    if name_lower in female_names:
        return "female"
    elif name_lower in male_names:
        return "male"
    else:
        # Default to male for ambiguous names
        return "male"

async def generate_professional_avatar(agent_name: str) -> str:
    """Generate a professional avatar using FAL AI"""
    try:
        # Parse first name from full name
        first_name = agent_name.split()[0] if agent_name else "Person"
        gender = determine_gender_from_name(first_name)
        
        # Create gender-appropriate prompt
        gender_descriptor = "woman" if gender == "female" else "man"
        
        prompt = f"Professional headshot portrait of a {gender_descriptor}, business attire, clean neutral background, high quality, photorealistic, confident expression, professional lighting, facing camera"
        
        handler = await fal_client.submit_async(
            "fal-ai/flux/dev",
            arguments={
                "prompt": prompt,
                "image_size": "portrait_4_3",
                "num_inference_steps": 28,
                "guidance_scale": 3.5,
                "num_images": 1
            }
        )
        
        result = await handler.get()
        
        if result and result.get("images") and len(result["images"]) > 0:
            return result["images"][0]["url"]
        else:
            logging.error(f"No images returned for avatar generation: {agent_name}")
            return ""
            
    except Exception as e:
        logging.error(f"Error generating avatar for {agent_name}: {e}")
        return ""

@api_router.post("/agents/generate-avatar")
async def generate_agent_avatar(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Generate professional avatar for an agent"""
    try:
        agent_name = request.get("agent_name", "")
        if not agent_name:
            raise HTTPException(status_code=400, detail="Agent name is required")
        
        avatar_url = await generate_professional_avatar(agent_name)
        
        if not avatar_url:
            raise HTTPException(status_code=500, detail="Failed to generate avatar")
        
        return {
            "success": True,
            "avatar_url": avatar_url,
            "agent_name": agent_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in avatar generation endpoint: {e}")
@api_router.post("/scenario/upload-content")
async def upload_scenario_content(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload content files for scenario context (images, docs, excel, links, pdfs)"""
    try:
        uploaded_files = []
        
        for file in files:
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
            
            # Read file content
            content = await file.read()
            
            # Process different file types
            if file.content_type and file.content_type.startswith('image/'):
                # Convert image to base64 for storage
                import base64
                content_base64 = base64.b64encode(content).decode('utf-8')
                processed_content = f"data:{file.content_type};base64,{content_base64}"
                content_type = "image"
            elif file.content_type == 'application/pdf':
                # For PDFs, we'd normally extract text, but for now store as base64
                import base64
                content_base64 = base64.b64encode(content).decode('utf-8')
                processed_content = f"data:{file.content_type};base64,{content_base64}"
                content_type = "pdf"
            elif file.content_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                # For Excel files, store as base64
                import base64
                content_base64 = base64.b64encode(content).decode('utf-8')
                processed_content = f"data:{file.content_type};base64,{content_base64}"
                content_type = "excel"
            elif file.content_type and file.content_type.startswith('text/'):
                # For text files, store as text
                processed_content = content.decode('utf-8', errors='ignore')
                content_type = "text"
            else:
                # For other files, store as base64
                import base64
                content_base64 = base64.b64encode(content).decode('utf-8')
                processed_content = f"data:{file.content_type};base64,{content_base64}"
                content_type = "document"
            
            # Store in database
            file_doc = {
                "id": file_id,
                "user_id": current_user.id,
                "filename": file.filename,
                "content_type": file.content_type,
                "file_type": content_type,
                "content": processed_content,
                "size": len(content),
                "uploaded_at": datetime.utcnow(),
                "scenario_context": True
            }
            
            await db.scenario_uploads.insert_one(file_doc)
            
            uploaded_files.append({
                "id": file_id,
                "filename": file.filename,
                "content_type": file.content_type,
                "file_type": content_type,
                "size": len(content)
            })
        
        return {
            "success": True,
            "message": f"Successfully uploaded {len(uploaded_files)} files",
            "files": uploaded_files
        }
        
    except Exception as e:
        logging.error(f"Error uploading scenario content: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@api_router.get("/scenario/uploads")
async def get_scenario_uploads(
    current_user: dict = Depends(get_current_user)
):
    """Get all uploaded scenario content for the user"""
    try:
        uploads = await db.scenario_uploads.find({
            "user_id": current_user.id,
            "scenario_context": True
        }).to_list(None)
        
        # Remove content from list view for performance
        for upload in uploads:
            upload.pop('content', None)
        
        return uploads
        
    except Exception as e:
        logging.error(f"Error fetching scenario uploads: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch uploads: {str(e)}")

@api_router.get("/scenario/uploads/{file_id}")
async def get_scenario_upload_content(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific uploaded file content"""
    try:
        upload = await db.scenario_uploads.find_one({
            "id": file_id,
            "user_id": current_user.id
        })
        
        if not upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        return upload
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching upload content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch file content: {str(e)}")
@api_router.delete("/conversation-history/bulk")
async def delete_conversations_bulk(
    conversation_ids: List[str],
    current_user: dict = Depends(get_current_user)
):
    """Delete multiple conversations for the authenticated user"""
    try:
        # Handle empty array case
        if not conversation_ids:
            return {
                "message": "Successfully deleted 0 conversations",
                "deleted_count": 0
            }
        
        # Verify all conversations belong to the user
        conversations = await db.conversation_history.find({
            "id": {"$in": conversation_ids},
            "user_id": current_user.id
        }).to_list(None)
        
        if len(conversations) != len(conversation_ids):
            raise HTTPException(status_code=404, detail="Some conversations not found or don't belong to user")
        
        # Delete the conversations
        result = await db.conversation_history.delete_many({
            "id": {"$in": conversation_ids},
            "user_id": current_user.id
        })
        
        return {
            "message": f"Successfully deleted {result.deleted_count} conversations",
            "deleted_count": result.deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete conversations: {str(e)}")

@api_router.post("/documents/bulk-delete")
async def delete_documents_bulk_post(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Delete multiple documents for the authenticated user using POST"""
    try:
        # Get document IDs from request body
        body = await request.body()
        if body:
            import json
            request_data = json.loads(body)
            # Handle both array directly and object with document_ids field
            if isinstance(request_data, list):
                document_ids = request_data
            elif isinstance(request_data, dict) and 'document_ids' in request_data:
                document_ids = request_data['document_ids']
            elif isinstance(request_data, dict) and 'data' in request_data:
                document_ids = request_data['data']
            else:
                document_ids = []
        else:
            document_ids = []
            
        # Ensure document_ids is a list
        if not isinstance(document_ids, list):
            raise HTTPException(status_code=400, detail="Request must contain a list of document IDs")
            
        # Handle empty array case
        if not document_ids:
            return {
                "message": "Successfully deleted 0 documents",
                "deleted_count": 0
            }
            
        # Verify all documents belong to the user
        documents = await db.documents.find({
            "id": {"$in": document_ids},
            "metadata.user_id": current_user.id
        }).to_list(None)
        
        if len(documents) != len(document_ids):
            raise HTTPException(status_code=404, detail="Some documents not found or don't belong to user")
        
        # Delete the documents
        result = await db.documents.delete_many({
            "id": {"$in": document_ids},
            "metadata.user_id": current_user.id
        })
        
        return {
            "message": f"Successfully deleted {result.deleted_count} documents",
            "deleted_count": result.deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete documents: {str(e)}")

@api_router.delete("/documents/bulk")
async def delete_documents_bulk(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Delete multiple documents for the authenticated user"""
    try:
        # Get document IDs from request body
        body = await request.body()
        if body:
            import json
            document_ids = json.loads(body)
        else:
            document_ids = []
            
        # Ensure document_ids is a list
        if not isinstance(document_ids, list):
            raise HTTPException(status_code=400, detail="Request body must be a list of document IDs")
            
        # Handle empty array case
        if not document_ids:
            return {
                "message": "Successfully deleted 0 documents",
                "deleted_count": 0
            }
            
        # Verify all documents belong to the user
        documents = await db.documents.find({
            "id": {"$in": document_ids},
            "metadata.user_id": current_user.id
        }).to_list(None)
        
        if len(documents) != len(document_ids):
            raise HTTPException(status_code=404, detail="Some documents not found or don't belong to user")
        
        # Delete the documents
        result = await db.documents.delete_many({
            "id": {"$in": document_ids},
            "metadata.user_id": current_user.id
        })
        
        return {
            "message": f"Successfully deleted {result.deleted_count} documents",
            "deleted_count": result.deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete documents: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
