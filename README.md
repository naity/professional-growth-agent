# Meeting Coach Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-package%20manager-orange.svg)](https://docs.astral.sh/uv/)
[![Claude Agent SDK](https://img.shields.io/badge/Claude-Agent%20SDK-blueviolet.svg)](https://docs.anthropic.com/en/agent-sdk)
[![AWS](https://img.shields.io/badge/AWS-Bedrock%20%26%20Transcribe-FF9900.svg)](https://aws.amazon.com/)

AI-powered meeting analysis using Claude Agent SDK and AWS Transcribe. Get actionable feedback on your 1:1s and team meetings.

## Quick Start

```bash
# Setup
uv sync
cp env.template .env
# Edit .env with your AWS credentials

# Create S3 bucket
aws s3 mb s3://meeting-coach-transcriptions --region us-west-2

# Run
uv run python agent.py your-meeting.mp3 --role report
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
MEETING_TRANSCRIBE_S3_BUCKET=meeting-coach-transcriptions
```

## Usage

### 1. Single Analysis (CLI)

```bash
# Meeting analysis
uv run python agent.py meeting.mp3 --scenario meeting --role report

# Interview analysis (as candidate)
uv run python agent.py interview.mp3 --scenario interview --role candidate

# Interview analysis (as interviewer)
uv run python agent.py interview.mp3 --scenario interview --role interviewer

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
- Custom system prompt with Meeting Coach instructions
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
