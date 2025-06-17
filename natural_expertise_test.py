#!/usr/bin/env python3
"""
Test module for natural expertise demonstration system
"""

import requests
import json
import time
import os
import sys
from dotenv import load_dotenv
import uuid
import re

def test_natural_expertise(API_URL, auth_token, run_test):
    """Test the natural expertise demonstration system"""
    print("\n" + "="*80)
    print("TESTING NATURAL EXPERTISE DEMONSTRATION SYSTEM")
    print("="*80)
    
    # Check if we have auth token
    if not auth_token:
        print("❌ Cannot test natural expertise without authentication")
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
    
    # Test 4: Generate multiple conversation rounds
    print("\nTest 4: Generating multiple conversation rounds")
    
    # Store all conversation rounds for analysis
    conversation_rounds = []
    
    # Generate 6 conversation rounds
    for i in range(6):
        print(f"\nGenerating conversation round {i+1}/6:")
        
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
    
    if len(conversation_rounds) < 4:
        print(f"❌ Failed to generate enough conversation rounds. Only generated {len(conversation_rounds)} out of 6.")
        return False, "Failed to generate enough conversation rounds"
    
    # Test 5: Check for explicit background mentions
    print("\nTest 5: Checking for explicit background mentions")
    
    # Define patterns for explicit background mentions
    background_mention_patterns = [
        r"as an? (expert|specialist|professional|authority|leader) in",
        r"given my (background|experience|expertise|knowledge|training) in",
        r"from my (experience|perspective|background|expertise|viewpoint) in",
        r"based on my (\d+|several|many|extensive|years of) (years|experience)",
        r"speaking as an? (expert|specialist|professional|authority|leader)",
        r"as someone (who|with) (has|have|having)",
        r"with my (expertise|experience|background|knowledge|training) in",
        r"given my professional (experience|background|expertise|knowledge)",
        r"in my (field|profession|discipline|area of expertise)",
        r"as a (quantum physicist|project manager|risk analyst|business developer)"
    ]
    
    # Count background mentions by agent and round
    background_mentions = {agent.get("name", "Unknown"): 0 for agent in created_agents}
    background_mentions_by_round = [0] * len(conversation_rounds)
    background_mention_examples = []
    
    for round_idx, round_data in enumerate(conversation_rounds):
        for message in round_data.get("messages", []):
            agent_name = message.get("agent_name", "Unknown")
            message_text = message.get("message", "")
            
            for pattern in background_mention_patterns:
                matches = re.finditer(pattern, message_text.lower())
                for match in matches:
                    background_mentions[agent_name] = background_mentions.get(agent_name, 0) + 1
                    background_mentions_by_round[round_idx] = background_mentions_by_round[round_idx] + 1
                    background_mention_examples.append({
                        "round": round_idx + 1,
                        "agent": agent_name,
                        "pattern": pattern,
                        "text": message_text[max(0, match.start() - 20):min(len(message_text), match.end() + 20)]
                    })
    
    # Print background mention statistics
    print("\nBackground mentions by agent:")
    for agent_name, count in background_mentions.items():
        print(f"{agent_name}: {count} mentions")
    
    print("\nBackground mentions by round:")
    for i, count in enumerate(background_mentions_by_round):
        print(f"Round {i+1}: {count} mentions")
    
    if background_mention_examples:
        print("\nExamples of background mentions:")
        for example in background_mention_examples[:5]:  # Show up to 5 examples
            print(f"Round {example['round']}, {example['agent']}: \"...{example['text']}...\"")
    
    total_background_mentions = sum(background_mentions.values())
    total_messages = sum(len(round_data.get("messages", [])) for round_data in conversation_rounds)
    background_mention_percentage = (total_background_mentions / total_messages) * 100 if total_messages > 0 else 0
    
    print(f"\nTotal background mentions: {total_background_mentions}/{total_messages} messages ({background_mention_percentage:.1f}%)")
    
    if background_mention_percentage <= 5:
        print("✅ Agents rarely mention their background explicitly")
    else:
        print("❌ Agents frequently mention their background explicitly")
    
    # Test 6: Check for natural expertise demonstration
    print("\nTest 6: Checking for natural expertise demonstration")
    
    # Define expertise-specific terminology for each field
    expertise_terminology = {
        "Quantum Physics": ["coherence", "entanglement", "superposition", "qubit", "decoherence", "quantum state", "error correction", "quantum gate", "interference", "measurement"],
        "Project Management": ["critical path", "milestone", "resource allocation", "deliverable", "stakeholder", "scope", "timeline", "dependencies", "gantt", "risk mitigation"],
        "Risk Assessment": ["threat vector", "vulnerability", "probability matrix", "impact analysis", "mitigation strategy", "contingency", "risk factor", "security protocol", "compliance", "audit"],
        "Business Development": ["market penetration", "scalability", "value proposition", "ROI", "competitive advantage", "market segment", "customer acquisition", "revenue stream", "partnership", "growth strategy"]
    }
    
    # Count natural expertise demonstrations by agent
    expertise_demonstrations = {agent.get("name", "Unknown"): 0 for agent in created_agents}
    expertise_demonstration_examples = []
    
    for agent in created_agents:
        agent_name = agent.get("name", "Unknown")
        agent_expertise = agent.get("expertise", "")
        
        if agent_expertise in expertise_terminology:
            terminology = expertise_terminology[agent_expertise]
            
            for round_data in conversation_rounds:
                for message in round_data.get("messages", []):
                    if message.get("agent_name", "") == agent_name:
                        message_text = message.get("message", "").lower()
                        
                        for term in terminology:
                            if term.lower() in message_text:
                                expertise_demonstrations[agent_name] = expertise_demonstrations.get(agent_name, 0) + 1
                                expertise_demonstration_examples.append({
                                    "agent": agent_name,
                                    "expertise": agent_expertise,
                                    "term": term,
                                    "text": message_text
                                })
                                break  # Count only one demonstration per message
    
    # Print expertise demonstration statistics
    print("\nNatural expertise demonstrations by agent:")
    for agent_name, count in expertise_demonstrations.items():
        agent_messages = sum(1 for round_data in conversation_rounds for message in round_data.get("messages", []) if message.get("agent_name", "") == agent_name)
        demonstration_percentage = (count / agent_messages) * 100 if agent_messages > 0 else 0
        print(f"{agent_name}: {count}/{agent_messages} messages ({demonstration_percentage:.1f}%)")
    
    if expertise_demonstration_examples:
        print("\nExamples of natural expertise demonstrations:")
        for example in expertise_demonstration_examples[:4]:  # Show up to 4 examples
            print(f"{example['agent']} ({example['expertise']}): Used term '{example['term']}' in message:")
            print(f"  \"{example['text'][:150]}...\"" if len(example['text']) > 150 else f"  \"{example['text']}\"")
    
    total_demonstrations = sum(expertise_demonstrations.values())
    demonstration_percentage = (total_demonstrations / total_messages) * 100 if total_messages > 0 else 0
    
    print(f"\nTotal natural expertise demonstrations: {total_demonstrations}/{total_messages} messages ({demonstration_percentage:.1f}%)")
    
    if demonstration_percentage >= 50:
        print("✅ Agents naturally demonstrate expertise through terminology")
    else:
        print("❌ Agents don't sufficiently demonstrate expertise through terminology")
    
    # Test 7: Check for professional communication patterns
    print("\nTest 7: Checking for professional communication patterns")
    
    # Define professional communication patterns by field
    professional_patterns = {
        "Quantum Physics": [
            r"coherence times? (of|above|below|around|approximately) \d+",
            r"(entanglement|superposition) (state|quality|measure|degree|level)",
            r"(error correction|error rate) (protocol|approach|method|technique|strategy)",
            r"(qubit|quantum state) (stability|fidelity|quality|coherence|measurement)"
        ],
        "Project Management": [
            r"critical path (analysis|method|calculation|determination)",
            r"resource (allocation|distribution|assignment|management)",
            r"milestone (dependencies|timeline|schedule|tracking|achievement)",
            r"(stakeholder|team) (management|coordination|communication|alignment)"
        ],
        "Risk Assessment": [
            r"(threat|risk) (vector|matrix|assessment|analysis|profile)",
            r"(probability|likelihood) (matrix|assessment|calculation|estimation)",
            r"mitigation (strategy|plan|approach|method|technique)",
            r"(security|vulnerability) (protocol|assessment|analysis|audit)"
        ],
        "Business Development": [
            r"market (penetration|analysis|segment|opportunity|strategy)",
            r"(value proposition|competitive advantage) (development|enhancement|refinement)",
            r"(customer|client) (acquisition|retention|satisfaction|engagement)",
            r"(revenue|growth) (stream|strategy|projection|forecast|model)"
        ]
    }
    
    # Count professional communication patterns by agent
    professional_patterns_count = {agent.get("name", "Unknown"): 0 for agent in created_agents}
    professional_pattern_examples = []
    
    for agent in created_agents:
        agent_name = agent.get("name", "Unknown")
        agent_expertise = agent.get("expertise", "")
        
        if agent_expertise in professional_patterns:
            patterns = professional_patterns[agent_expertise]
            
            for round_data in conversation_rounds:
                for message in round_data.get("messages", []):
                    if message.get("agent_name", "") == agent_name:
                        message_text = message.get("message", "")
                        
                        for pattern in patterns:
                            matches = re.search(pattern, message_text.lower())
                            if matches:
                                professional_patterns_count[agent_name] = professional_patterns_count.get(agent_name, 0) + 1
                                professional_pattern_examples.append({
                                    "agent": agent_name,
                                    "expertise": agent_expertise,
                                    "pattern": pattern,
                                    "text": message_text
                                })
                                break  # Count only one pattern per message
    
    # Print professional communication pattern statistics
    print("\nProfessional communication patterns by agent:")
    for agent_name, count in professional_patterns_count.items():
        agent_messages = sum(1 for round_data in conversation_rounds for message in round_data.get("messages", []) if message.get("agent_name", "") == agent_name)
        pattern_percentage = (count / agent_messages) * 100 if agent_messages > 0 else 0
        print(f"{agent_name}: {count}/{agent_messages} messages ({pattern_percentage:.1f}%)")
    
    if professional_pattern_examples:
        print("\nExamples of professional communication patterns:")
        for example in professional_pattern_examples[:4]:  # Show up to 4 examples
            print(f"{example['agent']} ({example['expertise']}): Used professional pattern in message:")
            print(f"  \"{example['text'][:150]}...\"" if len(example['text']) > 150 else f"  \"{example['text']}\"")
    
    total_patterns = sum(professional_patterns_count.values())
    pattern_percentage = (total_patterns / total_messages) * 100 if total_messages > 0 else 0
    
    print(f"\nTotal professional communication patterns: {total_patterns}/{total_messages} messages ({pattern_percentage:.1f}%)")
    
    if pattern_percentage >= 30:
        print("✅ Agents use professional communication patterns")
    else:
        print("❌ Agents don't sufficiently use professional communication patterns")
    
    # Test 8: Check for implicit vs explicit expertise
    print("\nTest 8: Checking for implicit vs explicit expertise")
    
    # Define patterns for explicit vs implicit expertise
    explicit_expertise_patterns = [
        r"as an? (expert|specialist|professional) in",
        r"from my (experience|perspective|background|expertise)",
        r"based on my (experience|knowledge|training|background)",
        r"in my (professional opinion|assessment|judgment|evaluation)",
        r"with my (expertise|experience|background|knowledge)"
    ]
    
    implicit_expertise_patterns = {
        "Quantum Physics": [
            r"we need (error correction|quantum gates|entanglement|coherence)",
            r"the (quantum state|qubit stability|decoherence rate|entanglement fidelity)",
            r"(implementing|designing|optimizing) (quantum circuits|error correction|quantum gates)",
            r"(measuring|calculating|estimating) (coherence times|error rates|qubit fidelity)"
        ],
        "Project Management": [
            r"the critical path (shows|indicates|suggests|requires)",
            r"(allocating|distributing|assigning) resources (to|for|across|between)",
            r"(tracking|monitoring|achieving) milestones (will|should|must|can)",
            r"(stakeholder|team) (alignment|coordination|communication) (is|remains|becomes)"
        ],
        "Risk Assessment": [
            r"(identifying|analyzing|mitigating) (threats|risks|vulnerabilities)",
            r"the (probability|likelihood|impact) (matrix|assessment|calculation)",
            r"(implementing|designing|establishing) (security protocols|mitigation strategies)",
            r"(conducting|performing|completing) (risk assessments|vulnerability audits)"
        ],
        "Business Development": [
            r"(analyzing|targeting|penetrating) (markets|segments|demographics)",
            r"(developing|enhancing|refining) (value propositions|competitive advantages)",
            r"(acquiring|retaining|engaging) (customers|clients|users)",
            r"(projecting|forecasting|modeling) (revenue|growth|adoption)"
        ]
    }
    
    # Count explicit vs implicit expertise by agent
    explicit_expertise_count = {agent.get("name", "Unknown"): 0 for agent in created_agents}
    implicit_expertise_count = {agent.get("name", "Unknown"): 0 for agent in created_agents}
    
    for agent in created_agents:
        agent_name = agent.get("name", "Unknown")
        agent_expertise = agent.get("expertise", "")
        
        for round_data in conversation_rounds:
            for message in round_data.get("messages", []):
                if message.get("agent_name", "") == agent_name:
                    message_text = message.get("message", "")
                    
                    # Check for explicit expertise
                    for pattern in explicit_expertise_patterns:
                        if re.search(pattern, message_text.lower()):
                            explicit_expertise_count[agent_name] = explicit_expertise_count.get(agent_name, 0) + 1
                            break
                    
                    # Check for implicit expertise
                    if agent_expertise in implicit_expertise_patterns:
                        for pattern in implicit_expertise_patterns[agent_expertise]:
                            if re.search(pattern, message_text.lower()):
                                implicit_expertise_count[agent_name] = implicit_expertise_count.get(agent_name, 0) + 1
                                break
    
    # Print explicit vs implicit expertise statistics
    print("\nExplicit vs Implicit expertise by agent:")
    for agent_name in explicit_expertise_count.keys():
        explicit_count = explicit_expertise_count.get(agent_name, 0)
        implicit_count = implicit_expertise_count.get(agent_name, 0)
        agent_messages = sum(1 for round_data in conversation_rounds for message in round_data.get("messages", []) if message.get("agent_name", "") == agent_name)
        
        explicit_percentage = (explicit_count / agent_messages) * 100 if agent_messages > 0 else 0
        implicit_percentage = (implicit_count / agent_messages) * 100 if agent_messages > 0 else 0
        
        print(f"{agent_name}:")
        print(f"  Explicit: {explicit_count}/{agent_messages} messages ({explicit_percentage:.1f}%)")
        print(f"  Implicit: {implicit_count}/{agent_messages} messages ({implicit_percentage:.1f}%)")
    
    total_explicit = sum(explicit_expertise_count.values())
    total_implicit = sum(implicit_expertise_count.values())
    
    explicit_percentage = (total_explicit / total_messages) * 100 if total_messages > 0 else 0
    implicit_percentage = (total_implicit / total_messages) * 100 if total_messages > 0 else 0
    
    print(f"\nTotal explicit expertise: {total_explicit}/{total_messages} messages ({explicit_percentage:.1f}%)")
    print(f"Total implicit expertise: {total_implicit}/{total_messages} messages ({implicit_percentage:.1f}%)")
    
    if implicit_percentage > explicit_percentage:
        print("✅ Agents favor implicit expertise over explicit credentials")
    else:
        print("❌ Agents use explicit credentials more than implicit expertise")
    
    # Print summary
    print("\nNATURAL EXPERTISE DEMONSTRATION SUMMARY:")
    
    # Check if all tests passed
    no_background_mentions = background_mention_percentage <= 5
    natural_expertise = demonstration_percentage >= 50
    professional_communication = pattern_percentage >= 30
    implicit_over_explicit = implicit_percentage > explicit_percentage
    
    if no_background_mentions and natural_expertise and professional_communication and implicit_over_explicit:
        print("✅ Natural expertise demonstration system is working correctly!")
        print("✅ Agents rarely mention their background explicitly")
        print("✅ Agents naturally demonstrate expertise through terminology")
        print("✅ Agents use professional communication patterns")
        print("✅ Agents favor implicit expertise over explicit credentials")
        return True, "Natural expertise demonstration system is working correctly"
    else:
        issues = []
        if not no_background_mentions:
            issues.append(f"Agents mention their background explicitly in {background_mention_percentage:.1f}% of messages (target: ≤5%)")
        if not natural_expertise:
            issues.append(f"Agents only demonstrate expertise through terminology in {demonstration_percentage:.1f}% of messages (target: ≥50%)")
        if not professional_communication:
            issues.append(f"Agents only use professional communication patterns in {pattern_percentage:.1f}% of messages (target: ≥30%)")
        if not implicit_over_explicit:
            issues.append(f"Agents use explicit credentials ({explicit_percentage:.1f}%) more than implicit expertise ({implicit_percentage:.1f}%)")
        
        print("❌ Natural expertise demonstration system has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}