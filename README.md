# Meeting Coach Agent

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

```bash
# Basic - analyzes from your perspective
uv run python agent.py meeting.mp3

# Specify your role
uv run python agent.py meeting.mp3 --role report        # You're junior person
uv run python agent.py meeting.mp3 --role manager       # You're senior person

# Analysis types
uv run python agent.py meeting.mp3 --type comprehensive # Full analysis (default)
uv run python agent.py meeting.mp3 --type manager_1on1  # 1:1 focused
uv run python agent.py meeting.mp3 --type quick         # Quick summary

# Custom output
uv run python agent.py meeting.mp3 --output analysis.md
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
├── agent.py                         # Main agent
├── pyproject.toml                   # Dependencies (uv)
├── env.template                     # Environment template
└── README.md
```

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
