from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uuid
from datetime import datetime, date
import asyncio
import re
import urllib.parse
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage
from google.cloud import texttospeech
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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

@api_router.get("/observer/messages")
async def get_observer_messages():
    """Get all observer messages"""
    messages = await db.observer_messages.find().sort("timestamp", -1).to_list(100)
    return messages

# Pydantic Models
class AgentPersonality(BaseModel):
    extroversion: int = Field(ge=1, le=10)
    optimism: int = Field(ge=1, le=10) 
    curiosity: int = Field(ge=1, le=10)
    cooperativeness: int = Field(ge=1, le=10)
    energy: int = Field(ge=1, le=10)

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
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AgentCreate(BaseModel):
    name: str
    archetype: str
    personality: Optional[AgentPersonality] = None
    goal: str
    expertise: str = ""
    background: str = ""

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
    messages: List[ConversationMessage]
    created_at: datetime = Field(default_factory=datetime.utcnow)

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

class ApiUsageTracker(BaseModel):
    date: str
    requests_used: int
    max_requests: int = 1400  # Buffer under 1500 limit

class ScenarioRequest(BaseModel):
    scenario: str

class AutoModeRequest(BaseModel):
    auto_conversations: bool = False
    auto_time: bool = False
    conversation_interval: int = 10
    time_interval: int = 30

