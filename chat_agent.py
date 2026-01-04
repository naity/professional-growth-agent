#!/usr/bin/env python3
"""
Interactive Multi-Turn Meeting Coach
Allows follow-up questions and deeper exploration of meeting analysis.
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from claude_agent_sdk import ClaudeSDKClient, AssistantMessage, TextBlock
from prompts import get_agent_options, get_initial_prompt

# Load environment variables
load_dotenv()


async def interactive_meeting_coach(
    audio_path: str,
    user_role: str = "participant",
    analysis_type: str = "comprehensive"
):
    """
    Interactive meeting coach with multi-turn conversation support.
    
    Args:
        audio_path: Path to the meeting audio file
        user_role: Your role in the meeting
        analysis_type: Type of analysis to perform
    """
    
    # Validate audio file
    if not Path(audio_path).exists():
        print(f"❌ Error: Audio file not found: {audio_path}", file=sys.stderr)
        return
    
    print(f"🎯 Interactive Meeting Coach")
    print(f"📁 Audio file: {audio_path}")
    print(f"👤 Your role: {user_role}")
    print(f"📊 Analysis type: {analysis_type}")
    print("-" * 80)
    
    # Get consistent agent configuration for chat mode
    options = get_agent_options(mode="chat")
    options.cwd = str(Path(__file__).parent.absolute())
    
    # Build initial prompt using shared configuration
    audio_name = Path(audio_path).stem
    output_file = f"{audio_name}_analysis.md"
    initial_prompt = get_initial_prompt(audio_path, user_role, analysis_type, output_file, mode="chat")
    
    # Start the interactive session
    async with ClaudeSDKClient(options=options) as client:
        print("\n🤖 Agent is analyzing the meeting...\n")
        
        # Send initial analysis request
        await client.query(initial_prompt)
        
        # Show analysis progress
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
        
        print("\n" + "-" * 80)
        print(f"✅ Initial analysis saved to: {output_file}")
        print("-" * 80)
        
        # Interactive follow-up loop
        print("\n💬 You can now ask follow-up questions about the meeting.")
        print("   Type 'exit' or 'quit' to end the session.\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("\n👋 Thanks for using Meeting Coach! Your analysis is saved.")
                    break
                
                # Send follow-up question
                await client.query(user_input)
                
                # Stream response
                print("\nCoach: ", end="", flush=True)
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                print(block.text, end="", flush=True)
                print("\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Your analysis is saved.")
                break
            except EOFError:
                break


def main():
    """CLI entry point for interactive meeting coach."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Interactive Meeting Coach - Analyze meetings and ask follow-up questions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start interactive session
  python chat_agent.py meeting.mp3
  
  # Specify your role
  python chat_agent.py meeting.mp3 --role report
  
  # Use 1:1 focused analysis
  python chat_agent.py meeting.mp3 --type manager_1on1 --role report

After the initial analysis, you can ask questions like:
  - "What specific questions should I have asked?"
  - "How can I improve my active listening?"
  - "Give me a script for bringing up career development"
  - "What did I miss in this conversation?"
        """
    )
    
    parser.add_argument('audio_file', help='Path to the meeting audio file')
    
    parser.add_argument(
        '-r', '--role',
        choices=['participant', 'report', 'manager'],
        default='participant',
        help='Your role in the meeting'
    )
    
    parser.add_argument(
        '-t', '--type',
        choices=['comprehensive', 'quick', 'manager_1on1'],
        default='comprehensive',
        help='Type of analysis to perform'
    )
    
    args = parser.parse_args()
    
    # Run interactive session
    asyncio.run(interactive_meeting_coach(
        audio_path=args.audio_file,
        user_role=args.role,
        analysis_type=args.type
    ))


if __name__ == "__main__":
    main()

