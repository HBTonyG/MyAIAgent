# Self-Improving AI Agent

A Python 3 application for a self-improving AI agent that automates interactions with the Grok (xAI) API, includes browser automation, comprehensive logging, and recursive self-modification capabilities.

## Features

- **YAML-based Prompt Sequences**: Define sequences of prompts with conditional logic
- **Grok (xAI) API Integration**: Automated API calls with rate limiting and exponential backoff
- **Cursor IDE Integration**: Automatic file writing - generated code appears in Cursor automatically
- **Iterative Code Improvement**: Analyze existing projects and automatically improve them through multiple iterations
- **Project Analysis**: Scan and understand project structure, detect project types
- **Quality Scoring**: AI-powered quality assessment with customizable criteria
- **Browser Automation**: Selenium-based automation for Brave browser (with automatic driver management)
- **Website Testing**: Basic functionality testing for web projects
- **SQLite Logging**: Comprehensive logging of all interactions
- **Self-Improvement**: Meta-prompting system that analyzes logs and suggests optimizations
- **CLI Interface**: Easy-to-use command-line interface
- **Git Safety**: Optional git integration for backup and rollback
- **Lightweight**: Optimized for MacBook Air M1 (8GB RAM)

## Installation

### Package Installation (Recommended)

**Prerequisites:**
- Python 3.10 or higher (3.11+ recommended)
- Check your Python version: `python3 --version`

