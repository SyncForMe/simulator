#!/usr/bin/env python3
"""
Script to generate avatars for all agents in the library and update the AgentLibrary.js file
"""

import requests
import json
import re
import os
import time

# Backend URL
BACKEND_URL = "http://localhost:8001/api"

def generate_library_avatars():
    """Generate avatars for all library agents"""
    print("🎨 Starting avatar generation for library agents...")
    
    try:
        response = requests.post(f"{BACKEND_URL}/avatars/generate-library", timeout=300)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Avatar generation completed!")
        print(f"📊 Generated: {result['generated_count']}/{result['total_agents']} avatars")
        
        if result['errors']:
            print(f"⚠️  Errors encountered:")
            for error in result['errors']:
                print(f"   - {error}")
        
        return result['agents']
        
    except requests.exceptions.Timeout:
        print("⏰ Request timed out. Avatar generation may take a while...")
        return None
    except Exception as e:
        print(f"❌ Error generating avatars: {e}")
        return None

def update_agent_library_file(agents):
    """Update the AgentLibrary.js file with generated avatar URLs"""
    print("📝 Updating AgentLibrary.js with generated avatars...")
    
    agent_library_path = "/app/frontend/src/AgentLibrary.js"
    
    # Read the current file
    with open(agent_library_path, 'r') as f:
        content = f.read()
    
    # Create a mapping of agent names to avatar URLs
    avatar_mapping = {}
    for agent in agents:
        if 'avatar_url' in agent:
            avatar_mapping[agent['name']] = agent['avatar_url']
    
    # Update avatars in the file
    updated_count = 0
    for name, avatar_url in avatar_mapping.items():
        # Pattern to match agent with this name and update avatar field
        pattern = r'(name:\s*["\']' + re.escape(name) + r'["\'],[\s\S]*?)avatar:\s*["\'][^"\']*["\']'
        replacement = r'\1avatar: "' + avatar_url + '"'
        
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            content = new_content
            updated_count += 1
            print(f"   ✅ Updated avatar for {name}")
    
    # Write the updated content back to the file
    with open(agent_library_path, 'w') as f:
        f.write(content)
    
    print(f"📊 Updated {updated_count} agent avatars in AgentLibrary.js")
    return updated_count

def main():
    print("🚀 Starting Library Avatar Generation Process")
    print("=" * 50)
    
    # Generate avatars
    agents = generate_library_avatars()
    
    if agents:
        # Update the AgentLibrary.js file
        updated_count = update_agent_library_file(agents)
        
        print("=" * 50)
        print("🎉 Library Avatar Generation Complete!")
        print(f"📊 Total agents processed: {len(agents)}")
        print(f"📊 Avatars updated in library: {updated_count}")
        print("💡 Agents in the library now have persistent avatars!")
        
        # Restart frontend to reflect changes
        print("🔄 Restarting frontend to reflect changes...")
        os.system("sudo supervisorctl restart frontend")
        
    else:
        print("❌ Avatar generation failed. Please check the backend logs.")

if __name__ == "__main__":
    main()