class FastForwardRequest(BaseModel):
    target_days: int = Field(ge=1, le=30)  # 1-30 days max
    conversations_per_period: int = Field(ge=1, le=5, default=2)  # 1-5 conversations per time period

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    archetype: Optional[str] = None
    personality: Optional[AgentPersonality] = None
    goal: Optional[str] = None
    expertise: Optional[str] = None
    background: Optional[str] = None
    memory_summary: Optional[str] = None

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

    async def generate_agent_response(self, agent: Agent, scenario: str, other_agents: List[Agent], context: str = "", conversation_history: List = None, language_instruction: str = "Respond in English."):
        """Generate a single agent response with better context and progression"""
        if not await self.can_make_request():
            return f"{agent.name} is taking a moment to think... (daily API limit reached)"
        
        # Build a simple, direct prompt for better LLM performance
        other_agent_names = [a.name for a in other_agents if a.id != agent.id]
        others_text = f"Others present: {', '.join(other_agent_names)}" if other_agent_names else "You are alone"
        
        # Enhanced system message for conversational responses
        system_message = f"""You are {agent.name}, a {AGENT_ARCHETYPES[agent.archetype]['description']}.

Your goal: {agent.goal}

Personality traits:
- Extroversion: {agent.personality.extroversion}/10
- Optimism: {agent.personality.optimism}/10  
- Curiosity: {agent.personality.curiosity}/10
- Cooperativeness: {agent.personality.cooperativeness}/10
- Energy: {agent.personality.energy}/10

NATURAL CONVERSATION RULES:
1. Respond like a real person - sometimes answer directly, sometimes challenge ideas, sometimes offer alternatives
2. Don't always end with questions - maybe 30% of responses should have questions, 70% should be statements/answers/opinions
3. When someone asks you a question, answer it clearly first, then add your own perspective
4. Push conversations toward decisions and conclusions rather than endless discussion
5. Sometimes disagree constructively or build on others' ideas
6. Show your expertise and background in your responses

LANGUAGE INSTRUCTION:
{language_instruction}
7. Make progress - don't rehash the same points endlessly
8. Be decisive when appropriate - "I think we should..." rather than "What if we considered..."

RESPONSE VARIETY (choose based on context):
- Direct answers: "Yes, that makes sense because..."
- Strong opinions: "I disagree. Based on my experience..."
- Building on ideas: "That's a solid point. We could also..."
- Providing alternatives: "Instead of that approach, what about..."
- Making decisions: "I think we should go with option X because..."
- Sharing expertise: "In my experience with [domain], this usually works better..."
- Challenging assumptions: "Hold on, I think we're missing something important here..."

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
            response = await chat.send_message(user_message)
            await self.increment_usage()
            
            # Validate response
            if response and len(response.strip()) > 5:
                return response.strip()
            else:
                return f"{agent.name}: I'm carefully considering this situation."
                
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

llm_manager = LLMManager()

# API Routes
@api_router.get("/")
async def root():
    return {"message": "AI Agent Simulation API"}

@api_router.post("/simulation/set-scenario")
async def set_scenario(request: ScenarioRequest):
    """Set a custom scenario for the simulation"""
    scenario = request.scenario.strip()
    if not scenario:
        raise HTTPException(status_code=400, detail="Scenario text required")
    
    # Update simulation state with new scenario
    await db.simulation_state.update_one(
        {},
        {"$set": {"scenario": scenario}},
        upsert=True
    )
    
    return {"message": "Scenario updated", "scenario": scenario}

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
    """Generate structured AI summary of conversations with focus on key discoveries"""
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
    
    # Check API usage
    if not await llm_manager.can_make_request():
        return {"summary": "Cannot generate summary - daily API limit reached"}
    
    # Prepare conversation text for summary
    conv_text = ""
    key_decisions = []
    agent_interactions = []
    
    for conv in recent_conversations:
        conv_text += f"\n**{conv['time_period']}:**\n"
        for msg in conv.get('messages', []):
            conv_text += f"- **{msg['agent_name']}**: {msg['message']}\n"
            # Track significant statements for key events
            if any(keyword in msg['message'].lower() for keyword in ['decide', 'discovery', 'found', 'breakthrough', 'crisis', 'solution', 'agreement', 'conflict']):
                key_decisions.append(f"{msg['agent_name']}: {msg['message']}")
    
    # Generate structured summary using LLM
    chat = LlmChat(
        api_key=llm_manager.api_key,
        session_id=f"weekly_summary_{datetime.now().timestamp()}",
        system_message="""You are analyzing AI agent interactions to create a structured weekly report. 
        Focus on concrete discoveries, decisions, breakthroughs, and significant developments.
        
        Create a report with these sections:
        1. KEY EVENTS & DISCOVERIES (main focus - most important developments, decisions, breakthroughs)
        2. RELATIONSHIP DEVELOPMENTS (how agent relationships changed)
        3. EMERGING PERSONALITIES (how each agent's personality manifested)
        4. SOCIAL DYNAMICS (team cohesion, leadership patterns, conflicts)
        5. STRATEGIC DECISIONS (important choices made by the team)
        6. LOOKING AHEAD (predictions for future developments)
        
        Use **bold** for section headers and important points. Be specific and actionable."""
    ).with_model("gemini", "gemini-2.0-flash")
    
    prompt = f"""Analyze these AI agent conversations from the Research Station simulation:

{conv_text}

Provide a weekly summary in this format:
**Week Summary - Day {current_day}**

**1. 🔥 KEY EVENTS & DISCOVERIES**

1. [First major event or discovery - detailed paragraph with specific examples]

2. [Second major event or discovery - detailed paragraph with specific examples]

3. [Third major event or discovery - detailed paragraph with specific examples]

**2. 📈 RELATIONSHIP DEVELOPMENTS**

1. [First relationship change or development - detailed paragraph]

2. [Second relationship change or development - detailed paragraph]

3. [Third relationship change or development - detailed paragraph]

**3. 🎭 EMERGING PERSONALITIES**

1. [First agent's personality development - detailed paragraph]

2. [Second agent's personality development - detailed paragraph]

3. [Third agent's personality development - detailed paragraph]

**4. 🤝 SOCIAL DYNAMICS**

1. [First social pattern or team dynamic - detailed paragraph]

2. [Second social pattern or team dynamic - detailed paragraph]

3. [Third social pattern or team dynamic - detailed paragraph]

**5. 🔮 LOOKING AHEAD**

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
    """Create a new AI agent"""
    # Use default personality if not provided
    if not agent_data.personality:
        if agent_data.archetype in AGENT_ARCHETYPES:
            default_traits = AGENT_ARCHETYPES[agent_data.archetype]["default_traits"]
            agent_data.personality = AgentPersonality(**default_traits)
        else:
            raise HTTPException(status_code=400, detail="Invalid archetype")
    
    agent = Agent(
        name=agent_data.name,
        archetype=agent_data.archetype,
        personality=agent_data.personality,
        goal=agent_data.goal,
        expertise=agent_data.expertise,
        background=agent_data.background
    )
    
    await db.agents.insert_one(agent.dict())
    return agent

@api_router.get("/agents", response_model=List[Agent])
async def get_agents():
    """Get all agents"""
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
async def start_simulation():
    """Start or reset the simulation"""
    # Reset simulation state
    simulation = SimulationState(is_active=True)
    await db.simulation_state.delete_many({})
    await db.simulation_state.insert_one(simulation.dict())
    
    # Clear previous conversations, relationships, and summaries
    await db.conversations.delete_many({})
    await db.relationships.delete_many({})
    await db.summaries.delete_many({})  # Clear old weekly reports
    
    return {"message": "Simulation started", "state": simulation}

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
    
    return state

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

@api_router.post("/conversation/generate")
async def generate_conversation():
    """Generate a conversation round between agents with sequential responses and progression tracking"""
    # Get current agents
    agents = await db.agents.find().to_list(100)
    if len(agents) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 agents for conversation")
    
    agent_objects = [Agent(**agent) for agent in agents]
    
    # Get simulation state including language setting
    state = await db.simulation_state.find_one()
    if not state:
        raise HTTPException(status_code=404, detail="Simulation not started")
    
    # Generate conversation context
    time_period = state["current_time_period"]
    day = state["current_day"]
    scenario = state["scenario"]
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
            agent, scenario, agent_objects, current_context, recent_conversations, language_instruction
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
        messages=messages
    )
    
    await db.conversations.insert_one(conversation_round.dict())
    
    # Update agent relationships based on interactions
    await update_relationships(agent_objects, messages)
    
    return conversation_round

@api_router.get("/conversations", response_model=List[ConversationRound])
async def get_conversations():
    """Get all conversation rounds"""
    conversations = await db.conversations.find().sort("created_at", 1).to_list(1000)
    return [ConversationRound(**conv) for conv in conversations]

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

@api_router.get("/api-usage")
async def get_api_usage():
    """Get current API usage"""
    usage = await llm_manager.get_usage_today()
    
    # Test if API is actually working
    api_available = True
    try:
        # Quick test call to check quota status
        chat = LlmChat(
            api_key=llm_manager.api_key,
            session_id=f"quota_test_{datetime.now().timestamp()}",
            system_message="You are a test."
        ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(10)
        
        user_message = UserMessage(text="Hi")
        test_response = await chat.send_message(user_message)
        
        if not test_response:
            api_available = False
            
    except Exception as e:
        api_available = False
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            api_available = "quota_exceeded"
    
    return {
        "date": str(date.today()),
        "requests_used": usage,
        "max_requests": llm_manager.max_daily_requests,
        "remaining": llm_manager.max_daily_requests - usage,
        "api_available": api_available,
        "note": "API quota exceeded - using intelligent fallbacks" if api_available == "quota_exceeded" else ""
    }

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
async def init_research_station():
    """Initialize default crypto team AI agents with rich personalities and expertise"""
    # Clear existing agents
    await db.agents.delete_many({})
    
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
            memory_summary=agent_data.get("memory_summary", "")
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
    """Translate all existing conversations to target language"""
    target_language = request.get("target_language", "en")
    
    if target_language == "en":
        return {"message": "No translation needed for English", "translated_count": 0}
    
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
        # Get all conversations
        conversations = await db.conversations.find().to_list(1000)
        translated_count = 0
        
        for conversation in conversations:
            # Skip if already translated to this language
            if conversation.get("language") == target_language:
                continue
                
            translated_messages = []
            
            for message in conversation.get("messages", []):
                original_text = message.get("message", "")
                if not original_text:
                    continue
                
                # Create translation prompt
                translation_prompt = f"""Translate this conversation message to {target_language_name}. 
                
Keep the same tone, personality, and meaning. This is from an AI agent simulation.

Original message: "{original_text}"

Translate to {target_language_name}:"""
                
                # Use LLM to translate
                chat = LlmChat(
                    api_key=llm_manager.api_key,
                    session_id=f"translate_{target_language}_{datetime.now().timestamp()}",
                    system_message=f"You are a professional translator. Translate text to {target_language_name} while preserving tone and meaning."
                ).with_model("gemini", "gemini-2.0-flash").with_max_tokens(200)
                
                user_message = UserMessage(text=translation_prompt)
                translated_text = await chat.send_message(user_message)
                
                # Update message
                translated_message = message.copy()
                translated_message["message"] = translated_text.strip() if translated_text else original_text
                translated_messages.append(translated_message)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(1)
            
            # Update conversation with translated messages
            await db.conversations.update_one(
                {"_id": conversation["_id"]},
                {
                    "$set": {
                        "messages": translated_messages,
                        "language": target_language,
                        "original_language": conversation.get("language", "en"),
                        "translated_at": datetime.utcnow()
                    }
                }
            )
            
            translated_count += 1
            await llm_manager.increment_usage()
        
        return {
            "message": f"Successfully translated {translated_count} conversations to {target_language_name}",
            "translated_count": translated_count,
            "target_language": target_language
        }
        
    except Exception as e:
        logging.error(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

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
        
        # Language to TTS language code mapping
        language_codes = {
            "en": "en-US",
            "es": "es-ES", 
            "fr": "fr-FR",
            "de": "de-DE",
            "it": "it-IT",
            "pt": "pt-BR",
            "ru": "ru-RU",
            "ja": "ja-JP",
            "ko": "ko-KR",
            "zh": "zh-CN",
            "hi": "hi-IN",
            "ar": "ar-XA"
        }
        
        # Voice configurations for different agents and languages
        agent_voices = {
            'Marcus "Mark" Castellano': {
                'en-US': {'name': 'en-US-Neural2-D', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'es-ES': {'name': 'es-ES-Neural2-B', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'fr-FR': {'name': 'fr-FR-Neural2-B', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'de-DE': {'name': 'de-DE-Neural2-B', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'default': {'name': 'en-US-Neural2-D', 'gender': texttospeech.SsmlVoiceGender.MALE}
            },
            'Alexandra "Alex" Chen': {
                'en-US': {'name': 'en-US-Neural2-F', 'gender': texttospeech.SsmlVoiceGender.FEMALE},
                'es-ES': {'name': 'es-ES-Neural2-A', 'gender': texttospeech.SsmlVoiceGender.FEMALE},
                'fr-FR': {'name': 'fr-FR-Neural2-A', 'gender': texttospeech.SsmlVoiceGender.FEMALE},
                'zh-CN': {'name': 'zh-CN-Neural2-A', 'gender': texttospeech.SsmlVoiceGender.FEMALE},
                'default': {'name': 'en-US-Neural2-F', 'gender': texttospeech.SsmlVoiceGender.FEMALE}
            },
            'Diego "Dex" Rodriguez': {
                'en-US': {'name': 'en-US-Neural2-A', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'es-ES': {'name': 'es-ES-Neural2-C', 'gender': texttospeech.SsmlVoiceGender.MALE},
                'default': {'name': 'en-US-Neural2-A', 'gender': texttospeech.SsmlVoiceGender.MALE}
            }
        }
        
        # Get language code
        tts_language = language_codes.get(request.language, "en-US")
        
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

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
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
