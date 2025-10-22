# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **AI Agent CLI** (ai-agent) - an intelligent terminal assistant that allows users to control the command line using natural language. It supports file operations, code execution, MCP (Model Context Protocol) integration, and intelligent file references via the `@` syntax.

Key features:
- Natural language command execution
- `@` file reference syntax for interactive file selection
- Conversation memory and context
- Dual LLM architecture (general model for dialogue, code model for command generation)
- MCP integration for filesystem and desktop control
- Git commit message generation
- Todo list management

## Development Commands

### Installation and Setup
```bash
# Install the CLI tool
./install.sh

# Uninstall
./uninstall.sh

# Install to custom directory
./install.sh /custom/path
```

### Running the Agent
```bash
# Interactive mode (default)
ai-agent

# Single command mode
ai-agent "list all Python files"

# With working directory
ai-agent -w /path/to/project "show git status"

# Quiet mode (no header)
ai-agent -q "pwd"
```

### Testing
```bash
# Run individual tests
python3 test/test_file_reference.py
python3 test/test_interactive_selector.py
python3 test/test_demo.py
python3 test/test_todo.py

# Test the workflow directly
python3 terminal_agent.py
```

### Python Environment
```bash
# Install dependencies
pip3 install -r requirements.txt

# Required packages
pip3 install langgraph langchain-core langchain-openai httpx requests python-dotenv
```

## Architecture

### Dual LLM System
The project uses two separate LLM configurations:

1. **LLM_CONFIG** (`agent_config.py`): General-purpose model for intent analysis, dialogue, and Q&A
2. **LLM_CONFIG2** (`agent_config.py`): Code-specialized model for command generation and code writing

Both are configured in `agent_config.py` with their own API keys, base URLs, and temperature settings.

### LangGraph Workflow
The core workflow is built with LangGraph (`agent_workflow.py`):

```
User Input → File Reference Processing → Intent Analysis → Route by Intent
                                                                ↓
            ┌───────────────┬──────────────┬──────────────────┼───────────────┐
            ↓               ↓              ↓                  ↓               ↓
    Terminal Command   Multi-Step    MCP Tool Call    Git Commit      Todo Manager
            ↓               ↓              ↓                  ↓               ↓
    Execute Command    Plan Steps    Execute Tool     Generate Msg    Process Todo
            ↓               ↓              ↓                  ↓               ↓
        Format ←────── Execute Multi ← Format ←───────── Direct End ←── Direct End
            ↓
         Result
```

Intent types (defined in `AgentState`):
- `terminal_command`: Single shell command
- `multi_step_command`: Multiple commands or file creation
- `mcp_tool_call`: Use MCP tools (file operations, desktop control)
- `git_commit`: Generate git commit messages
- `add_todo` / `query_todo`: Manage todo items
- `question`: Answer user questions

### Core Modules

**Entry Point:**
- `ai-agent`: Executable entry point with CLI argument parsing

**Configuration:**
- `agent_config.py`: LLM configs, working directory, state type definitions
- `mcp_config.json`: MCP server configurations

**Workflow & Nodes:**
- `agent_workflow.py`: LangGraph workflow definition with routing logic
- `agent_nodes.py`: Node implementations (intent analysis, command execution, etc.)

**LLM Layer:**
- `agent_llm.py`: LLM client instances (`llm` for general, `llm_code` for code)

**Memory & State:**
- `agent_memory.py`: Conversation history management
- Uses `MAX_CONVERSATION_HISTORY` and `MAX_COMMAND_HISTORY` from config

**File Reference System:**
- `file_reference_parser.py`: Parse `@` syntax, match files, read content
- `interactive_file_selector.py`: Interactive file picker UI

**MCP Integration:**
- `mcp_manager.py`: MCP server manager and tool registry
- `mcp_filesystem.py`: Built-in filesystem tools

**Special Features:**
- `git_tools.py`: Git commit message generation
- `todo_manager.py`: Todo list management (add/query/complete)

**UI & Utilities:**
- `agent_ui.py`: User interface, prompts, and special command handling
- `agent_utils.py`: Command execution, validation, safety checks

### State Management
The `AgentState` (TypedDict in `agent_config.py`) contains all workflow state:
- Input/output: `user_input`, `response`, `error`
- Intent & routing: `intent`, `command`, `commands`
- Execution: `command_output`, `command_outputs`
- File operations: `file_path`, `file_content`, `needs_file_creation`
- File references: `original_input`, `referenced_files`, `file_contents`
- MCP: `mcp_tool`, `mcp_params`, `mcp_result`
- Todo: `todo_action`, `todo_date`, `todo_time`, `todo_content`, `todo_result`
- Memory: `chat_history`

## Key Implementation Details

### @ File Reference Feature
Supports multiple syntax modes:
- `@` alone: Launch interactive file selector
- `@filename`: Quick search and select
- `@./path/file`: Relative path reference
- `@/abs/path`: Absolute path reference
- `@*.py`: Glob pattern matching
- `@folder/`: Directory reference

Processing flow:
1. `file_reference_processor` node parses `@` syntax from user input
2. Uses `parse_file_references()` to extract file references
3. Reads file content via MCP filesystem tools
4. Injects content into conversation context
5. Replaces `@path` with processed input for downstream nodes

### Adding New Nodes
To add a new workflow node:

1. Define node function in `agent_nodes.py`:
   ```python
   def my_new_node(state: AgentState) -> dict:
       """Node description"""
       # Process state
       return {"field_to_update": value}
   ```

