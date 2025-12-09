# Agent Training Guide: Building Your Self-Improving AI Assistant

**Purpose:** This guide explains how to train and evolve your custom AI agent. Training involves iterative use, feedback, and self-improvement loops to turn a basic automation tool into a powerful personal assistant. No advanced coding skills required—start simple and progress gradually.

## Table of Contents

1. Introduction
2. Prerequisites
3. Initial Setup
4. Training Basics: How Self-Improvement Works
5. Progression Ideas: From Simple to Complex
6. Best Practices and Troubleshooting
7. Advanced Tips

---

## 1. Introduction

Your AI agent is a Python-based tool that automates interactions with the Grok (xAI) API. It sequences prompts, handles browser tasks via Selenium, logs everything to SQLite, and improves itself by analyzing past runs and suggesting YAML configuration tweaks.

"Training" means running sessions, reviewing outputs, and approving improvements—like teaching an apprentice. Start with basic tasks to build confidence, then scale to complex workflows.

The agent evolves recursively: It uses the AI to analyze its own performance and suggest optimizations to its YAML prompt sequences, reducing manual effort over time.

**Goal:** Achieve efficient, hands-off automation for coding, research, or creative workflows.

---

## 2. Prerequisites

- **Hardware:** MacBook Air M1 (or better) with at least 8GB RAM and macOS Ventura or later
- **Software:**
  - Python 3.10+ (install via Homebrew: `brew install python`)
  - Dependencies: Run `pip install -r requirements.txt` (installs `openai`, `selenium`, `pyyaml`, `requests`)
  - ChromeDriver: Required for Selenium with Brave browser
    ```bash
    brew install chromedriver
    ```
  - Browser: Brave browser installed (auto-detected on macOS)
