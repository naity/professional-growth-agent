"""
Shared prompt configuration for Professional Growth Agent.
Ensures consistency across CLI and Streamlit interfaces.
"""

from claude_agent_sdk import ClaudeAgentOptions


def get_agent_options(mode="analysis"):
    """
    Get consistent agent options for all interfaces.
    
    Args:
        mode: "analysis" (write to file), "chat" (interactive), or "stream" (streaming UI)
    
    Returns:
        ClaudeAgentOptions configured consistently
    """
    
    # Base configuration - shared across all modes
    base_config = {
        "allowed_tools": ["Skill", "Read", "Write", "Bash"],
        "permission_mode": "acceptEdits",
        "setting_sources": ["project"],  # Load skills from .claude/skills/
        # Custom system prompt with Professional Growth Coach instructions
        "system_prompt": _get_system_prompt(mode)
    }
    
    return ClaudeAgentOptions(**base_config)


def _get_system_prompt(mode):
    """Get custom system prompt for Professional Growth Coach."""
    
    # Complete Professional Growth Coach instructions in system prompt
    base = """You are a Professional Growth Coach - an expert at analyzing professional conversations (meetings, interviews) and providing constructive feedback to help people advance their careers.

## Your Role

Help users improve their communication and get more value from conversations (meetings, interviews) by:
- Analyzing conversation transcripts objectively
- Focusing on what the user can control and improve
- Providing specific, actionable feedback
- Being conversational and supportive
- Adapting feedback to the context (meetings, interviews, etc.)

## Transcription Guidelines

IMPORTANT: Always specify the language when transcribing to enable speaker labels:
- English meetings: `--language en-US` (default if not specified)
- Chinese meetings: `--language zh-CN`
- Spanish meetings: `--language es-ES`
- Other languages: `--language <code>` (fr-FR, de-DE, ja-JP, ko-KR, zh-TW)

Speaker labels (spk_0, spk_1, spk_2) are ALWAYS enabled to identify different speakers.

## Analysis Principles

1. **User-Centric Perspective**
   - Always analyze from the user's perspective
   - Focus on behaviors they can change
   - Provide actionable suggestions for improvement

2. **Neutral Speaker References**
   - Refer to speakers neutrally (Speaker A, Speaker B, spk_0, spk_1, or Interviewer/Candidate if context is clear)
   - Don't make assumptions about roles or relationships unless specified
   - Adapt feedback based on the conversation type (meeting vs interview)

3. **Specificity**
   - Use concrete examples from the transcript
   - Quote specific phrases when illustrating points
   - Provide measurable observations (e.g., "spoke 30% of the time")

4. **Constructive Tone**
   - Balance criticism with acknowledgment of strengths
   - Frame feedback as opportunities, not failures
   - Be encouraging and supportive

5. **Conciseness with Depth**
   - Be comprehensive but tight - every sentence should add value
   - Use 1-2 strong examples instead of many weak ones
   - Get to insights quickly, avoid repetition
   - Eliminate redundancy while maintaining substance"""
    
    # Add mode-specific behavior
    mode_addition = _get_mode_specific_prompt(mode)
    
    if mode_addition:
        return f"{base}\n\n{mode_addition}"
    return base


def _get_mode_specific_prompt(mode):
    """Get mode-specific prompt additions."""
    
    if mode == "analysis":
        # One-shot analysis mode - writes to file
        return """
After completing your analysis, write it directly to the specified markdown file.
"""
    
    elif mode == "chat":
        # Interactive CLI mode - conversational
        return """
You are in an interactive session. After the initial analysis:
- Answer follow-up questions naturally
- Provide specific, actionable advice
- Offer scripts and examples when helpful
- Be concise but thorough
"""
    
    elif mode == "stream":
        # Streamlit UI mode - web interface
        return """
You are in a web chat interface. Be:
- Conversational and friendly
- Concise (users can ask for more detail)
- Visual (use markdown formatting effectively)
- Responsive to follow-up questions
"""
    
    return ""  # Default: no additional prompt