If you don't have Python 3.10+, install it:
- **macOS:** `brew install python` or download from [python.org](https://www.python.org/downloads/)
- **Linux:** Use your package manager or [python.org](https://www.python.org/downloads/)

1. **Clone or download this repository:**
   ```bash
   cd ~/Code/MyAIAgent
   ```

2. **Install the package in editable mode:**
   
   If you have multiple Python versions, use the specific version:
   ```bash
   python3.11 -m pip install -e .
   ```
   
   Or if `python3` points to 3.10+:
   ```bash
   python3 -m pip install -e .
   ```
   
   **Note:** If you get a "Python version" error, ensure you're using Python 3.10+ by specifying the version explicitly (e.g., `python3.11` or `python3.10`).
   
   This installs the `myaiagent` command globally, allowing you to run it from any directory.

3. **Browser Setup** (optional, only needed for browser automation):
   - Install Brave browser if you want to use browser automation features
   - ChromeDriver is automatically managed by Selenium 4.6+ - no manual installation needed!

4. **Set your Grok (xAI) API key:**
   ```bash
   export GROK_API_KEY="your-api-key-here"
   ```
   Or use `XAI_API_KEY` environment variable, or add it to `~/.zshrc` for persistence:
   ```bash
   echo 'export GROK_API_KEY="your-api-key-here"' >> ~/.zshrc
   source ~/.zshrc
   ```
   
   Get your API key from [console.x.ai](https://console.x.ai)

### Alternative: Direct Script Execution

If you prefer not to install as a package, you can run the script directly:

**Prerequisites:** Python 3.10 or higher (3.11+ recommended)

1. **Install Python dependencies:**
   ```bash
   cd ~/Code/MyAIAgent
   python3 -m pip install -r requirements.txt
   ```
   (Use `python3.11 -m pip` if you have multiple Python versions)

2. **Run from the MyAIAgent directory:**
   ```bash
   python3 main.py [command]
   ```

## Usage

After package installation, you can run `myaiagent` from any directory:

### Start an agent session:
```bash
myaiagent start [config_file]
```

Example:
```bash
myaiagent start config/prompts.yaml
```

### View recent logs:
```bash
myaiagent logs [--limit N]
```

### Review pending improvements:
```bash
myaiagent improvements
```

### Approve an improvement:
```bash
myaiagent approve [improvement_id]
```

### Reject an improvement:
```bash
myaiagent reject [improvement_id]
```

### Pause current session:
```bash
myaiagent pause
```

### Resume paused session:
```bash
myaiagent resume
```

### Improve a project iteratively:
```bash
myaiagent improve [config_file] [--project-path PATH]
```

Example (from your project directory):
```bash
cd ~/Code/MyProject
myaiagent improve
```

This will analyze your project, assess quality, and automatically improve it through iterative cycles until quality standards are met.

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

### File Operations (Cursor Integration)

Generate code and automatically write it to files that Cursor will detect:

```yaml
file_operations:
  - type: "write"
    target: "output/my_script.py"
    extract_code: true
    language: "python"
```

- `type: "write"` - Write code to a file
- `target` - File path (relative to project root)
- `extract_code` - Automatically extract code blocks from API response
- `language` - Programming language for code extraction (default: "python")

## Iterative Code Improvement

The agent can analyze and automatically improve existing projects in Cursor:

```bash
# From your project directory
myaiagent improve
```

### How It Works

1. **Analyzes** your project: Scans files, detects project type, builds context
2. **Assesses Quality**: Scores code across multiple criteria (accessibility, UX, performance, etc.)
3. **Researches Best Practices**: AI researches current standards for your project type
4. **Generates Improvements**: Creates specific, actionable improvement suggestions
5. **Applies Changes**: Updates files automatically in Cursor
6. **Iterates**: Repeats until quality threshold is met, max iterations reached, or token budget exceeded

### Improvement Configuration

Create `config/project_improvement.yaml`:

```yaml
project:
  path: "."  # Your project directory (defaults to current directory)
  file_patterns: ["*.html", "*.css", "*.js"]

quality:
  threshold: 85  # Target score
  criteria:
    - accessibility
    - user_experience
    - performance

iteration:
  max_iterations: 5
  auto_improve: true

safety:
  git_integration: true  # Auto-commit backups

token_budget:
  max_tokens_per_session: 100000  # Default: 100k tokens
  warning_threshold: 0.80  # Warn at 80% of budget
  hard_stop: true  # Stop execution when budget exceeded
```

### Token Budget

The agent includes configurable token budgeting to prevent API credit overruns:

- **Default Budget**: 100,000 tokens per session
- **Warning Threshold**: 80% (warns when 80,000 tokens used)
- **Hard Stop**: Enabled by default - stops execution when budget exceeded
- **Usage Tracking**: Token usage is tracked and displayed after each iteration

To adjust the budget, modify the `token_budget` section in your config file. Set `max_tokens_per_session` to `null` for unlimited usage (not recommended).

### Example Workflow

1. **Create your project in Cursor**: Build a basic website or application
2. **Add a PRD**: Document your requirements in Cursor
3. **Let Cursor generate initial code**: Use Cursor's AI to create the initial implementation
4. **Run the improvement agent**: 
   ```bash
   # Navigate to your project directory
   cd ~/Code/MyProject
   
   # Run the improvement agent (works from any directory after installation)
   myaiagent improve
   ```
5. **Agent analyzes and improves**: The agent reads Cursor-generated files and applies improvements
6. **Review in Cursor**: Files are automatically updated and visible in Cursor
7. **Agent stops when**: Quality threshold met, max iterations reached, or token budget exceeded

### Command Options

```bash
myaiagent improve [config_file] [--project-path PATH]
```

- `config_file` (optional): Path to improvement config file. If not specified, uses default `config/project_improvement.yaml` from package installation
- `--project-path PATH` (optional): Path to project directory. Defaults to current directory if not specified

**Example with options:**
```bash
myaiagent improve --project-path /path/to/my/project
```

## Architecture

- `main.py` - CLI entry point
- `agent.py` - Main orchestration logic
- `config_parser.py` - YAML configuration handling
- `api_client.py` - Grok (xAI) API wrapper
- `cursor_integration.py` - Cursor IDE file operations integration
- `project_analyzer.py` - Project scanning and structure analysis
- `quality_analyzer.py` - Code quality assessment and scoring
- `improvement_engine.py` - Iterative improvement loop controller
- `website_tester.py` - Browser-based website testing
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

