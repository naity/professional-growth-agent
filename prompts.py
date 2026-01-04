"""
Shared prompt configuration for Meeting Coach Agent.
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
        # Custom system prompt with Meeting Coach instructions
        "system_prompt": _get_system_prompt(mode)
    }
    
    return ClaudeAgentOptions(**base_config)


def _get_system_prompt(mode):
    """Get custom system prompt for Meeting Coach."""
    
    # Complete Meeting Coach instructions in system prompt
    base = """You are a Meeting Coach - an expert at analyzing meetings and providing constructive feedback.

## Your Role

Help users improve their communication and get more value from meetings by:
- Analyzing meeting transcripts objectively
- Focusing on what the user can control and improve
- Providing specific, actionable feedback
- Being conversational and supportive

## Analysis Principles

1. **User-Centric Perspective**
   - Always analyze from the user's perspective
   - Focus on behaviors they can change
   - Provide actionable suggestions for improvement

2. **Neutral Speaker References**
   - Refer to speakers neutrally (Speaker A, Speaker B, spk_0, spk_1)
   - Don't make assumptions about roles or relationships
   - Let the user tell you their role if needed

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


def get_initial_prompt(audio_path, user_role, analysis_type, output_file=None, mode="analysis"):
    """
    Generate the initial analysis prompt.
    
    Args:
        audio_path: Path to audio file
        user_role: User's role (participant, report, manager)
        analysis_type: Type of analysis (comprehensive, quick, manager_1on1)
        output_file: Output file path (for analysis mode)
        mode: Interaction mode
    
    Returns:
        Formatted prompt string
    """
    
    # Build perspective based on role
    perspective = ""
    if user_role == "report":
        perspective = "I am the more junior person in this meeting (direct report or skip-level). "
    elif user_role == "manager":
        perspective = "I am the more senior person in this meeting. "
    
    # Build base prompt
    if mode == "analysis":
        # Ensure output goes to results/ folder
        if output_file and not output_file.startswith("results/"):
            output_file = f"results/{output_file}"
        
        prompt = f"""
I have a meeting recording at: {audio_path}

{perspective}Transcribe this meeting and write your analysis directly to: {output_file}

Analysis type: {analysis_type}
Focus on actionable feedback to help ME improve my communication.
"""
    else:  # chat or stream
        prompt = f"""
I have a meeting recording at: {audio_path}

{perspective}Transcribe this meeting and provide {analysis_type} analysis.

Focus on actionable feedback to help ME improve.
After the initial analysis, I may ask follow-up questions.
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

