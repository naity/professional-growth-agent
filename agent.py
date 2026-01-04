#!/usr/bin/env python3
"""
Meeting Coach Agent
Analyzes meeting recordings and provides constructive feedback.

This agent uses Claude via Amazon Bedrock to:
1. Transcribe meeting audio using AWS Transcribe
2. Analyze conversation patterns
3. Provide actionable feedback and insights
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

# Load environment variables from .env file
load_dotenv()


def get_analysis_prompt(
    audio_path: str, 
    analysis_type: str = "comprehensive",
    user_role: str = "participant",
    output_file: str = "analysis.md"
) -> str:
    """
    Generate the appropriate analysis prompt based on the type of analysis requested.
    
    Args:
        audio_path: Path to the audio file
        analysis_type: Type of analysis (comprehensive, quick, specific)
    
    Returns:
        Formatted prompt for the agent
    """
    
    # Determine perspective based on user role
    perspective = ""
    if user_role == "report":
        perspective = "I am the more junior person in this meeting (direct report or skip-level). "
    elif user_role == "manager":
        perspective = "I am the more senior person in this meeting. "
    else:  # participant or any other
        perspective = "I am one of the participants in this meeting. "
    
    base_prompt = f"""
I have a meeting recording at: {audio_path}

{perspective}Transcribe this meeting and write your analysis directly to: {output_file}

Focus on actionable feedback to help ME improve my communication and get more value from future meetings.

When analyzing:
- Refer to speakers neutrally (Speaker A, Speaker B, or by speaker labels like spk_0, spk_1)
- Focus on what I can control and improve
- Provide actionable suggestions for MY behavior
- Don't make assumptions about roles or relationships unless I specify them
"""
    
    if analysis_type == "comprehensive":
        base_prompt += """
Provide a comprehensive analysis including:

1. **Meeting Summary**
   - Key topics discussed
   - Main decisions made
   - Overall meeting tone

2. **Speaking Patterns**
   - Who spoke more/less
   - Speaking time distribution
   - Any interruptions or speaking over each other

3. **Communication Quality**
   - Active listening indicators (acknowledgments, follow-up questions)
   - Question quality (open-ended vs closed, clarifying vs leading)
   - Clarity of communication

4. **Action Items & Next Steps**
   - Explicit action items mentioned
   - Ownership clarity (who is responsible for what)
   - Timeline discussions

5. **Constructive Feedback**
   - What went well in this meeting
   - Areas for improvement
   - Specific suggestions for the next meeting

6. **Emotional Intelligence & Tone**
   - Collaborative vs directive tone
   - Empathy and understanding shown
   - Psychological safety indicators

Please be specific and provide examples from the transcript to support your observations.
"""
    
    elif analysis_type == "quick":
        base_prompt += """
Provide a quick analysis covering:
- 3 key takeaways
- Main action items
- One suggestion for improvement
"""
    
    elif analysis_type == "manager_1on1":
        base_prompt += """
Analyze this 1:1 meeting with a focus on helping ME be more effective:

1. **My Communication Effectiveness**
   - Did I speak enough? Too much? Was my input balanced?
   - Quality of my contributions vs just responding

2. **My Questions**
   - What questions did I ask? Were they strategic or tactical?
   - Did I seek feedback, clarification, or guidance?
   - What questions should I have asked but didn't?

3. **My Active Listening**
   - Did I acknowledge and build on what was said?
   - Did I miss opportunities to engage deeper?
   - Areas where I could have asked for clarification

4. **Career Development Discussion**
   - Did I bring up my growth and development?
   - Did I miss signals about expectations or opportunities?

5. **My Action Items Clarity**
   - Are MY next steps clear?
   - Did I clarify priorities and timelines?

6. **What I Can Do Better Next Time**
   - Specific behaviors I should change
   - Questions I should prepare
   - How I can make the meeting more valuable for my growth
