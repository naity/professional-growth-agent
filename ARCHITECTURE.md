# Architecture: Consistent Prompt Management

## Overview

Meeting Coach Agent uses a centralized prompt management approach inspired by Claude Agent SDK best practices for maintaining consistency across multiple interfaces.

## Design Pattern

### Three-Layer Approach

```
┌─────────────────────────────────────────────┐
│ prompts.py                                  │
│ - Custom system prompt with instructions    │
│ - get_agent_options(mode)                   │
│ - get_initial_prompt(...)                   │
└─────────────────────────────────────────────┘
                    ↓
┌────────────┬─────────────┬──────────────────┐
│ agent.py   │ chat_agent  │ streamlit_app.py │
│ (analysis) │ (chat)      │ (stream)         │
└────────────┴─────────────┴──────────────────┘
```

## Components

### 1. prompts.py (Centralized Configuration)

**Purpose**: Single source of truth for all Meeting Coach configuration

**Contains**:
- Custom system prompt with Meeting Coach instructions
- Mode-specific prompt additions
- Initial prompt builder

**Functions**:

```python
get_agent_options(mode="analysis"|"chat"|"stream")
# Returns ClaudeAgentOptions with:
# - Base config (tools, permissions, settings)
# - Minimal system prompt (tool descriptions)
# - Mode-specific instructions

get_initial_prompt(audio_path, user_role, analysis_type, output_file, mode)
# Returns formatted prompt with:
# - Role-based perspective
# - Analysis-type specific instructions
# - Mode-appropriate format
```

**System Prompt Strategy**:
- Uses **custom system prompt** (Method 4 from SDK docs)
- Complete Meeting Coach instructions in the prompt
- Mode-specific additions appended
- No CLAUDE.md or output styles needed

**Why this approach?**
- ✅ Simple and straightforward
- ✅ All configuration in one place (prompts.py)
- ✅ Easy to version control
- ✅ No filesystem dependencies

### 2. Interface Files

All three interfaces import and use the shared configuration:

```python
from prompts import get_agent_options, get_initial_prompt

options = get_agent_options(mode="chat")
prompt = get_initial_prompt(audio_path, user_role, analysis_type, ...)
```

## Benefits

| Benefit | Description |
|---------|-------------|
| **Consistency** | Same core behavior across CLI and web |
| **Maintainability** | Update prompts.py once, affects all modes |
| **Flexibility** | Mode-specific tweaks via `append` |
| **Best Practices** | Follows Claude SDK documentation patterns |
| **Version Control** | Instructions tracked in git |
| **Team Collaboration** | Shared understanding via CLAUDE.md |

## Extending the System

### Adding a New Interface

```python
# new_interface.py
from prompts import get_agent_options, get_initial_prompt

# Get configured options
options = get_agent_options(mode="my_mode")  # Add to prompts.py

# Get prompt
prompt = get_initial_prompt(..., mode="my_mode")

# Use with agent
async for message in query(prompt=prompt, options=options):
    ...
```

### Modifying Core Behavior

Edit `_get_system_prompt()` in `prompts.py` - changes apply to all interfaces.

### Adding Mode-Specific Behavior

Edit `_get_mode_specific_prompt()` in `prompts.py`.

## References

- [Claude SDK: Modifying System Prompts](claude_docs/Modifying%20system%20prompts.md)
- [Claude SDK: Session Management](claude_docs/Session%20Management.md)
- [Claude SDK: Streaming Input](claude_docs/Streaming%20Input.md)

