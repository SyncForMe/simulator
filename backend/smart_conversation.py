"""
Smart Conversation Generation System
Creates realistic, contextual conversations when LLM calls timeout
"""

import random
from typing import List, Dict, Any
from datetime import datetime

class SmartConversationGenerator:
    def __init__(self):
        self.conversation_starters = {
            "scientist": [
                "The data I've been analyzing suggests {topic_insight}",
                "From a research perspective, we need to examine {key_factor}",
                "My lab results indicate that {technical_point}",
                "The scientific evidence shows {research_finding}",
                "Based on peer-reviewed studies, {scientific_approach}"
            ],
            "optimist": [
                "This is an incredible opportunity to {positive_outcome}!",
                "I'm excited about the potential for {breakthrough_possibility}",
                "Think about how this could transform {improvement_area}",
                "The possibilities here are endless - we could {inspiring_vision}",
                "This breakthrough could be the game-changer we've been waiting for"
            ],
            "skeptic": [
                "We need to be realistic about {potential_challenge}",
                "I'm concerned about the {risk_factor} implications",
                "Before we get too excited, what about {practical_concern}?",
                "The numbers don't add up when it comes to {economic_reality}",
                "History shows us that {cautionary_example}"
            ],
            "leader": [
                "We need to develop a strategic approach to {key_challenge}",
                "The implementation timeline should focus on {priority_area}",
                "My experience leading {relevant_project} taught me {leadership_insight}",
                "To scale this effectively, we must {strategic_action}",
                "The key stakeholders we need to align are {stakeholder_groups}"
            ],
            "artist": [
                "This isn't just about technology - it's about {human_element}",
                "We need to tell the story of {inspiring_narrative}",
                "The visual impact of {creative_aspect} could be powerful",
                "People will only embrace this if we {emotional_connection}",
                "The aesthetic and user experience of {design_element} matters"
            ]
        }
        
        self.response_patterns = {
            "agreement": [
                "Absolutely, {name}. Building on that, {extension}",
                "You're right about {point}. I'd also add that {addition}",
                "That's exactly what I was thinking. {supporting_evidence}",
                "Great point, {name}. In my experience, {related_experience}"
            ],
            "disagreement": [
                "I see your point, {name}, but {counterargument}",
                "That's interesting, though I'm not sure about {concern}",
                "I have a different perspective on {topic}. {alternative_view}",
                "While I understand {acknowledgment}, I think {opposing_view}"
            ],
            "building": [
                "Building on {name}'s point about {topic}, {expansion}",
                "That reminds me of {related_concept}. What if {new_idea}?",
                "Following that logic, we could also {logical_extension}",
                "Taking that further, {development_of_idea}"
            ]
        }

    def generate_contextual_response(self, agent: Dict[str, Any], scenario: str, scenario_name: str, 
                                   conversation_history: List[Dict], turn_number: int) -> str:
        """Generate a realistic, contextual response based on agent personality and context"""
        
        archetype = agent.get("archetype", "scientist")
        name = agent.get("name", "Agent")
        expertise = agent.get("expertise", "general knowledge")
        background = agent.get("background", "professional experience")
        
        # Extract key themes from scenario
        scenario_keywords = self.extract_key_themes(scenario, scenario_name)
        
        # Determine response type based on conversation flow
        if turn_number == 0:
            # First speaker - introduce perspective
            response_type = "starter"
        elif len(conversation_history) > 0:
            # Respond to previous speakers
            response_type = random.choices(
                ["agreement", "building", "disagreement"],
                weights=[0.4, 0.4, 0.2]  # More agreement/building than disagreement
            )[0]
        else:
            response_type = "starter"
        
        if response_type == "starter":
            return self.generate_opening_statement(agent, scenario_keywords, scenario_name)
        else:
            return self.generate_response_to_conversation(agent, scenario_keywords, conversation_history, response_type)
    
    def extract_key_themes(self, scenario: str, scenario_name: str) -> Dict[str, str]:
        """Extract key themes and concepts from the scenario"""
        scenario_lower = scenario.lower()
        scenario_name_lower = scenario_name.lower()
        
        themes = {}
        
        # Technology themes
        if any(word in scenario_lower for word in ["ai", "artificial intelligence", "machine learning"]):
            themes["tech_focus"] = "artificial intelligence"
        elif any(word in scenario_lower for word in ["solar", "renewable", "energy", "battery"]):
            themes["tech_focus"] = "renewable energy"
        elif any(word in scenario_lower for word in ["blockchain", "crypto", "digital"]):
            themes["tech_focus"] = "blockchain technology"
        elif any(word in scenario_lower for word in ["bio", "medical", "health", "genetic"]):
            themes["tech_focus"] = "biotechnology"
        else:
            themes["tech_focus"] = "emerging technology"
        
        # Challenge themes
        if any(word in scenario_lower for word in ["investment", "funding", "cost", "economic"]):
            themes["challenge"] = "economic viability"
        elif any(word in scenario_lower for word in ["cooperation", "global", "international"]):
            themes["challenge"] = "international coordination"
        elif any(word in scenario_lower for word in ["ethical", "privacy", "safety", "risk"]):
            themes["challenge"] = "ethical considerations"
        else:
            themes["challenge"] = "implementation challenges"
        
        # Opportunity themes
        if any(word in scenario_lower for word in ["transform", "revolution", "breakthrough"]):
            themes["opportunity"] = "transformative potential"
        elif any(word in scenario_lower for word in ["scale", "global", "widespread"]):
            themes["opportunity"] = "scalable impact"
        elif any(word in scenario_lower for word in ["sustainable", "environment", "climate"]):
            themes["opportunity"] = "sustainability benefits"
        else:
            themes["opportunity"] = "innovation opportunities"
        
        return themes
    
    def generate_opening_statement(self, agent: Dict[str, Any], themes: Dict[str, str], scenario_name: str) -> str:
        """Generate an opening statement based on agent archetype and scenario themes"""
        archetype = agent.get("archetype", "scientist")
        expertise = agent.get("expertise", "general knowledge")
        
        if archetype == "scientist":
            return f"Looking at this {scenario_name} from a research perspective, my work in {expertise} suggests we need to carefully validate the {themes.get('tech_focus', 'technology')} before moving to large-scale implementation. The peer review process will be crucial."
        
        elif archetype == "optimist":
            return f"This {scenario_name} represents an incredible opportunity! My experience in {expertise} has shown me that breakthroughs like this can create {themes.get('opportunity', 'positive change')} beyond what we initially imagine. We should move quickly but thoughtfully."
        
        elif archetype == "skeptic":
            return f"While the {scenario_name} sounds promising, my background in {expertise} makes me cautious about {themes.get('challenge', 'potential obstacles')}. We've seen similar initiatives struggle with scaling. What's our realistic timeline and budget?"
        
        elif archetype == "leader":
            return f"The {scenario_name} requires strategic coordination. In my experience with {expertise}, success depends on aligning all stakeholders around {themes.get('opportunity', 'shared goals')}. We need a clear roadmap and governance structure."
        
        elif archetype == "artist":
            return f"The {scenario_name} isn't just about the technology - it's about how people will experience and adopt it. My work in {expertise} has taught me that {themes.get('tech_focus', 'innovation')} only succeeds when it resonates emotionally with users."
        
        else:
            return f"From my perspective in {expertise}, the {scenario_name} presents both {themes.get('opportunity', 'opportunities')} and {themes.get('challenge', 'challenges')}. We need a balanced approach that considers all stakeholders."
    
    def generate_response_to_conversation(self, agent: Dict[str, Any], themes: Dict[str, str], 
                                        conversation_history: List[Dict], response_type: str) -> str:
        """Generate a response that builds on the conversation"""
        archetype = agent.get("archetype", "scientist")
        expertise = agent.get("expertise", "general knowledge")
        
        if not conversation_history:
            return self.generate_opening_statement(agent, themes, "discussion")
        
        # Get the last speaker's name for reference
        last_message = conversation_history[-1]
        last_speaker = last_message.get("agent_name", "previous speaker")
        
        if response_type == "agreement":
            if archetype == "scientist":
                return f"I agree with {last_speaker}'s analysis. The data from my {expertise} research supports that approach. We should also consider the long-term sustainability metrics."
            elif archetype == "optimist":
                return f"Exactly, {last_speaker}! That's the kind of forward-thinking we need. My experience in {expertise} shows that when we combine innovation with collaboration, we can achieve {themes.get('opportunity', 'remarkable results')}."
            elif archetype == "skeptic":
                return f"{last_speaker} raises valid points, though I remain concerned about the {themes.get('challenge', 'practical challenges')}. My work in {expertise} has shown that these issues often become magnified at scale."
            elif archetype == "leader":
                return f"Building on {last_speaker}'s insights, we need to structure this as a phased implementation. My experience in {expertise} suggests we start with pilot programs to validate the approach."
            else:
                return f"I appreciate {last_speaker}'s perspective. From my background in {expertise}, I'd add that user adoption will be key to success."
        
        elif response_type == "building":
            if archetype == "scientist":
                return f"Expanding on {last_speaker}'s point, my research in {expertise} indicates we could also explore {themes.get('tech_focus', 'related technologies')}. The scientific literature suggests promising synergies."
            elif archetype == "optimist":
                return f"That's a great foundation, {last_speaker}! Taking it further, imagine if we could leverage {themes.get('opportunity', 'this opportunity')} to create even broader impact in underserved communities."
            elif archetype == "skeptic":
                return f"While {last_speaker} makes good points, we need to also consider the {themes.get('challenge', 'regulatory hurdles')}. My experience in {expertise} shows these often take longer than expected to resolve."
            elif archetype == "leader":
                return f"Following {last_speaker}'s logic, the next step is to identify key stakeholders and develop a governance framework. My work in {expertise} has taught me that clear accountability drives results."
            else:
                return f"Building on what {last_speaker} said, the user experience design for {themes.get('tech_focus', 'this technology')} will be crucial for widespread adoption."
        
        elif response_type == "disagreement":
            if archetype == "scientist":
                return f"I see {last_speaker}'s point, but the research in {expertise} suggests a different approach. We need more rigorous testing before we can make those claims."
            elif archetype == "skeptic":
                return f"I have to respectfully disagree with {last_speaker}. My analysis of {themes.get('challenge', 'market conditions')} shows this approach may not be financially viable at scale."
            elif archetype == "optimist":
                return f"I understand {last_speaker}'s concerns, but I think we're underestimating the {themes.get('opportunity', 'positive potential')}. My experience in {expertise} shows that bold moves often pay off."
            elif archetype == "leader":
                return f"While I respect {last_speaker}'s perspective, my experience in {expertise} suggests we need a more structured approach to {themes.get('challenge', 'risk management')}."
            else:
                return f"I have a different take than {last_speaker}. From my work in {expertise}, I think the key factor we're missing is {themes.get('tech_focus', 'human-centered design')}."
        
        return f"That's an interesting perspective from my background in {expertise}."