"""
    
    return base_prompt


async def run_meeting_analysis(
    audio_path: str,
    analysis_type: str = "comprehensive",
    user_role: str = "participant",
    output_file: str = None,
    verbose: bool = True
):
    """
    Run the meeting analysis agent.
    
    Args:
        audio_path: Path to the meeting audio file
        analysis_type: Type of analysis to perform
        user_role: User's role in the meeting (participant, report, manager)
        output_file: Path to save the analysis (default: auto-generated markdown file)
        verbose: Whether to print progress messages
    """
    
    # Validate audio file exists
    if not Path(audio_path).exists():
        print(f"❌ Error: Audio file not found: {audio_path}", file=sys.stderr)
        return
    
    # Generate output filename if not provided
    if output_file is None:
        audio_name = Path(audio_path).stem
        output_file = f"{audio_name}_analysis.md"
    
    if verbose:
        print(f"🎯 Starting Meeting Coach Agent")
        print(f"📁 Audio file: {audio_path}")
        print(f"📊 Analysis type: {analysis_type}")
        print(f"👤 Your role: {user_role}")
        print(f"📄 Output file: {output_file}")
        print("-" * 80)
    
    # Configure the agent
    options = ClaudeAgentOptions(
        # Enable tools: Skill for transcription, Write for saving analysis, Read and Bash for other tasks
        allowed_tools=["Skill", "Read", "Write", "Bash"],
        
        # Load skills from the project directory
        setting_sources=["project"],
        
        # Use Bedrock permissions mode - auto-approve since transcription is safe
        permission_mode="acceptEdits",
        
        # Set working directory to project root
        cwd=str(Path(__file__).parent.absolute()),
        
        # Custom system prompt to guide the agent
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": """
You are a Meeting Coach - an expert at analyzing meetings and providing constructive feedback.

When analyzing meetings:
- Be specific and use examples from the transcript
- Focus on actionable insights, not just observations
- Be constructive and encouraging, not just critical
- Consider both verbal content and communication patterns
- Think about power dynamics and psychological safety

Your goal is to help people have better, more productive meetings.
"""
        }
    )
    
    # Generate the analysis prompt (includes instruction to save to file)
    prompt = get_analysis_prompt(audio_path, analysis_type, user_role, output_file)
    
    if verbose:
        print("\n🤖 Agent is working...\n")
    
    # Track metrics
    cost = None
    duration = None
    
    # Stream the agent's response
    async for message in query(prompt=prompt, options=options):
        # Print assistant messages as they come in
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    if verbose:
                        print(block.text)
        
        # Capture result summary
        if hasattr(message, 'subtype') and message.subtype in ['success', 'error']:
            if hasattr(message, 'total_cost_usd'):
                cost = message.total_cost_usd
            if hasattr(message, 'duration_ms'):
                duration = message.duration_ms
    
    # Agent has written the file itself!
    if verbose:
        print("\n" + "-" * 80)
        print(f"✅ Analysis saved to: {output_file}")
        if cost:
            print(f"💰 Cost: ${cost:.4f}")
        if duration:
            print(f"⏱️  Duration: {duration / 1000:.1f}s")
        print("-" * 80)
        print(f"\nTo read the analysis:")
        print(f"  cat {output_file}")
        print(f"  # or open in your editor/markdown viewer")


def main():
    """Main entry point for the CLI."""
    import argparse
    
    # Verify environment configuration
    required_vars = ['AWS_REGION', 'CLAUDE_CODE_USE_BEDROCK', 'MEETING_TRANSCRIBE_S3_BUCKET']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"❌ Error: Missing required environment variables: {', '.join(missing_vars)}", 
              file=sys.stderr)
        print("Make sure your .env file is configured properly.", file=sys.stderr)
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description="Meeting Coach Agent - Analyze meeting recordings with AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Comprehensive analysis (you as generic participant)
  python agent.py recording.mp3
  
  # Specify your role as report (works for both direct and skip-level)
  python agent.py recording.mp3 --role report
  
  # 1:1 meeting analysis
  python agent.py recording.mp3 --type manager_1on1 --role report
  
  # Custom output file
  python agent.py recording.mp3 --output my_analysis.md
  
  # Quick summary, quiet mode
  python agent.py recording.mp3 --type quick --quiet

Environment Variables (loaded from .env):
  AWS_REGION                         AWS region for Bedrock and Transcribe
  CLAUDE_CODE_USE_BEDROCK           Set to 1 to use Bedrock
  MEETING_TRANSCRIBE_S3_BUCKET      S3 bucket for audio uploads
  CLEANUP_AUDIO_FROM_S3             Set to 'false' to keep audio files in S3
        """
    )
    
    parser.add_argument(
        'audio_file',
        help='Path to the meeting audio file (MP3, WAV, M4A, etc.)'
    )
    
    parser.add_argument(
        '-t', '--type',
        choices=['comprehensive', 'quick', 'manager_1on1'],
        default='comprehensive',
        help='Type of analysis to perform (default: comprehensive)'
    )
    
    parser.add_argument(
        '-r', '--role',
        choices=['participant', 'report', 'manager'],
        default='participant',
        help='Your role: participant (neutral), report (junior person), manager (senior person)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: <audio_name>_analysis.md)'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Reduce output verbosity'
    )
    
    args = parser.parse_args()
    
    # Run the agent
    asyncio.run(run_meeting_analysis(
        audio_path=args.audio_file,
        analysis_type=args.type,
        user_role=args.role,
        output_file=args.output,
        verbose=not args.quiet
    ))


if __name__ == "__main__":
    main()

