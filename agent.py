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
from claude_agent_sdk import query, AssistantMessage, TextBlock
from prompts import get_agent_options, get_initial_prompt

# Load environment variables from .env file
load_dotenv()


def build_analysis_prompt(
    audio_path: str, 
    analysis_type: str = "comprehensive",
    user_role: str = "participant",
    output_file: str = "analysis.md",
    scenario: str = "meeting"
) -> str:
    """Wrapper for shared prompt builder - kept for backward compatibility."""
    return get_initial_prompt(audio_path, user_role, analysis_type, output_file, mode="analysis", scenario=scenario)


async def run_meeting_analysis(
    audio_path: str,
    analysis_type: str = "manager_1on1",
    user_role: str = "report",
    output_file: str = None,
    scenario: str = "meeting",
    verbose: bool = True
):
    """
    Run the meeting/interview analysis agent.
    
    Args:
        audio_path: Path to the audio file
        analysis_type: Type of analysis to perform
        user_role: User's role in the conversation
        output_file: Path to save the analysis (default: auto-generated markdown file)
        scenario: Type of conversation (meeting or interview)
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
    
    # Get consistent agent configuration
    options = get_agent_options(mode="analysis")
    
    # Set working directory
    options.cwd = str(Path(__file__).parent.absolute())
    
    # Generate the analysis prompt
    prompt = build_analysis_prompt(audio_path, analysis_type, user_role, output_file, scenario)
    
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
        '-s', '--scenario',
        choices=['meeting', 'interview'],
        default='meeting',
        help='Type of conversation: meeting or interview'
    )
    
    parser.add_argument(
        '-r', '--role',
        default='report',
        help='Your role: meeting (participant/report/manager), interview (candidate/interviewer)'
    )
    
    parser.add_argument(
        '-t', '--type',
        choices=['comprehensive', 'quick', 'manager_1on1'],
        default='manager_1on1',
        help='Type of analysis to perform (default: manager_1on1 for meetings)'
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
        scenario=args.scenario,
        verbose=not args.quiet
    ))


if __name__ == "__main__":
    main()