- **API Key:** 
  - Sign up for Grok API at [console.x.ai](https://console.x.ai)
  - Set it as an environment variable: `export GROK_API_KEY='your-key'`
  - Or use `XAI_API_KEY` environment variable
- **Skills:** Basic terminal use (e.g., running `python main.py start`). No coding needed for training, but editing YAML files helps.

---

## 3. Initial Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your Grok API key:**
   ```bash
   export GROK_API_KEY="your-api-key-here"
   ```
   Or add it to `~/.zshrc` for persistence:
   ```bash
   echo 'export GROK_API_KEY="your-api-key-here"' >> ~/.zshrc
   source ~/.zshrc
   ```

3. **Create your first YAML config file** (e.g., `config/my_first_task.yaml`):
   ```yaml
   prompts:
     - id: "step1"
       start: true
       prompt: "Write a simple Python script that prints 'Hello, World!'"
       conditions:
         - if: "response contains 'error'"
           then: "step_error"
         - if: "response contains 'print'"
           then: "step2"
       next: "step2"
     
     - id: "step2"
       prompt: "Improve the previous script to accept user input and greet them by name"
       conditions:
         - if: "response contains 'input'"
           then: "step_complete"
     
     - id: "step_error"
       prompt: "An error occurred. Please analyze and provide a corrected version"
     
     - id: "step_complete"
       prompt: "Provide a summary of what was built"
   ```

4. **Run the agent:**
   ```bash
   python main.py start config/my_first_task.yaml
   ```

5. **Monitor progress:** The CLI shows progress, logs, and prompts for approvals on improvements.

---

## 4. Training Basics: How Self-Improvement Works

The agent's core loop:

1. **Run a Session:** Execute your prompt sequence. The agent sends prompts to the Grok API, processes responses, and automates browser tasks (if configured).

2. **Log Everything:** All interactions are stored in a local SQLite database (`agent.db`). View logs with:
   ```bash
   python main.py logs --limit 20
   ```

3. **Self-Review:** After the session completes, the agent automatically meta-prompts the Grok API: "Analyze this log—suggest optimizations like better sequencing, clearer prompts, or improved conditional logic."

4. **Review Improvements:** The agent proposes updates to your YAML configuration. View pending improvements:
   ```bash
   python main.py improvements
   ```

5. **Approve Changes:** Review each suggestion and approve if it looks good:
   ```bash
   python main.py approve [improvement_id]
   ```
   Or reject:
   ```bash
   python main.py reject [improvement_id]
   ```

6. **Iterate:** Rerun with the updated config. Each cycle makes the agent smarter—aim for 3-5 iterations per training session.

**Important Notes:**
- The agent can only modify YAML configuration files, not Python code. This keeps your core system stable.
- After approving an improvement, the agent automatically updates your YAML file.
- Rate your sessions mentally (e.g., "Score this run 7/10—too slow"). The agent's analysis considers patterns across sessions.
- Train 1-2 hours per day initially to monitor API costs (check usage at console.x.ai).

---

## 5. Progression Ideas: From Simple to Complex

Start small to test basics, then build complexity. Each stage adds layers like conditionals, browser automation, or recursive patterns. Use the agent's self-improvement to guide evolution—after a few runs, it might suggest the next steps itself!

### Stage 1: Basic App Creation (1-2 Sessions, Beginner Level)

- **Goal:** Get comfortable with automation.

- **Example YAML Sequence:**
   ```yaml
   prompts:
     - id: "step1"
       start: true
       prompt: "Create a simple Python script that prints 'Hello, World!'"
       next: "step2"
     
     - id: "step2"
       prompt: "Test and debug the app. If there are any errors, fix them"
       conditions:
         - if: "response contains 'error'"
           then: "step2"  # Loop back to fix errors
         - if: "response contains 'working'"
           then: "step_complete"
     
     - id: "step_complete"
       prompt: "Provide a summary of the completed app"
   ```

- **Browser Actions:** None at first.

- **Training Focus:** Run, log, and approve one improvement (e.g., add error checking conditions).

- **Expected Outcome:** Agent handles a full app build cycle without manual input.

- **Why Start Here:** Low risk; builds trust in the system.

### Stage 2: Adding Interactivity and Conditionals (2-3 Sessions)

- **Goal:** Introduce logic and conditional branching.

- **Example YAML Sequence:**
   ```yaml
   prompts:
     - id: "step1"
       start: true
       prompt: "Build a basic calculator app in Python that can add, subtract, multiply, and divide"
       conditions:
         - if: "response contains 'def '"
           then: "step2"
         - if: "response contains 'error'"
           then: "step_error"
       next: "step2"
     
     - id: "step2"
       prompt: |
         If the calculator works, enhance it by adding a GUI using Tkinter.
         Provide the complete code with a simple window and buttons.
       conditions:
         - if: "response contains 'Tkinter'"
           then: "step_complete"
         - if: "response contains 'error'"
           then: "step_error"
       browser_actions:
         - type: "navigate"
           params:
             url: "https://docs.python.org/3/library/tkinter.html"
         - type: "wait"
           params:
             time: 2
     
     - id: "step_error"
       prompt: "An error occurred. Analyze the issue and provide a corrected version"
       conditions:
         - if: "response contains 'def '"
           then: "step2"
     
     - id: "step_complete"
       prompt: "Provide a summary of the completed calculator with GUI"
   ```

- **Training Focus:** Teach handling failures—intentionally use a prompt that might fail, then let self-improvement fix it.

- **Expected Outcome:** Agent adapts to errors, evolving sequences dynamically based on response patterns.

### Stage 3: Web-Related Tasks (3-4 Sessions)

- **Goal:** Automate real-world web interactions.

- **Example YAML Sequence:**
   ```yaml
   prompts:
     - id: "step1"
       start: true
       prompt: "Write a Python script to scrape headlines from https://example.com/news using requests and BeautifulSoup"
       next: "step2"
     
     - id: "step2"
       prompt: |
         Optimize the scraper for speed and add data saving to CSV.
         Include error handling for network requests.
       conditions:
         - if: "response contains 'csv'"
           then: "step3"
       next: "step3"
     
     - id: "step3"
       prompt: |
         Enhance the scraper to use Selenium for JavaScript-heavy pages.
         Navigate to the news site, wait for content to load, then extract headlines.
       browser_actions:
         - type: "navigate"
           params:
             url: "https://example.com/news"
         - type: "wait"
           params:
             time: 3
         - type: "screenshot"
           params:
             filepath: "news_page.png"
       conditions:
         - if: "response contains 'selenium'"
           then: "step_complete"
     
     - id: "step_complete"
       prompt: "Provide a summary of the web scraping solution"
   ```

- **Training Focus:** Review logs for efficiency; approve recursive tweaks (e.g., agent prompts itself to refine scraping rules).

- **Expected Outcome:** A mini web agent that self-optimizes for accuracy and speed.

### Stage 4: Recursive Self-Building (4+ Sessions, Advanced)

- **Goal:** Achieve "personal AGI" feel with complex task orchestration.

- **Example YAML Sequence:**
   ```yaml
   prompts:
     - id: "step1"
       start: true
       prompt: |
         Design a YAML prompt sequence for a specialized agent that:
         1. Takes a research topic as input
         2. Searches the web for relevant information
         3. Summarizes findings
         4. Generates a report
       
         Provide the complete YAML configuration.
       next: "step2"
     
     - id: "step2"
       prompt: |
         Now use this new agent configuration to improve the main agent's 
         prompt sequence. Suggest optimizations based on what you've learned.
       browser_actions:
         - type: "navigate"
           params:
             url: "https://example.com"
         - type: "wait"
           params:
             time: 2
       conditions:
         - if: "response contains 'prompts:'"
           then: "step_complete"
     
     - id: "step_complete"
       prompt: "Provide a summary of the recursive improvement process"
   ```

- **Training Focus:** Let it run semi-autonomously; intervene only for approvals. Experiment with meta-tasks like "Evolve to handle multi-step research workflows."

- **Expected Outcome:** Agent builds and trains sub-agents, handling complex projects like full apps or data pipelines.

**Progress at your pace**—spend 1-2 days per stage. If the agent plateaus, manually add challenges (e.g., create a prompt sequence that tests error handling).

---

## 6. Best Practices and Troubleshooting

### Best Practices

- **Version Your YAML Files:** Keep versions (e.g., `my_task_v1.yaml`, `my_task_v2.yaml`) so you can roll back if needed.
- **Monitor API Costs:** Start with free/low-cost tiers. Check usage at console.x.ai regularly.
- **Backup Logs Weekly:** The SQLite database (`agent.db`) contains valuable training data. Back it up.
- **Ethical Use:** Avoid automating sensitive tasks (e.g., no scraping without permission, no automating social media spam).
- **Review Improvements Carefully:** Don't approve every suggestion—some might not align with your goals.
- **Use Descriptive Prompt IDs:** Name your prompt IDs clearly (e.g., `fetch_data`, `process_results`) for easier debugging.

### Troubleshooting

- **API Errors:**
  - Check your API key: `echo $GROK_API_KEY`
  - Verify internet connection
  - Check rate limits at console.x.ai
  - The agent has built-in exponential backoff for rate limits

- **Selenium/Browser Failures:**
  - Update ChromeDriver: `brew upgrade chromedriver`
  - Ensure Brave browser is installed
  - Check browser path in `config/agent_config.yaml` if auto-detection fails
  - Try running browser in headless mode: set `headless: true` in config

- **Slow Runs:**
  - Reduce sequence length initially
  - Approve optimizations that suggest simplifying prompts
  - Check logs for bottlenecks: `python main.py logs --limit 50`

- **Agent Stuck in Loop:**
  - Review your conditional logic—ensure there's always an exit condition
  - Check logs to see which prompt is repeating
  - Manually edit YAML to break the loop

- **No Improvements Generated:**
  - Ensure the session completed successfully (check logs)
  - Run a few sessions to build up training data
  - The agent needs sufficient log data to generate meaningful suggestions

- **YAML Syntax Errors:**
  - Validate your YAML with an online validator
  - Check indentation (YAML is sensitive to spacing)
  - Review the example in `config/prompts.yaml`

---

## 7. Advanced Tips

- **Custom Variables:** Use variable substitution in prompts:
   ```yaml
   prompts:
     - id: "step1"
       prompt: "Create a script for {{task_type}}"
   ```
   (Note: Variable functionality may require custom implementation)

- **Chain Multiple Config Files:** Run different sequences in sequence:
   ```bash
   python main.py start config/research.yaml
   python main.py start config/analysis.yaml
   ```

- **Export Logs for Analysis:** Query the SQLite database directly:
   ```bash
   sqlite3 agent.db "SELECT * FROM prompts WHERE session_id = 'your-session-id'"
   ```

- **Scale Beyond Coding:** Once trained, use for non-coding tasks:
   - Research sequences: "Summarize topic X, then critique the findings"
   - Content generation workflows
   - Data analysis pipelines
   - Documentation generation

- **Session Management:** Use pause/resume for long-running tasks:
   ```bash
   python main.py pause   # In another terminal
   python main.py resume  # When ready to continue
   ```

- **Experiment with Models:** Try different Grok models by setting:
   ```bash
   export GROK_MODEL="grok-beta"  # or other available models
   ```

---

## Getting Help

- Review the main README.md for technical details
- Check `config/prompts.yaml` for YAML structure examples
- Examine logs to understand agent behavior: `python main.py logs`
- The agent's self-improvement suggestions often contain hints about best practices

**Happy Training!** 🚀

