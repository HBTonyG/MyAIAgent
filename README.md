# Self-Improving AI Agent

A Python 3 application for a self-improving AI agent that automates interactions with the Grok (xAI) API, includes browser automation, comprehensive logging, and recursive self-modification capabilities.

## Features

- **YAML-based Prompt Sequences**: Define sequences of prompts with conditional logic
- **Grok (xAI) API Integration**: Automated API calls with rate limiting and exponential backoff
- **Browser Automation**: Selenium-based automation for Brave browser
- **SQLite Logging**: Comprehensive logging of all interactions
- **Self-Improvement**: Meta-prompting system that analyzes logs and suggests optimizations
- **CLI Interface**: Easy-to-use command-line interface
- **Lightweight**: Optimized for MacBook Air M1 (8GB RAM)

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Browser Setup** (optional, only needed for browser automation):
   - Install Brave browser if you want to use browser automation features
   - ChromeDriver is automatically managed by Selenium 4.6+ - no manual installation needed!

3. **Set your Grok (xAI) API key:**
   ```bash
   export GROK_API_KEY="your-api-key-here"
   ```
   Or use `XAI_API_KEY` environment variable, or add it to `config/agent_config.yaml`
   
   Get your API key from [console.x.ai](https://console.x.ai)

## Usage

### Start an agent session:
```bash
python main.py start [config_file]
```

Example:
```bash
python main.py start config/prompts.yaml
```

### View recent logs:
```bash
python main.py logs [--limit N]
```

### Review pending improvements:
```bash
python main.py improvements
```

### Approve an improvement:
```bash
python main.py approve [improvement_id]
```

### Reject an improvement:
```bash
python main.py reject [improvement_id]
```

### Pause current session:
```bash
python main.py pause
```

### Resume paused session:
```bash
python main.py resume
```

## Configuration

### Prompt Sequences (YAML)

Define your prompt sequences in YAML files. Example structure:

```yaml
prompts:
  - id: "step1"
    start: true
    prompt: "Your prompt text here"
    conditions:
      - if: "response contains 'success'"
        then: "step2"
      - if: "response contains 'error'"
        then: "step_error"
    browser_actions:
      - type: "navigate"
        params:
          url: "https://example.com"
```

### Supported Conditions

- `response contains 'text'` - Check if response contains text
- `response not contains 'text'` - Check if response doesn't contain text
- `response length > 100` - Compare response length
- `variable_name == 'value'` - Compare variable value

### Browser Actions

- `navigate` - Navigate to URL
- `click` - Click an element
- `type` - Type text into input
- `switch_tab` - Switch browser tab
- `wait` - Wait for specified time
- `screenshot` - Take screenshot

## Architecture

- `main.py` - CLI entry point
- `agent.py` - Main orchestration logic
- `config_parser.py` - YAML configuration handling
- `api_client.py` - OpenAI API wrapper
- `browser_automation.py` - Selenium wrapper
- `database.py` - SQLite logging
- `self_improvement.py` - Meta-prompting system

## Database Schema

The SQLite database (`agent.db`) stores:
- Sessions
- Prompts and responses
- Errors
- Browser actions
- Improvement suggestions

## Self-Improvement

After each session, the agent:
1. Analyzes logs using meta-prompting
2. Generates improvement suggestions
3. Stores suggestions for user review
4. Applies approved changes to YAML configs

**Note**: The agent can only modify YAML configuration files, not Python code.

## Error Handling

- Exponential backoff for rate limits
- Maximum 5 retry attempts
- Graceful degradation on failures
- Comprehensive error logging

## License

This project is provided as-is for educational and development purposes.

