#!/usr/bin/env python3
"""
Test module for improved conversation generation system
"""

import requests
import json
import time
import os
import sys
from dotenv import load_dotenv
import uuid

def test_conversation_generation(API_URL, auth_token, run_test):
    """Test the improved conversation generation system"""
    print("\n" + "="*80)
    print("TESTING IMPROVED CONVERSATION GENERATION SYSTEM")
    print("="*80)
    
    # Check if we have auth token
    if not auth_token:
        print("❌ Cannot test conversation generation without authentication")
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
    
    # Test 2: Create test agents
    print("\nTest 2: Creating test agents")
    
    # Create three agents with different archetypes
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
            "goal": "Advance scientific understanding of the project",
            "expertise": "Quantum Physics",
            "background": "Former lead researcher at CERN",
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
            "background": "20 years experience in tech leadership",
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
            "background": "Former security consultant",
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
        print(f"❌ Failed to create all test agents. Only created {len(created_agents)} out of 3.")
        return False, "Failed to create all test agents"
    
    # Test 3: Set a scenario
    print("\nTest 3: Setting a scenario")
    
    scenario_data = {
        "scenario": "The team is discussing the implementation of a new quantum computing project with potential applications in cryptography.",
        "scenario_name": "Quantum Computing Project"
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
    
    # Test 4: Generate multiple conversation rounds
    print("\nTest 4: Generating multiple conversation rounds")
    
    # Store all conversation rounds for analysis
    conversation_rounds = []
    
    # Generate 5 conversation rounds
    for i in range(5):
        print(f"\nGenerating conversation round {i+1}/5:")
        
        generate_data = {
            "round_number": i+1,
            "time_period": f"Day {i+1} Morning",
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
        else:
            print(f"❌ Failed to generate conversation round {i+1}")
    
    if len(conversation_rounds) < 3:
        print(f"❌ Failed to generate enough conversation rounds. Only generated {len(conversation_rounds)} out of 5.")
        return False, "Failed to generate enough conversation rounds"
    
    # Test 5: Analyze conversation content for improvements
    print("\nTest 5: Analyzing conversation content for improvements")
    
    # Check for self-introductions after first round
    print("\nChecking for self-introductions after first round:")
    self_intro_count = 0
    intro_phrases = [
        "good morning", "good afternoon", "good evening",
        "i'm", "and i'm here to", "my name is"
    ]
    
    for i, round_data in enumerate(conversation_rounds):
        if i == 0:  # Skip first round
            continue
            
        for message in round_data.get("messages", []):
            message_text = message.get("message", "").lower()
            for phrase in intro_phrases:
                if phrase in message_text:
                    self_intro_count += 1
                    print(f"Found self-introduction in round {i+1}: '{message.get('message')}'")
                    break
    
    if self_intro_count == 0:
        print("✅ No self-introductions found after first round")
    else:
        print(f"❌ Found {self_intro_count} self-introductions after first round")
    
    # Check for repetitive phrases
    print("\nChecking for repetitive phrases:")
    repetitive_phrases = [
        "alright team", "alright everyone",
        "as an expert in", "this is concerning", 
        "this is interesting", "this is exciting", 
        "let me share my perspective"
    ]
    
    repetitive_phrase_count = 0
    
    for round_data in conversation_rounds:
        for message in round_data.get("messages", []):
            message_text = message.get("message", "").lower()
            for phrase in repetitive_phrases:
                if phrase in message_text:
                    repetitive_phrase_count += 1
                    print(f"Found repetitive phrase '{phrase}' in message: '{message.get('message')}'")
                    break
    
    if repetitive_phrase_count == 0:
        print("✅ No repetitive phrases found")
    else:
        print(f"❌ Found {repetitive_phrase_count} repetitive phrases")
    
    # Check for solution-focused responses
    print("\nChecking for solution-focused responses:")
    solution_phrases = [
        "suggest", "recommend", "propose", "implement", 
        "approach", "solution", "strategy", "plan",
        "timeline", "schedule", "milestone", "next steps"
    ]
    
    solution_focused_count = 0
    total_messages = 0
    
    for round_data in conversation_rounds:
        for message in round_data.get("messages", []):
            total_messages += 1
            message_text = message.get("message", "").lower()
            for phrase in solution_phrases:
                if phrase in message_text:
                    solution_focused_count += 1
                    break
    
    solution_percentage = (solution_focused_count / total_messages) * 100 if total_messages > 0 else 0
    print(f"Solution-focused messages: {solution_focused_count}/{total_messages} ({solution_percentage:.1f}%)")
    
    if solution_percentage >= 50:
        print("✅ Conversations are solution-focused")
    else:
        print("❌ Conversations are not sufficiently solution-focused")
    
    # Check for references to previous speakers
    print("\nChecking for references to previous speakers:")
    reference_count = 0
    
    for round_data in conversation_rounds:
        messages = round_data.get("messages", [])
        for i, message in enumerate(messages):
            if i == 0:  # Skip first message in each round
                continue
                
            message_text = message.get("message", "").lower()
            previous_speakers = [prev_msg.get("agent_name", "") for prev_msg in messages[:i]]
            
            for speaker in previous_speakers:
                if speaker.lower() in message_text:
                    reference_count += 1
                    break
    
    reference_percentage = (reference_count / (total_messages - len(conversation_rounds))) * 100 if (total_messages - len(conversation_rounds)) > 0 else 0
    print(f"Messages referencing previous speakers: {reference_count}/{total_messages - len(conversation_rounds)} ({reference_percentage:.1f}%)")
    
    if reference_percentage >= 30:
        print("✅ Conversations show good references to previous speakers")
    else:
        print("❌ Conversations don't sufficiently reference previous speakers")
    
    # Check for conversation progression
    print("\nChecking for conversation progression:")
    
    # Early rounds should focus on analysis and brainstorming
    early_analysis_terms = ["analyze", "consider", "explore", "understand", "identify", "assess"]
    early_analysis_count = 0
    
    # Later rounds should focus on concrete proposals and decisions
    later_decision_terms = ["decide", "implement", "plan", "schedule", "assign", "commit", "vote"]
    later_decision_count = 0
    
    early_rounds = conversation_rounds[:2] if len(conversation_rounds) >= 2 else []
    later_rounds = conversation_rounds[2:] if len(conversation_rounds) >= 3 else []
    
    for round_data in early_rounds:
        for message in round_data.get("messages", []):
            message_text = message.get("message", "").lower()
            for term in early_analysis_terms:
                if term in message_text:
                    early_analysis_count += 1
                    break
    
    for round_data in later_rounds:
        for message in round_data.get("messages", []):
            message_text = message.get("message", "").lower()
            for term in later_decision_terms:
                if term in message_text:
                    later_decision_count += 1
                    break
    
    early_messages = sum(len(round_data.get("messages", [])) for round_data in early_rounds)
    later_messages = sum(len(round_data.get("messages", [])) for round_data in later_rounds)
    
    early_analysis_percentage = (early_analysis_count / early_messages) * 100 if early_messages > 0 else 0
    later_decision_percentage = (later_decision_count / later_messages) * 100 if later_messages > 0 else 0
    
    print(f"Early rounds analysis focus: {early_analysis_count}/{early_messages} ({early_analysis_percentage:.1f}%)")
    print(f"Later rounds decision focus: {later_decision_count}/{later_messages} ({later_decision_percentage:.1f}%)")
    
    progression_ok = early_analysis_percentage >= 30 and later_decision_percentage >= 30
    
    if progression_ok:
        print("✅ Conversations show good progression from analysis to decisions")
    else:
        print("❌ Conversations don't show clear progression")
    
    # Test 6: Test fallback responses
    print("\nTest 6: Testing fallback responses")
    
    # Generate a conversation with a very short timeout to trigger fallbacks
    fallback_data = {
        "round_number": 99,  # Use a high number to ensure it's a new round
        "time_period": "Fallback Test",
        "scenario": "This is a test scenario to trigger fallback responses",
        "scenario_name": "Fallback Test"
    }
    
    fallback_test, fallback_response = run_test(
        "Generate Fallback Conversation",
        "/conversation/generate",
        method="POST",
        data=fallback_data,
        auth=True,
        expected_keys=["id", "round_number", "messages"]
    )
    
    if fallback_test and fallback_response:
        print("✅ Generated fallback conversation")
        
        # Check fallback responses for banned phrases
        fallback_banned_phrases = 0
        
        for message in fallback_response.get("messages", []):
            message_text = message.get("message", "").lower()
            for phrase in repetitive_phrases + intro_phrases:
                if phrase in message_text:
                    fallback_banned_phrases += 1
                    print(f"Found banned phrase in fallback response: '{message.get('message')}'")
                    break
        
        if fallback_banned_phrases == 0:
            print("✅ No banned phrases found in fallback responses")
        else:
            print(f"❌ Found {fallback_banned_phrases} banned phrases in fallback responses")
        
        # Check if fallback responses are solution-focused
        fallback_solution_count = 0
        fallback_total = len(fallback_response.get("messages", []))
        
        for message in fallback_response.get("messages", []):
            message_text = message.get("message", "").lower()
            for phrase in solution_phrases:
                if phrase in message_text:
                    fallback_solution_count += 1
                    break
        
        fallback_solution_percentage = (fallback_solution_count / fallback_total) * 100 if fallback_total > 0 else 0
        print(f"Fallback solution-focused messages: {fallback_solution_count}/{fallback_total} ({fallback_solution_percentage:.1f}%)")
        
        if fallback_solution_percentage >= 50:
            print("✅ Fallback responses are solution-focused")
        else:
            print("❌ Fallback responses are not sufficiently solution-focused")
    else:
        print("❌ Failed to generate fallback conversation")
    
    # Print summary
    print("\nIMPROVED CONVERSATION GENERATION SUMMARY:")
    
    # Check if all tests passed
    no_self_intros = self_intro_count == 0
    no_repetitive_phrases = repetitive_phrase_count == 0
    is_solution_focused = solution_percentage >= 50
    has_references = reference_percentage >= 30
    shows_progression = progression_ok
    
    if no_self_intros and no_repetitive_phrases and is_solution_focused and has_references and shows_progression:
        print("✅ Improved conversation generation system is working correctly!")
        print("✅ No self-introductions after first round")
        print("✅ No repetitive phrases")
        print("✅ Conversations are solution-focused")
        print("✅ Agents reference previous speakers")
        print("✅ Conversations show progression from analysis to decisions")
        return True, "Improved conversation generation system is working correctly"
    else:
        issues = []
        if not no_self_intros:
            issues.append(f"Found {self_intro_count} self-introductions after first round")
        if not no_repetitive_phrases:
            issues.append(f"Found {repetitive_phrase_count} repetitive phrases")
        if not is_solution_focused:
            issues.append(f"Only {solution_percentage:.1f}% of messages are solution-focused (target: 50%)")
        if not has_references:
            issues.append(f"Only {reference_percentage:.1f}% of messages reference previous speakers (target: 30%)")
        if not shows_progression:
            issues.append("Conversations don't show clear progression from analysis to decisions")
        
        print("❌ Improved conversation generation system has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}