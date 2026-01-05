#!/usr/bin/env python3
"""
Streamlit Web UI for Professional Growth Agent
Upload meetings/interviews, get analysis, and ask follow-up questions.
"""

import streamlit as st
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from claude_agent_sdk import query, AssistantMessage, TextBlock, ResultMessage
from prompts import get_agent_options, get_initial_prompt
from session_manager import SessionManager
import tempfile

# Load environment variables
load_dotenv()

# Initialize session manager
session_manager = SessionManager()

# Page config
st.set_page_config(
    page_title="Professional Growth Coach",
    page_icon="🚀",
    layout="wide"
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'audio_path' not in st.session_state:
    st.session_state.audio_path = None
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'current_audio_filename' not in st.session_state:
    st.session_state.current_audio_filename = None
if 'output_file' not in st.session_state:
    st.session_state.output_file = None


async def analyze_meeting(audio_path: str, user_role: str, analysis_type: str, original_filename: str, scenario: str = "meeting", analysis_language: str = "auto", transcription_language: str = "en-US"):
    """Analyze meeting/interview and capture session ID for follow-up questions."""
    
    # Validate audio file exists
    if not Path(audio_path).exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    # Get consistent agent configuration
    options = get_agent_options(mode="analysis")
    options.cwd = str(Path(__file__).parent.absolute())
    
    # Build initial prompt using shared configuration
    # Use original filename, not temp path
    # Note: prompts.py automatically adds "results/" prefix
    output_file = f"analysis_{Path(original_filename).stem}.md"
    prompt = get_initial_prompt(audio_path, user_role, analysis_type, output_file, mode="analysis", scenario=scenario, analysis_language=analysis_language, transcription_language=transcription_language)
    
    # Run query and capture session ID
    session_id = None
    all_messages = []
    error_occurred = False
    
    try:
        async for message in query(prompt=prompt, options=options):
            # Capture session ID from init message
            if hasattr(message, 'subtype') and message.subtype == 'init':
                session_id = message.data.get('session_id')
            
            # Check for errors
            if hasattr(message, 'subtype') and message.subtype == 'error':
                error_occurred = True
                error_msg = message.data.get('message', 'Unknown error occurred')
                all_messages.append(f"❌ Error: {error_msg}")
            
            # Collect all assistant text messages
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        text = block.text.strip()
                        if text:  # Only add non-empty messages
                            all_messages.append(text)
    except Exception as e:
        error_occurred = True
        all_messages.append(f"❌ Exception during analysis: {str(e)}")
    
    # Return the LAST message (should be Claude's final summary)
    # Skip short narration messages and get the last substantial one
    result_text = ""
    for msg in reversed(all_messages):
        if len(msg) > 50:  # Substantial message
            result_text = msg
            break
    
    # Fallback: use last message or default
    if not result_text:
        result_text = all_messages[-1] if all_messages else "Analysis completed and saved to file."
    
    # Verify output file was created and has content
    output_path = Path(options.cwd) / "results" / output_file
    if output_path.exists():
        file_size = output_path.stat().st_size
        if file_size == 0:
            result_text += "\n\n⚠️ Warning: Output file was created but is empty. The analysis may have failed."
        else:
            result_text += f"\n\n✅ Analysis saved to {output_file}"
    else:
        result_text += f"\n\n⚠️ Warning: Expected output file not found: {output_file}"
    
    return session_id, result_text


async def ask_followup(session_id: str, question: str):
    """Ask a follow-up question using session resumption."""
    try:
        # Get agent options for chat mode
        options = get_agent_options(mode="chat")
        options.cwd = str(Path(__file__).parent.absolute())
        options.resume = session_id  # Resume the session
        
        # For chat mode, we want the conversational AssistantMessage responses
        response_text = []
        async for message in query(prompt=question, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_text.append(block.text)
        
        result = "\n".join(response_text)
        if not result:
            return "I apologize, but I didn't generate a response. Could you rephrase your question?"
        return result
    except Exception as e:
        return f"Error processing your question: {str(e)}"


# UI Layout
st.title("🚀 Professional Growth Coach")
st.markdown("AI-powered meeting and interview analysis with Claude Agent SDK")

# Sidebar for configuration and previous sessions
with st.sidebar:
    st.header("Settings")
    
    scenario = st.selectbox(
        "Scenario",
        ["meeting", "interview"],
        help="Type of conversation to analyze"
    )
    
    # Role options change based on scenario
    if scenario == "meeting":
        role_options = ["mentee", "peer", "mentor"]  # mentee first as default
        role_help = "Your role in the meeting"
        default_role_idx = 0  # mentee
    else:  # interview
        role_options = ["candidate", "interviewer"]
        role_help = "Your role in the interview"
        default_role_idx = 0  # candidate
    
    user_role = st.selectbox(
        "Your Role",
        role_options,
        index=default_role_idx,
        help=role_help
    )
    
    # Analysis types
    if scenario == "meeting":
        analysis_options = ["comprehensive", "manager_1on1", "quick"]  # comprehensive first as default
        default_analysis_idx = 0  # comprehensive
    else:  # interview
        analysis_options = ["comprehensive", "quick"]
        default_analysis_idx = 0  # comprehensive
    
    analysis_type = st.selectbox(
        "Analysis Type",
        analysis_options,
        index=default_analysis_idx,
        help="Depth and focus of analysis"
    )
    
    # Transcription language selection
    transcription_language_options = {
        "English (US)": "en-US",
        "Chinese (Mandarin - Simplified)": "zh-CN",
        "Chinese (Traditional - Taiwan)": "zh-TW",
        "Spanish": "es-ES",
        "French": "fr-FR",
        "German": "de-DE",
        "Japanese": "ja-JP",
        "Korean": "ko-KR"
    }
    
    transcription_language_display = st.selectbox(
        "Transcription Language",
        list(transcription_language_options.keys()),
        index=0,
        help="Language of the audio recording (speaker labels will be enabled)"
    )
    transcription_language = transcription_language_options[transcription_language_display]
    
    analysis_language = st.selectbox(
        "Analysis Language",
        ["Same as audio", "English"],
        index=0,
        help="Choose analysis language: 'Same as audio' = Chinese for Chinese meetings, English for English meetings. 'English' = Always English."
    )
    
    st.markdown("---")
    st.header("📜 Previous Sessions")
    
    # Get all previous sessions
    previous_sessions = session_manager.get_all_sessions()
    
    if previous_sessions:
        session_options = ["-- Select a session --"] + [
            session_manager.format_session_display(s) for s in previous_sessions
        ]
        
        selected_idx = st.selectbox(
            "Load Previous Analysis",
            range(len(session_options)),
            format_func=lambda i: session_options[i],
            help="Resume a previous meeting analysis"
        )
        
        if selected_idx > 0:  # Not the default option
            selected_session = previous_sessions[selected_idx - 1]
            
            if st.button("📂 Load This Session", type="primary"):
                # Load the session
                st.session_state.session_id = selected_session['session_id']
                st.session_state.current_audio_filename = selected_session['audio_filename']
                st.session_state.output_file = selected_session['output_file']
                st.session_state.analysis_complete = True
                
                # Load the analysis from file
                output_path = Path(selected_session['output_file'])
                if output_path.exists():
                    with open(output_path, 'r') as f:
                        analysis = f.read()
                    
                    st.session_state.messages = [{
                        "role": "assistant",
                        "content": analysis
                    }]
                    
                    session_manager.update_last_accessed(selected_session['session_id'])
                    st.success(f"✅ Loaded: {selected_session['audio_filename']}")
                    st.rerun()
                else:
                    st.error("Analysis file not found")
    else:
        st.info("No previous sessions yet")
    
    st.markdown("---")
    st.markdown("### About")
    if scenario == "meeting":
        st.markdown("""
        Upload your meeting recording to get:
        - Actionable feedback
        - Communication insights
        - Areas for improvement
        
        Then ask follow-up questions!
        """)
    else:
        st.markdown("""
        Upload your interview recording to get:
        - Performance feedback
        - Answer quality analysis
        - Interview technique insights
        
        Then ask follow-up questions!
        """)

# Main content area
tab1, tab2 = st.tabs(["📁 Upload & Analyze", "💬 Chat"])

with tab1:
    recording_label = "Interview" if scenario == "interview" else "Meeting"
    st.header(f"Upload {recording_label} Recording")
    
    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=['mp3', 'wav', 'm4a', 'mp4', 'flac', 'ogg'],
        help="Upload your meeting recording (MP3, WAV, M4A, etc.)"
    )
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
            st.session_state.audio_path = tmp_path
        
        st.success(f"✅ Uploaded: {uploaded_file.name}")
        
        if st.button("🚀 Analyze Meeting", type="primary"):
            with st.spinner("🤖 Analyzing meeting... This may take a few minutes."):
                try:
                    # Get list of files before analysis
                    results_dir = Path("results")
                    results_dir.mkdir(exist_ok=True)
                    existing_files = set(results_dir.glob("*.md"))
                    
                    # Convert UI language selection to parameter
                    analysis_lang_param = "auto" if analysis_language == "Same as audio" else "english"
                    
                    # Run analysis with original filename
                    session_id, analysis = asyncio.run(
                        analyze_meeting(tmp_path, user_role, analysis_type, uploaded_file.name, scenario, analysis_lang_param, transcription_language)
                    )
                    
                    # Find the newly created file
                    new_files = set(results_dir.glob("*.md")) - existing_files
                    
                    if new_files:
                        actual_output_file = str(list(new_files)[0])
                    else:
                        # Expected filename
                        expected_file = f"results/analysis_{Path(uploaded_file.name).stem}.md"
                        actual_output_file = expected_file
                    
                    # Store session ID and metadata
                    st.session_state.session_id = session_id
                    st.session_state.current_audio_filename = uploaded_file.name
                    st.session_state.output_file = actual_output_file
                    st.session_state.analysis_complete = True
                    
                    # Store the latest analysis in messages
                    st.session_state.messages = [{
                        "role": "assistant",
                        "content": analysis
                    }]
                    
                    # Save session metadata with actual file path
                    session_manager.save_session(
                        session_id=session_id,
                        audio_filename=uploaded_file.name,
                        user_role=user_role,
                        analysis_type=analysis_type,
                        output_file=actual_output_file
                    )
                    
                    st.success("✅ Analysis complete! Switch to the Chat tab to ask follow-up questions.")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error during analysis: {str(e)}")
    
    # Show analysis and download button if analysis exists (outside button block)
    if st.session_state.analysis_complete and st.session_state.output_file:
        # Show analysis
        if st.session_state.messages:
            latest_analysis = st.session_state.messages[0]["content"]
            with st.expander("📊 View Analysis", expanded=True):
                st.markdown(latest_analysis)
        
        # Show download button
        output_path = Path(st.session_state.output_file)
        if output_path.exists():
            with open(output_path, "r") as f:
                md_content = f.read()
            
            st.download_button(
                label="📥 Download Analysis (Markdown)",
                data=md_content,
                file_name=output_path.name,
                mime="text/markdown",
                use_container_width=True,
                key="download_analysis_tab1"
            )

with tab2:
    st.header("Ask Follow-Up Questions")
    
    # Show current session info
    if st.session_state.analysis_complete and st.session_state.current_audio_filename:
        st.caption(f"💬 Chatting about: **{st.session_state.current_audio_filename}**")
    
    if not st.session_state.analysis_complete:
        st.info("👈 Upload and analyze a meeting first, or load a previous session to start chatting!")
    else:
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask a follow-up question..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get agent response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = asyncio.run(
                            ask_followup(st.session_state.session_id, prompt)
                        )
                        st.markdown(response)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response
                        })
                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })

# Footer
st.markdown("---")
st.markdown("Built with [Claude Agent SDK](https://docs.anthropic.com/en/agent-sdk) and [Streamlit](https://streamlit.io)")