def get_initial_prompt(audio_path, user_role, analysis_type, output_file=None, mode="analysis", scenario="meeting", analysis_language="auto", transcription_language="en-US"):
    """
    Generate the initial analysis prompt.
    
    Args:
        audio_path: Path to audio file
        user_role: User's role (mentee/peer/mentor for meetings, candidate/interviewer for interviews)
        analysis_type: Type of analysis (comprehensive, quick, manager_1on1)
        output_file: Output file path (for analysis mode)
        mode: Interaction mode
        scenario: Context type (meeting or interview)
        analysis_language: Language for analysis output ("auto" = same as audio, "english" = force English)
    
    Returns:
        Formatted prompt string
    """
    
    # Build perspective based on scenario and role
    perspective = ""
    if scenario == "meeting":
        if user_role == "mentee":
            perspective = "I am seeking guidance in this conversation (mentee, report, or junior person). "
        elif user_role == "mentor":
            perspective = "I am providing guidance in this conversation (mentor, manager, or senior person). "
    elif scenario == "interview":
        if user_role == "candidate":
            perspective = "I am the candidate being interviewed. "
        elif user_role == "interviewer":
            perspective = "I am the interviewer conducting the interview. "
    
    # Build base prompt
    conversation_type = "interview" if scenario == "interview" else "meeting"
    
    # Add transcription language instruction
    transcription_instruction = f"\n\nIMPORTANT: Use --language {transcription_language} when transcribing to enable speaker labels."
    
    # Add analysis language instruction based on preference
    analysis_instruction = ""
    if analysis_language == "english":
        analysis_instruction = "\n\nIMPORTANT: Write the analysis AND all your conversational responses in English, even if the conversation is in another language."
    elif analysis_language == "auto":
        analysis_instruction = "\n\nIMPORTANT: Write the analysis AND all your conversational responses in the SAME LANGUAGE as the conversation. If the transcript is in Chinese, write everything in Chinese. If it's in English, write everything in English."
    
    if mode == "analysis":
        # Ensure output goes to results/ folder with absolute path
        # This prevents issues when cwd changes (e.g., during Skill tool execution)
        from pathlib import Path
        import os
        if output_file:
            if not output_file.startswith("results/"):
                output_file = f"results/{output_file}"
            # Convert to absolute path to ensure it's written to project root
            if not Path(output_file).is_absolute():
                # Use the project cwd that was set in options
                output_file = str(Path(os.getcwd()) / output_file)
        
        prompt = f"""
I have a {conversation_type} recording at: {audio_path}

{perspective}Transcribe this {conversation_type} and write your analysis directly to: {output_file}{transcription_instruction}

Analysis type: {analysis_type}
Focus on actionable feedback to help ME improve my {"interview performance" if scenario == "interview" else "communication"}.{analysis_instruction}
"""
    else:  # chat or stream
        prompt = f"""
I have a {conversation_type} recording at: {audio_path}

{perspective}Transcribe this {conversation_type} and provide {analysis_type} analysis.{transcription_instruction}

Focus on actionable feedback to help ME improve.
After the initial analysis, I may ask follow-up questions.{analysis_instruction}
"""
    
    # Add analysis-type specific instructions
    if analysis_type == "manager_1on1":
        prompt += """

Focus on:
- My communication effectiveness (did I speak enough/too much?)
- Quality of my questions (strategic vs tactical)
- My active listening behaviors
- Career development discussion
- Clarity of my action items
- What I can do better next time

Keep the analysis comprehensive but tight - aim for depth without redundancy.
"""
    elif scenario == "interview":
        # Interview-specific guidance
        if user_role == "candidate":
            prompt += """

Focus on candidate performance:
- Answer structure and clarity (STAR method if relevant)
- Technical depth and accuracy (for technical questions)
- Communication skills and articulation
- Questions I asked about the role/company
- Confidence and engagement level
- Areas where I struggled or could improve
- Specific suggestions for better answers

Keep the analysis comprehensive but tight - aim for depth without redundancy.
"""
        elif user_role == "interviewer":
            prompt += """

Focus on interviewer effectiveness:
- Question quality and relevance
- Follow-up and probing techniques
- Candidate engagement and rapport building
- Potential bias indicators in questions or tone
- Time management and coverage
- Clear communication of role/expectations
- Areas for improvement in interview technique

Keep the analysis comprehensive but tight - aim for depth without redundancy.
"""
    elif analysis_type == "quick":
        prompt += """

Provide:
- 3 key takeaways
- Main action items for me
- One specific suggestion for improvement
"""
    elif analysis_type == "comprehensive":
        prompt += """

Provide comprehensive analysis covering:
1. Meeting summary
2. My speaking patterns
3. My communication quality
4. My action items
5. Constructive feedback for me
6. Specific suggestions for next meeting

Keep it comprehensive but concise - quality over quantity.
"""
    
    return prompt

