# Professional Growth Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-package%20manager-orange.svg)](https://docs.astral.sh/uv/)
[![Claude Agent SDK](https://img.shields.io/badge/Claude-Agent%20SDK-blueviolet.svg)](https://docs.anthropic.com/en/agent-sdk)
[![AWS](https://img.shields.io/badge/AWS-Bedrock%20%26%20Transcribe-FF9900.svg)](https://aws.amazon.com/)

AI-powered professional development through intelligent feedback. Analyze meetings, interviews, and conversations to accelerate your career growth using Claude Agent SDK and AWS Transcribe.

## Quick Start

```bash
# Setup
uv sync
cp env.template .env
# Edit .env with your AWS credentials

# Create S3 bucket
aws s3 mb s3://professional-growth-transcriptions --region us-west-2

# Run (you as mentee seeking guidance)
uv run python agent.py your-meeting.mp3 --role mentee
```

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) - `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [Claude Code CLI](https://claude.ai/install.sh) - `curl -fsSL https://claude.ai/install.sh | bash`
- AWS account with Bedrock and Transcribe access

## Configuration

Edit `.env`:

```bash
AWS_REGION=us-west-2
CLAUDE_CODE_USE_BEDROCK=1
MEETING_TRANSCRIBE_S3_BUCKET=professional-growth-transcriptions
```

## Usage

### 1. Single Analysis (CLI)

```bash
# Meeting analysis (you as mentee seeking guidance)
uv run python agent.py meeting.mp3 --scenario meeting --role mentee

# Career coaching or mentorship conversation
uv run python agent.py coaching.m4a --role mentee

# Interview analysis (as candidate)
uv run python agent.py interview.mp3 --scenario interview --role candidate

# Interview analysis (as interviewer)
uv run python agent.py interview.mp3 --scenario interview --role interviewer

# Chinese meeting analyzed in English
uv run python agent.py chinese_meeting.m4a --analysis-language english

# Custom output file
uv run python agent.py meeting.mp3 --output analysis.md
```

### 2. Web UI with Multi-Turn Chat (Streamlit)

Visual interface with chat and session management:

```bash
uv run streamlit run streamlit_app.py

# Then open browser to http://localhost:8501
# - Choose scenario (meeting or interview)
# - Select your role
# - Upload audio file
# - Get analysis with download button
# - Ask follow-up questions in chat
# - Load previous sessions from sidebar
```

## What It Analyzes

Focus is on **helping YOU improve**:

- Your speaking patterns - Did you speak enough? Too much?
- Your communication quality - Question quality, active listening
- Your action items - Clarity on what you need to do
- Your effectiveness - Missed opportunities to improve
- Actionable feedback - Specific behaviors you can change

Output saved as markdown file (e.g., `meeting_analysis.md`).

## Multi-Language Support

**Supports multiple languages** with speaker identification (English, Chinese, Spanish, French, German, Japanese, Korean).

**How it works:**
- You specify the meeting language (or default to English)
- System transcribes with **speaker labels** (spk_0, spk_1) to identify who said what
- Analysis is provided in your chosen language

**Analysis Language Options**:
- **Same as audio** (default) - Analysis matches the recording language (Chinese → Chinese, English → English)
- **English** - Always analyze in English, regardless of recording language (useful for sharing or portfolio)

**Usage:**
```bash
# English meeting (default)
uv run python agent.py meeting.mp3 --role mentee

# Chinese meeting with speaker labels
uv run python agent.py chinese-meeting.m4a --role mentee
# In the conversation, say: "This is a Chinese meeting"
# Claude will use: --language zh-CN

# Or explicitly in prompt
uv run python agent.py "Transcribe this Spanish meeting" meeting.mp3
```

**Usage**:
```bash
# Chinese meeting, analysis in Chinese (default with auto-detection)
uv run python agent.py chinese_meeting.m4a

# Chinese meeting, analysis in English (for sharing/portfolio)
uv run python agent.py chinese_meeting.m4a --analysis-language english

# Explicitly use auto-detection (same as default)
uv run python agent.py chinese_meeting.m4a --analysis-language auto
```

## How It Works

1. **Agent Skill** (`.claude/skills/meeting-transcription/`) - Transcribes audio via AWS Transcribe
2. **Claude Analysis** - Analyzes transcript with focus on YOUR perspective
3. **Autonomous Output** - Agent writes analysis directly to markdown file

## Cost

Typical 30-minute meeting: ~$1.50
- Bedrock (Claude Sonnet): ~$0.50
- AWS Transcribe: ~$0.72 ($0.024/min)
- S3: Negligible (auto-deleted)

## Project Structure

```
.
├── .claude/skills/meeting-transcription/
│   ├── SKILL.md                     # Skill definition
│   └── transcribe_audio.py          # AWS Transcribe integration
├── agent.py                         # Single analysis (CLI)
├── streamlit_app.py                 # Web UI with multi-turn chat
├── prompts.py                       # Shared prompt configuration
├── pyproject.toml                   # Dependencies (uv)
├── env.template                     # Environment template
└── README.md
```

### Architecture

**Consistent Prompt Management:**
- `prompts.py` - Centralized configuration with custom system prompt
- Custom system prompt with Professional Growth Coach instructions
- Mode-specific additions for analysis/chat/stream
- All three interfaces use identical configuration

## IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
      "transcribe:StartTranscriptionJob",
      "transcribe:GetTranscriptionJob",
      "s3:PutObject",
      "s3:GetObject",
      "s3:DeleteObject"
    ],
    "Resource": "*"
  }]
}
```

## License

MIT
