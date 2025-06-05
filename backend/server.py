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
from emergentintegrations.llm.chat import LlmChat, UserMessage

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
    current_mood: str = "neutral"
    current_activity: str = "idle"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AgentCreate(BaseModel):
    name: str
    archetype: str
    personality: Optional[AgentPersonality] = None
    goal: str

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

# LLM Integration and Request Management
class LLMManager:
    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        self.max_daily_requests = 1400
        
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
    
    async def can_make_request(self):
        """Check if we can make another API request today"""
        usage = await self.get_usage_today()
        return usage < self.max_daily_requests
    
    async def generate_agent_response(self, agent: Agent, scenario: str, other_agents: List[Agent], context: str = ""):
        """Generate a single agent response"""
        if not await self.can_make_request():
            return "Agent is resting (daily API limit reached)"
        
        # Create LLM chat instance for this agent
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"agent_{agent.id}_{datetime.now().timestamp()}",
            system_message=f"""You are {agent.name}, {AGENT_ARCHETYPES[agent.archetype]['description']}.
            
Your personality traits:
- Extroversion: {agent.personality.extroversion}/10
- Optimism: {agent.personality.optimism}/10  
- Curiosity: {agent.personality.curiosity}/10
- Cooperativeness: {agent.personality.cooperativeness}/10
- Energy: {agent.personality.energy}/10

Your goal: {agent.goal}

You are currently in: {scenario}
Current context: {context}

Respond authentically to your personality in 1-2 sentences. Be natural and conversational."""
        ).with_model("gemini", "gemini-2.0-flash")
        
        # Generate prompt based on other agents present
        other_names = [a.name for a in other_agents if a.id != agent.id]
        prompt = f"You are in {scenario}. Others present: {', '.join(other_names) if other_names else 'no one else'}. {context}"
        
        try:
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            await self.increment_usage()
            return response
        except Exception as e:
            logging.error(f"Error generating response for {agent.name}: {e}")
            return f"{agent.name} seems distracted..."

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
    """Generate AI summary of conversations from the past week"""
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
    for conv in recent_conversations:
        conv_text += f"\n{conv['time_period']}:\n"
        for msg in conv.get('messages', []):
            conv_text += f"- {msg['agent_name']}: {msg['message']}\n"
    
    # Generate summary using LLM
    chat = LlmChat(
        api_key=llm_manager.api_key,
        session_id=f"summary_{datetime.now().timestamp()}",
        system_message="""You are analyzing AI agent interactions over time. 
        Create a concise summary highlighting:
        1. Key relationship developments
        2. Personality traits that emerged
        3. Conflicts or agreements
        4. Notable behavioral patterns
        5. Any emergent discoveries or realizations
        
        Be analytical but engaging. Focus on the most interesting social dynamics."""
    ).with_model("gemini", "gemini-2.0-flash")
    
    prompt = f"""Analyze these AI agent conversations from the Research Station simulation:

{conv_text}

Provide a weekly summary in this format:
**Week Summary - Day {current_day}**

**Relationship Developments:**
[Key changes in how agents interact with each other]

**Emerging Personalities:** 
[How each agent's personality manifested]

**Key Events & Discoveries:**
[Important moments, agreements, conflicts, or insights]

**Social Dynamics:**
[Overall team cohesion, leadership patterns, group behavior]

**Looking Ahead:**
[Predictions for future developments]"""
    
    try:
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        await llm_manager.increment_usage()
        
        # Store summary in database
        summary_doc = {
            "id": str(uuid.uuid4()),
            "summary": response,
            "day_generated": current_day,
            "conversations_analyzed": len(recent_conversations),
            "created_at": datetime.utcnow()
        }
        await db.summaries.insert_one(summary_doc)
        
        return {"summary": response, "day": current_day, "conversations_count": len(recent_conversations)}
        
    except Exception as e:
        logging.error(f"Error generating summary: {e}")
        return {"summary": f"Error generating summary: {str(e)}"}

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
        goal=agent_data.goal
    )
    
    await db.agents.insert_one(agent.dict())
    return agent

@api_router.get("/agents", response_model=List[Agent])
async def get_agents():
    """Get all agents"""
    agents = await db.agents.find().to_list(100)
    return [Agent(**agent) for agent in agents]

@api_router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    result = await db.agents.delete_one({"id": agent_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": "Agent deleted"}

@api_router.post("/simulation/start")
async def start_simulation():
    """Start or reset the simulation"""
    # Reset simulation state
    simulation = SimulationState(is_active=True)
    await db.simulation_state.delete_many({})
    await db.simulation_state.insert_one(simulation.dict())
    
    # Clear previous conversations and relationships
    await db.conversations.delete_many({})
    await db.relationships.delete_many({})
    
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
    """Generate a conversation round between agents"""
    # Get current agents
    agents = await db.agents.find().to_list(100)
    if len(agents) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 agents for conversation")
    
    agent_objects = [Agent(**agent) for agent in agents]
    
    # Get simulation state
    state = await db.simulation_state.find_one()
    if not state:
        raise HTTPException(status_code=404, detail="Simulation not started")
    
    # Generate conversation context
    time_period = state["current_time_period"]
    day = state["current_day"]
    scenario = state["scenario"]
    
    context = f"Day {day}, {time_period}. The research team is settling into their routine."
    
    # Generate responses from each agent
    messages = []
    for agent in agent_objects:
        response = await llm_manager.generate_agent_response(
            agent, scenario, agent_objects, context
        )
        
        message = ConversationMessage(
            agent_id=agent.id,
            agent_name=agent.name,
            message=response,
            mood=agent.current_mood
        )
        messages.append(message)
    
    # Get current round number
    conversation_count = await db.conversations.count_documents({})
    
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
    return relationships

@api_router.get("/api-usage")
async def get_api_usage():
    """Get current API usage"""
    usage = await llm_manager.get_usage_today()
    return {
        "date": str(date.today()),
        "requests_used": usage,
        "max_requests": llm_manager.max_daily_requests,
        "remaining": llm_manager.max_daily_requests - usage
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

@api_router.get("/summaries")
async def get_summaries():
    """Get all generated summaries"""
    summaries = await db.summaries.find().sort("created_at", -1).to_list(100)
    
    # Convert MongoDB ObjectId to string to make it JSON serializable
    for summary in summaries:
        if '_id' in summary:
            summary['_id'] = str(summary['_id'])
    
    return summaries

@api_router.post("/simulation/toggle-auto-mode")
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

# Initialize Research Station scenario
@api_router.post("/simulation/init-research-station")
async def init_research_station():
    """Initialize the Research Station scenario with 3 default agents"""
    # Clear existing agents
    await db.agents.delete_many({})
    
    # Create the 3 research station agents
    agents_data = [
        {
            "name": "Dr. Sarah Chen",
            "archetype": "scientist",
            "goal": "Study team dynamics and research efficiency during isolation"
        },
        {
            "name": "Marcus Rivera", 
            "archetype": "optimist",
            "goal": "Keep team morale high and foster collaboration"
        },
        {
            "name": "Alex Thompson",
            "archetype": "skeptic", 
            "goal": "Ensure mission safety and identify potential problems"
        }
    ]
    
    created_agents = []
    for agent_data in agents_data:
        agent_create = AgentCreate(**agent_data)
        agent = await create_agent(agent_create)
        created_agents.append(agent)
    
    # Start simulation
    await start_simulation()
    
    return {
        "message": "Research Station scenario initialized", 
        "agents": created_agents
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
