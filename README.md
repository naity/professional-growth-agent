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

# Interview analysis (as candidate)
uv run python agent.py interview.mp3 --scenario interview --role candidate

# Non-English meeting (see Multi-Language Support section for all languages)
uv run python agent.py chinese_meeting.m4a --transcription-language zh-CN

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

**Supported languages** with speaker identification:
- English (en-US)
- Chinese Mandarin - Simplified (zh-CN)
- Chinese Traditional - Taiwan (zh-TW)
- Spanish (es-ES)
- French (fr-FR)
- German (de-DE)
- Japanese (ja-JP)
- Korean (ko-KR)

**How it works:**
- Specify transcription language with `--transcription-language` (defaults to en-US)
- Speaker labels are **always enabled** to identify who said what (spk_0, spk_1, etc.)
- Choose analysis language: same as audio (default) or English

**Analysis Language Options:**
- `--analysis-language auto` (default) - Analysis matches the recording language
- `--analysis-language english` - Always analyze in English (useful for sharing/portfolio)

**CLI Examples:**
```bash
# English meeting (default)
uv run python agent.py meeting.mp3

# Chinese meeting, analysis in Chinese
uv run python agent.py meeting.m4a --transcription-language zh-CN

# Chinese meeting, analysis in English
uv run python agent.py meeting.m4a --transcription-language zh-CN --analysis-language english

# Spanish meeting
uv run python agent.py meeting.mp3 --transcription-language es-ES

# French meeting
uv run python agent.py meeting.mp3 --transcription-language fr-FR
```

**Streamlit UI:**
- Use the "Transcription Language" dropdown to select the audio language
- Use the "Analysis Language" dropdown to choose output language
- Speaker labels are automatically enabled

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
