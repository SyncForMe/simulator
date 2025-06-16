#!/usr/bin/env python3
"""
Test module for enhanced dynamic conversation system
"""

import requests
import json
import time
import os
import sys
from dotenv import load_dotenv
import uuid
import re

def test_dynamic_conversation(API_URL, auth_token, run_test):
    """Test the enhanced dynamic conversation system"""
    print("\n" + "="*80)
    print("TESTING ENHANCED DYNAMIC CONVERSATION SYSTEM")
    print("="*80)
    
    # Check if we have auth token
    if not auth_token:
        print("❌ Cannot test dynamic conversation without authentication")
        return False, "Authentication failed"
    
    # Test 1: Create a new simulation
    print("\nTest 1: Creating a new simulation")
    
    simulation_start_test, simulation_start_response = run_test(
        "Start simulation",
        "/simulation/start",
        method="POST",
        auth=True,
        expected_keys=["message", "state"]
    )
    
    if not simulation_start_test:
        print("❌ Failed to start simulation")
        return False, "Failed to start simulation"
    
    print("✅ Successfully started simulation")
    
    # Test 2: Create test agents with diverse expertise
    print("\nTest 2: Creating test agents with diverse expertise")
    
    # Create agents with different expertise areas
    agent_data = [
        {
            "name": "Dr. James Wilson",
            "archetype": "scientist",
            "personality": {
                "extroversion": 4,
                "optimism": 6,
                "curiosity": 9,
                "cooperativeness": 7,
                "energy": 6
            },
            "goal": "Advance scientific understanding of quantum computing",
            "expertise": "Quantum Physics",
            "background": "Former lead researcher at CERN with 15 years experience in quantum computing",
            "memory_summary": "",
            "avatar_prompt": "",
            "avatar_url": ""
        },
        {
            "name": "Sarah Johnson",
            "archetype": "leader",
            "personality": {
                "extroversion": 9,
                "optimism": 8,
                "curiosity": 6,
                "cooperativeness": 8,
                "energy": 8
            },
            "goal": "Ensure project success and team coordination",
            "expertise": "Project Management",
            "background": "20 years experience in tech leadership and managing complex technical projects",
            "memory_summary": "",
            "avatar_prompt": "",
            "avatar_url": ""
        },
        {
            "name": "Michael Chen",
            "archetype": "skeptic",
            "personality": {
                "extroversion": 4,
                "optimism": 3,
                "curiosity": 7,
                "cooperativeness": 5,
                "energy": 5
            },
            "goal": "Identify and mitigate project risks",
            "expertise": "Risk Assessment",
            "background": "Former security consultant specializing in cryptographic systems",
            "memory_summary": "",
            "avatar_prompt": "",
            "avatar_url": ""
        },
        {
            "name": "Emily Rodriguez",
            "archetype": "optimist",
            "personality": {
                "extroversion": 8,
                "optimism": 10,
                "curiosity": 6,
                "cooperativeness": 9,
                "energy": 8
            },
            "goal": "Maximize the positive impact of quantum computing",
            "expertise": "Business Development",
            "background": "Startup founder with experience in bringing emerging technologies to market",
            "memory_summary": "",
            "avatar_prompt": "",
            "avatar_url": ""
        }
    ]
    
    created_agents = []
    
    for agent in agent_data:
        create_agent_test, create_agent_response = run_test(
            f"Create Agent: {agent['name']}",
            "/agents",
            method="POST",
            data=agent,
            auth=True,
            expected_keys=["id", "name"]
        )
        
        if create_agent_test and create_agent_response:
            print(f"✅ Created agent: {create_agent_response.get('name')} with ID: {create_agent_response.get('id')}")
            created_agents.append(create_agent_response)
        else:
            print(f"❌ Failed to create agent: {agent['name']}")
    
    if len(created_agents) < 3:
        print(f"❌ Failed to create enough test agents. Only created {len(created_agents)} out of 4.")
        return False, "Failed to create enough test agents"
    
    # Test 3: Set a scenario
    print("\nTest 3: Setting a scenario")
    
    scenario_data = {
        "scenario": "The team is discussing the implementation of a new quantum computing project with potential applications in cryptography. The project has a tight deadline and limited budget, but could revolutionize secure communications if successful.",
        "scenario_name": "Quantum Cryptography Project"
    }
    
    set_scenario_test, set_scenario_response = run_test(
        "Set Scenario",
        "/simulation/set-scenario",
        method="POST",
        data=scenario_data,
        auth=True,
        expected_keys=["message", "scenario"]
    )
    
    if not set_scenario_test:
        print("❌ Failed to set scenario")
        return False, "Failed to set scenario"
    
    print("✅ Successfully set scenario")
    
    # Test 4: Generate multiple conversation rounds (8-10 exchanges)
    print("\nTest 4: Generating multiple conversation rounds")
    
    # Store all conversation rounds for analysis
    conversation_rounds = []
    
    # Generate 8 conversation rounds
    for i in range(8):
        print(f"\nGenerating conversation round {i+1}/8:")
        
        generate_data = {
            "round_number": i+1,
            "time_period": f"Day {i//3 + 1} {'Morning' if i%3==0 else 'Afternoon' if i%3==1 else 'Evening'}",
            "scenario": scenario_data["scenario"],
            "scenario_name": scenario_data["scenario_name"]
        }
        
        generate_test, generate_response = run_test(
            f"Generate Conversation Round {i+1}",
            "/conversation/generate",
            method="POST",
            data=generate_data,
            auth=True,
            expected_keys=["id", "round_number", "messages"]
        )
        
        if generate_test and generate_response:
            print(f"✅ Generated conversation round {i+1}")
            conversation_rounds.append(generate_response)
            
            # Print the messages for this round
            print("\nMessages in this round:")
            for msg in generate_response.get("messages", []):
                agent_name = msg.get("agent_name", "Unknown")
                message = msg.get("message", "")
                print(f"{agent_name}: {message[:100]}..." if len(message) > 100 else f"{agent_name}: {message}")
        else:
            print(f"❌ Failed to generate conversation round {i+1}")
    
    if len(conversation_rounds) < 6:
        print(f"❌ Failed to generate enough conversation rounds. Only generated {len(conversation_rounds)} out of 8.")
        return False, "Failed to generate enough conversation rounds"
    
    # Test 5: Analyze conversation for scenario repetition elimination
    print("\nTest 5: Analyzing conversation for scenario repetition elimination")
    
    # Extract scenario keywords
    scenario_keywords = set()
    for word in scenario_data["scenario"].lower().split():
        if len(word) > 4 and word not in ["the", "and", "with", "that", "this", "have", "from", "will", "would", "could", "should"]:
            scenario_keywords.add(word)
    
    print(f"Scenario keywords: {scenario_keywords}")
    
    # Check for scenario repetition in each round
    scenario_repetition_count = [0] * len(conversation_rounds)
    
    for i, round_data in enumerate(conversation_rounds):
        round_text = ""
        for message in round_data.get("messages", []):
            round_text += message.get("message", "").lower() + " "
        
        # Count scenario keywords in this round
        for keyword in scenario_keywords:
            if keyword in round_text:
                scenario_repetition_count[i] += 1
    
    print("\nScenario keyword count by round:")
    for i, count in enumerate(scenario_repetition_count):
        print(f"Round {i+1}: {count} scenario keywords")
    
    # First round should have more scenario keywords than later rounds
    if scenario_repetition_count[0] > sum(scenario_repetition_count[3:]) / len(scenario_repetition_count[3:]):
        print("✅ First round contains more scenario context than later rounds")
    else:
        print("❌ Scenario repetition not properly eliminated in later rounds")
    
    # Test 6: Analyze conversation state awareness
    print("\nTest 6: Analyzing conversation state awareness")
    
    # Define phase-specific keywords
    early_phase_keywords = ["understand", "analyze", "explore", "consider", "identify", "assess", "examine"]
    middle_phase_keywords = ["approach", "solution", "option", "alternative", "strategy", "method", "technique"]
    later_phase_keywords = ["implement", "plan", "timeline", "schedule", "assign", "responsibility", "action"]
    advanced_phase_keywords = ["progress", "update", "status", "complete", "finalize", "review", "refine"]
    
    # Count phase-specific keywords in each round
    phase_keyword_counts = []
    
    for round_data in conversation_rounds:
        round_text = ""
        for message in round_data.get("messages", []):
            round_text += message.get("message", "").lower() + " "
        
        early_count = sum(1 for word in early_phase_keywords if word in round_text)
        middle_count = sum(1 for word in middle_phase_keywords if word in round_text)
        later_count = sum(1 for word in later_phase_keywords if word in round_text)
        advanced_count = sum(1 for word in advanced_phase_keywords if word in round_text)
        
        phase_keyword_counts.append({
            "early": early_count,
            "middle": middle_count,
            "later": later_count,
            "advanced": advanced_count
        })
    
    print("\nPhase keyword counts by round:")
    for i, counts in enumerate(phase_keyword_counts):
        print(f"Round {i+1}: Early={counts['early']}, Middle={counts['middle']}, Later={counts['later']}, Advanced={counts['advanced']}")
    
    # Check if conversation progresses through phases
    early_rounds_avg = sum(counts["early"] for counts in phase_keyword_counts[:3]) / 3
    middle_rounds_avg = sum(counts["middle"] for counts in phase_keyword_counts[2:5]) / 3
    later_rounds_avg = sum(counts["later"] for counts in phase_keyword_counts[4:]) / min(3, len(phase_keyword_counts[4:]))
    
    if early_rounds_avg > middle_rounds_avg and later_rounds_avg > early_rounds_avg:
        print("✅ Conversation shows clear progression through different phases")
    else:
        print("❌ Conversation does not show clear phase progression")
    
    # Test 7: Analyze dynamic topic building
    print("\nTest 7: Analyzing dynamic topic building")
    
    # Check for references to previous speakers
    reference_count = 0
    total_messages = 0
    
    for round_data in conversation_rounds:
        messages = round_data.get("messages", [])
        for i, message in enumerate(messages):
            if i == 0:  # Skip first message in each round
                continue
                
            total_messages += 1
            message_text = message.get("message", "").lower()
            
            # Check for references to previous speakers
            for j in range(i):
                prev_speaker = messages[j].get("agent_name", "").split()[0]  # Get first name
                if prev_speaker.lower() in message_text:
                    reference_count += 1
                    print(f"Found reference to previous speaker: '{prev_speaker}' in '{message_text[:50]}...'")
                    break
    
    reference_percentage = (reference_count / total_messages) * 100 if total_messages > 0 else 0
    print(f"\nMessages referencing previous speakers: {reference_count}/{total_messages} ({reference_percentage:.1f}%)")
    
    if reference_percentage >= 25:
        print("✅ Agents build on specific previous points")
    else:
        print("❌ Agents don't sufficiently reference previous speakers")
    
    # Test 8: Analyze for natural human-like patterns
    print("\nTest 8: Analyzing for natural human-like patterns")
    
    # Check for incremental building on ideas
    incremental_building_patterns = [
        "building on", "to add to", "expanding on", "following up on", 
        "as mentioned by", "to continue", "in addition to", "furthermore",
        "moreover", "as we discussed", "earlier point", "previous point"
    ]
    
    incremental_building_count = 0
    
    for round_data in conversation_rounds:
        for message in round_data.get("messages", []):
            message_text = message.get("message", "").lower()
            for pattern in incremental_building_patterns:
                if pattern in message_text:
                    incremental_building_count += 1
                    print(f"Found incremental building: '{pattern}' in '{message_text[:50]}...'")
                    break
    
    incremental_percentage = (incremental_building_count / total_messages) * 100 if total_messages > 0 else 0
    print(f"\nMessages with incremental building: {incremental_building_count}/{total_messages} ({incremental_percentage:.1f}%)")
    
    if incremental_percentage >= 20:
        print("✅ Conversations show natural incremental building on ideas")
    else:
        print("❌ Conversations lack natural incremental building")
    
    # Test 9: Check for banned phrase detection
    print("\nTest 9: Checking for banned phrase detection")
    
    banned_phrases = [
        "we need to act urgently", "as you know", "the situation is",
        "we need to work together", "alright team", "as an expert in",
        "this is concerning", "this is interesting", "this is exciting",
        "let me share my perspective", "from my perspective", "in my experience"
    ]
    
    banned_phrase_count = 0
    
    for round_data in conversation_rounds:
        for message in round_data.get("messages", []):
            message_text = message.get("message", "").lower()
            for phrase in banned_phrases:
                if phrase in message_text:
                    banned_phrase_count += 1
                    print(f"Found banned phrase: '{phrase}' in '{message_text[:50]}...'")
                    break
    
    banned_percentage = (banned_phrase_count / total_messages) * 100 if total_messages > 0 else 0
    print(f"\nMessages with banned phrases: {banned_phrase_count}/{total_messages} ({banned_percentage:.1f}%)")
    
    if banned_percentage <= 10:
        print("✅ Enhanced filtering successfully catches banned phrases")
    else:
        print("❌ Too many banned phrases detected")
    
    # Test 10: Check for strategic question-answer dynamics
    print("\nTest 10: Checking for strategic question-answer dynamics")
    
    # Count strategic questions
    strategic_questions = 0
    direct_answers = 0
    collaborative_learning = 0
    
    # Track questions and their answers
    questions = []
    
    for round_idx, round_data in enumerate(conversation_rounds):
        messages = round_data.get("messages", [])
        
        # First pass: identify questions
        for msg_idx, message in enumerate(messages):
            message_text = message.get("message", "")
            agent_name = message.get("agent_name", "")
            
            # Check if message contains a question
            if "?" in message_text:
                # Check if it's a strategic question (mentions expertise or name)
                is_strategic = False
                target_agent = None
                
                for other_agent in created_agents:
                    other_name = other_agent.get("name", "").split()[0]  # First name
                    other_expertise = other_agent.get("expertise", "").lower()
                    
                    if (other_name in message_text and other_name != agent_name.split()[0]) or \
                       (other_expertise in message_text.lower()):
                        is_strategic = True
                        target_agent = other_name
                        break
                
                if is_strategic:
                    strategic_questions += 1
                    print(f"Found strategic question from {agent_name} to {target_agent}: '{message_text[:100]}...'")
                    
                    # Store question for answer tracking
                    questions.append({
                        "round": round_idx,
                        "msg_idx": msg_idx,
                        "asker": agent_name,
                        "target": target_agent,
                        "question": message_text,
                        "answered": False
                    })
        
        # Second pass: check for answers to previous questions
        for msg_idx, message in enumerate(messages):
            message_text = message.get("message", "")
            agent_name = message.get("agent_name", "")
            first_name = agent_name.split()[0]
            
            # Check if this message answers any previous question
            for q in questions:
                if not q["answered"] and q["target"] == first_name:
                    # Check if this message appears after the question
                    if q["round"] < round_idx or (q["round"] == round_idx and q["msg_idx"] < msg_idx):
                        # Check if message references question or asker
                        asker_name = q["asker"].split()[0]
                        if asker_name in message_text or any(phrase in message_text.lower() for phrase in ["to answer", "regarding your question", "you asked", "to your point"]):
                            direct_answers += 1
                            q["answered"] = True
                            print(f"Found direct answer from {agent_name} to {q['asker']}'s question")
            
            # Check for collaborative learning
            collaborative_phrases = [
                "hadn't considered that", "good point", "interesting perspective",
                "that changes my", "i see what you mean", "thanks for explaining",
                "learned something", "appreciate your insight", "hadn't thought of"
            ]
            
            if any(phrase in message_text.lower() for phrase in collaborative_phrases):
                collaborative_learning += 1
                print(f"Found collaborative learning in message from {agent_name}: '{message_text[:100]}...'")
    
    # Calculate percentages
    total_messages = sum(len(round_data.get("messages", [])) for round_data in conversation_rounds)
    strategic_question_percentage = (strategic_questions / total_messages) * 100 if total_messages > 0 else 0
    direct_answer_percentage = (direct_answers / strategic_questions) * 100 if strategic_questions > 0 else 0
    collaborative_learning_percentage = (collaborative_learning / total_messages) * 100 if total_messages > 0 else 0
    
    print(f"\nStrategic questions: {strategic_questions}/{total_messages} ({strategic_question_percentage:.1f}%)")
    print(f"Direct answers to questions: {direct_answers}/{strategic_questions} ({direct_answer_percentage:.1f}%)")
    print(f"Collaborative learning instances: {collaborative_learning}/{total_messages} ({collaborative_learning_percentage:.1f}%)")
    
    question_answer_success = strategic_question_percentage >= 15 and direct_answer_percentage >= 30 and collaborative_learning_percentage >= 10
    
    if question_answer_success:
        print("✅ Strategic question-answer dynamics are working well")
    else:
        print("❌ Strategic question-answer dynamics need improvement")
    
    # Print summary
    print("\nENHANCED DYNAMIC CONVERSATION SYSTEM SUMMARY:")
    
    # Check if all tests passed
    scenario_repetition_eliminated = scenario_repetition_count[0] > sum(scenario_repetition_count[3:]) / len(scenario_repetition_count[3:])
    conversation_state_aware = early_rounds_avg > middle_rounds_avg and later_rounds_avg > early_rounds_avg
    dynamic_topic_building = reference_percentage >= 25
    natural_patterns = incremental_percentage >= 20
    banned_phrase_filtering = banned_percentage <= 10
    
    if scenario_repetition_eliminated and conversation_state_aware and dynamic_topic_building and natural_patterns and banned_phrase_filtering:
        print("✅ Enhanced dynamic conversation system is working correctly!")
        print("✅ Scenario repetition is eliminated after first few exchanges")
        print("✅ Agents understand conversation progression through different phases")
        print("✅ Conversations show dynamic topic building")
        print("✅ Conversations display natural human-like patterns")
        print("✅ Enhanced filtering successfully catches banned phrases")
        
        if question_answer_success:
            print("✅ Strategic question-answer dynamics are working well")
        else:
            print("⚠️ Strategic question-answer dynamics need improvement")
            
        return True, "Enhanced dynamic conversation system is working correctly"
    else:
        issues = []
        if not scenario_repetition_eliminated:
            issues.append("Scenario repetition is not properly eliminated after first few exchanges")
        if not conversation_state_aware:
            issues.append("Agents don't show clear understanding of conversation progression")
        if not dynamic_topic_building:
            issues.append("Conversations lack dynamic topic building")
        if not natural_patterns:
            issues.append("Conversations don't display natural human-like patterns")
        if not banned_phrase_filtering:
            issues.append("Too many banned phrases detected")
        if not question_answer_success:
            issues.append("Strategic question-answer dynamics need improvement")
        
        print("❌ Enhanced dynamic conversation system has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}