2. Register in `agent_workflow.py`:
   ```python
   workflow.add_node("my_node", my_new_node)
   ```

3. Add routing logic if needed:
   ```python
   def route_by_intent(state: AgentState) -> str:
       if state["intent"] == "my_intent":
           return "my_node"
   ```

4. Connect edges:
   ```python
   workflow.add_edge("source_node", "my_node")
   workflow.add_edge("my_node", "target_node")
   ```

### Adding New MCP Tools
To integrate a new MCP server:

1. Add server config to `mcp_config.json`:
   ```json
   {
     "mcpServers": {
       "my-server": {
         "command": "npx",
         "args": ["-y", "@scope/mcp-server", "arg1"]
       }
     }
   }
   ```

2. MCP tools are auto-discovered by `mcp_manager.py`

3. Use in workflow via `mcp_tool_executor` node

### Safety Features
- Command validation checks dangerous commands (`DANGEROUS_COMMANDS` in config)
- Execution timeout: `COMMAND_TIMEOUT = 10` seconds
- Working directory constraints
- Input sanitization before execution

## Configuration Files

### Environment Variables
Set API keys and URLs in `agent_config.py`:
```python
LLM_CONFIG = {
    "model": "qwen-plus",
    "api_key": "your-api-key",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "temperature": 0.7,
}

LLM_CONFIG2 = {
    "model": "qwen-coder-plus",
    "api_key": "your-api-key",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "temperature": 0.1,
}
```

**IMPORTANT**: Never commit API keys. Consider using environment variables or `.env` files (already in `.gitignore`).

### Working Directory
Default working directory is set in `agent_config.py`:
```python
WORKING_DIRECTORY = "/Users/zhangyanhua/Desktop/AI/tushare/quantification/example"
```

This can be overridden with `-w` flag at runtime.

## File Organization

```
.
├── ai-agent                    # Executable entry point
├── agent_config.py             # Configuration and state types
├── agent_workflow.py           # LangGraph workflow
├── agent_nodes.py              # Workflow node implementations
├── agent_llm.py                # LLM client instances
├── agent_memory.py             # Conversation memory
├── agent_utils.py              # Utilities and command execution
├── agent_ui.py                 # UI and special commands
├── file_reference_parser.py    # @ syntax parser
├── interactive_file_selector.py # File picker UI
├── mcp_manager.py              # MCP integration
├── mcp_filesystem.py           # Built-in filesystem tools
├── mcp_config.json             # MCP server config
├── git_tools.py                # Git commit generation
├── todo_manager.py             # Todo list management
├── requirements.txt            # Python dependencies
├── install.sh                  # Installation script
├── uninstall.sh               # Uninstallation script
├── test/                       # Test files
│   ├── test_file_reference.py
│   ├── test_interactive_selector.py
│   ├── test_demo.py
│   └── test_todo.py
├── .cursor/rules/              # Cursor AI rules
│   ├── project-overview.mdc
│   ├── python-style.mdc
│   ├── workflow-development.mdc
│   ├── file-reference-feature.mdc
│   ├── mcp-integration.mdc
│   ├── testing.mdc
│   └── documentation.mdc
└── docs/                       # Documentation
```

## Code Style

### Python Standards
- Follow PEP 8
- Use type hints (TypedDict for state, function annotations)
- Use docstrings for all functions and classes
- Chinese comments for context, English for technical terms
- Keep functions focused and under 50 lines when possible
- Use descriptive variable names

### LangGraph Conventions
- Node functions take `AgentState` and return `dict` with partial state updates
- Never mutate state directly, return updates
- Use routing functions for conditional edges
- Keep node logic focused on single responsibility

### UI/UX
- Use emoji for visual feedback (✅ ❌ 🎯 📁 etc.)
- Provide clear error messages
- Show progress indicators for long operations
- Use colored/formatted output for better readability

## Cursor Rules Reference

The `.cursor/rules/` directory contains MDC files that automatically apply when editing:
- **project-overview.mdc**: Always applied, provides project context
- **python-style.mdc**: Auto-applied for `*.py` files
- **testing.mdc**: Auto-applied for `test_*.py` files
- **documentation.mdc**: Auto-applied for `*.md` files
- **workflow-development.mdc**: Query when developing LangGraph workflows
- **file-reference-feature.mdc**: Query when working on `@` file reference feature
- **mcp-integration.mdc**: Query when working on MCP integration

See `.cursor/rules/README.md` for details.

## Common Tasks

### Adding a New Intent Type
1. Add to `AgentState` literal type in `agent_config.py`
2. Create node function in `agent_nodes.py`
3. Update `route_by_intent()` in `agent_workflow.py`
4. Register node and edges in `build_agent()`

### Debugging Workflow
- Add print statements in node functions
- Check state transitions in `agent_workflow.py`
- Use `chat_history` in memory to trace conversation flow
- Test nodes individually before integrating

### Updating LLM Models
Edit `agent_config.py` to change models or providers. The dual LLM architecture allows using different models for different tasks (e.g., fast model for intent, powerful model for code).

## Important Notes

- The CLI is installed to `~/.local/bin/` by default
- All module files are copied to the same directory as `ai-agent` executable
- API keys are currently hardcoded in `agent_config.py` - should be externalized for production
- MCP config path is relative to the executable location
- Working directory can be changed via `-w` flag or by modifying `WORKING_DIRECTORY` constant
