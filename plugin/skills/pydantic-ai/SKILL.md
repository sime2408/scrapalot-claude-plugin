---
name: pydantic-ai
description: Pydantic AI agent reference for the Scrapalot Python AI backend — creating, wiring and testing agents in the RAG pipeline, backed by a scraped copy of the current docs. Use when adding or changing a deep-research or RAG agent in scrapalot-chat.
---

# Pydantic AI Agent Developer Skill

**Type**: Project skill for Scrapalot-Chat
**Pydantic AI Version**: 2.9.0

## Purpose

Use this skill when working with Pydantic AI agents in the Scrapalot-Chat RAG application. This skill provides expertise in creating, managing, and integrating Pydantic AI agents to enhance RAG techniques with agentic workflows.

## When to Use This Skill

Invoke this skill when you need to:
- Create new Pydantic AI agents for RAG workflows
- Add tools to existing agents
- Implement multi-agent patterns for complex RAG orchestration
- Stream agent responses with real-time updates
- Integrate agents with existing RAG strategies
- Debug or optimize agent behavior
- Implement dependency injection patterns for agents
- Create agent-enhanced retrieval strategies
- Use Capabilities or Toolsets for composable agent behavior
- Define agents via YAML/JSON with AgentSpec

## Core Concepts

### Pydantic AI Agents

Agents are the primary interface for interacting with LLMs in Pydantic AI. They provide:
- Type-safe dependency injection via `deps_type`
- Structured output validation via `output_type`
- Function tools for LLM-callable capabilities
- Streaming support for real-time responses
- Retry mechanisms for self-correction
- Composable Capabilities (tools + hooks + instructions packaged as reusable units)
- Toolsets for grouping and managing tools
- Built-in tools (web search, code interpreter, file search, image generation)
- Lifecycle hooks for intercepting agent behavior
- Concurrency limiting for rate control
- Agent description for observability

### Agent Components

1. **Instructions/System Prompts**: Define agent behavior and capabilities
2. **Tools**: Functions the LLM can call to gather information or perform actions
3. **Toolsets**: Groups of tools managed as units (`FunctionToolset`, `DynamicToolset`, `ToggleableToolset`)
4. **Capabilities**: Composable behavior units (tools + hooks + instructions + model settings)
5. **Dependencies**: Runtime context (database sessions, user info, configuration)
6. **Output Types**: Pydantic models for structured, validated responses (`NativeOutput`, `PromptedOutput`, `ToolOutput`)
7. **Model Settings**: Temperature, max tokens, timeout configuration
8. **Hooks**: Lifecycle interceptors (`@agent.on_model_request`, `@agent.on_tool_call`, etc.)
9. **History Processor**: Custom message history manipulation

### Integration with Scrapalot RAG

Pydantic AI agents enhance RAG strategies by:
- **Query Analysis**: Agents analyze queries to select optimal RAG strategies
- **Multi-Step Retrieval**: Agents orchestrate complex retrieval workflows
- **Document Filtering**: Agents intelligently filter and rerank documents
- **Answer Synthesis**: Agents combine multiple sources with citations
- **Adaptive Routing**: Agents route queries to specialized sub-agents

## File Structure

```
src/main/service/agents/
├── __init__.py                    # Package initialization
├── agent_factory.py               # Agent instance management and caching
├── base_agent.py                  # Base agent wrapper for Scrapalot integration
├── tools/                         # Agent tools directory
│   ├── __init__.py
│   ├── retrieval_tools.py         # Tools for document retrieval
│   ├── analysis_tools.py          # Tools for query analysis
│   ├── citation_tools.py          # Tools for citation generation
│   └── hierarchy_tools.py         # Tools for knowledge graph hierarchy
├── rag_agents/                    # RAG-specific agents (16 agents)
│   ├── __init__.py
│   ├── query_analyzer_agent.py    # Query analysis and classification
│   ├── strategy_router.py         # Strategy routing agent
│   ├── context_navigator.py       # Context expansion decisions
│   ├── collection_selector.py     # Collection selection
│   ├── section_navigation_agent.py # Section-level navigation
│   ├── tool_based_rag_agent.py    # Tool-based RAG with FunctionToolset
│   └── ...                        # 10 more specialized agents
└── examples/
    └── basic_rag_agent.py         # Simple RAG agent example
```

## Key Patterns

### 1. Agent Creation with Dependencies

```python
from pydantic_ai import Agent, RunContext
from sqlalchemy.orm import Session
from typing import Optional

# Define dependencies type
class RAGDependencies:
    db: Session
    user_id: str
    collection_ids: Optional[List[UUID]]

# Create agent with typed dependencies
agent = Agent(
    'openai:gpt-4o',
    deps_type=RAGDependencies,
    output_type=str,  # or Pydantic model for structured output
    system_prompt="You are a helpful RAG assistant...",
    description="RAG retrieval agent",  # NEW in 1.69.0 - for observability
)
```

### 2. Adding Tools to Agents

```python
@agent.tool
async def retrieve_documents(
    ctx: RunContext[RAGDependencies],
    query: str,
    top_k: int = 10
) -> str:
    """Retrieve relevant documents from the vector store.

    Args:
        query: The search query
        top_k: Number of documents to retrieve

    Returns:
        Formatted document context
    """
    # Access dependencies via ctx.deps
    collection_ids = ctx.deps.collection_ids

    from src.main.service.retriever.retriever_manager import RetrieverManager
    retriever = await RetrieverManager.get_retriever(
        db=ctx.deps.db,
        user_id=ctx.deps.user_id,
        retriever_type="pgvector"
    )

    documents = await retriever.process(
        prompt=query,
        collection_ids=collection_ids,
        top_k=top_k
    )

    return format_documents_for_context(documents)
```

### 3. Toolsets (NEW in 1.4.4+)

Group and manage tools as composable units:

```python
from pydantic_ai.toolsets import FunctionToolset, ToggleableToolset

# Create a toolset with multiple tools
retrieval_toolset = FunctionToolset()

@retrieval_toolset.tool
async def search_documents(ctx: RunContext[RAGDependencies], query: str) -> str:
    """Search for documents matching the query."""
    ...

@retrieval_toolset.tool
async def get_document_metadata(ctx: RunContext[RAGDependencies], doc_id: str) -> str:
    """Get metadata for a specific document."""
    ...

# Make tools toggleable (enable/disable at runtime)
toggleable = ToggleableToolset(retrieval_toolset, enabled=True)

# Use toolset with agent
agent = Agent('openai:gpt-4o', toolsets=[retrieval_toolset])
```

### 4. Built-in Tools (NEW in 1.6.2+)

```python
from pydantic_ai import Agent

# Agent with built-in web search
agent = Agent(
    'openai:gpt-4o',
    builtin_tools=['web_search', 'code_interpreter'],
)
```

### 5. Running Agents with Streaming

```python
# Stream agent responses
async with agent.run_stream(
    "What are the key findings about climate change?",
    deps=RAGDependencies(
        db=db,
        user_id=user_id,
        collection_ids=[collection_id]
    )
) as result:
    async for text in result.stream_text():
        yield json.dumps({"type": "bot_answer", "content": text}) + "\n"
```

### 6. Multi-Agent Pattern

```python
# Routing agent selects strategy
router_agent = Agent('openai:gpt-4o-mini', output_type=StrategySelection)

# Specialized agents for different tasks
retrieval_agent = Agent('openai:gpt-4o', deps_type=RAGDependencies)
synthesis_agent = Agent('anthropic:claude-sonnet-4', deps_type=RAGDependencies)

# Router decides which agent to use
strategy = await router_agent.run(query)

if strategy.output.requires_complex_retrieval:
    result = await retrieval_agent.run(query, deps=deps)
else:
    result = await synthesis_agent.run(query, deps=deps)
```

### 7. Lifecycle Hooks (NEW in 1.71.0+)

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4o', system_prompt="...")

@agent.on_model_request
async def log_request(ctx, request):
    """Log every model request for debugging."""
    logger.info("Model request: %s tools", len(request.tools or []))

@agent.on_tool_call
async def validate_tool(ctx, tool_call):
    """Validate tool calls before execution."""
    logger.info("Tool called: %s", tool_call.tool_name)
```

### 8. Output Type Modes (NEW in 1.3.3+)

Control how structured output is extracted:

```python
from pydantic_ai.output import NativeOutput, PromptedOutput, ToolOutput

# NativeOutput: Uses provider's native structured output (OpenAI JSON mode)
agent = Agent('openai:gpt-4o', output_type=NativeOutput(MyModel))

# PromptedOutput: Adds instructions to prompt for structure
agent = Agent('openai:gpt-4o', output_type=PromptedOutput(MyModel))

# ToolOutput: Uses tool calls to extract structured data (default)
agent = Agent('openai:gpt-4o', output_type=ToolOutput(MyModel))
```

### 9. Tool Timeout and Validation (NEW in 1.32.0+)

```python
@agent.tool(timeout=30)  # 30 second timeout for this tool
async def slow_retrieval(ctx: RunContext[RAGDependencies], query: str) -> str:
    """Retrieve documents with timeout protection."""
    ...

# args_validator for pre-execution validation (NEW in 1.63.0)
@agent.tool(args_validator=lambda args: args.get('top_k', 10) <= 100)
async def validated_search(ctx: RunContext[RAGDependencies], query: str, top_k: int = 10) -> str:
    ...
```

### 10. History Processor (NEW in 1.7.0)

```python
from pydantic_ai import Agent

def truncate_history(messages, max_messages=20):
    """Keep only last N messages to save tokens."""
    if len(messages) > max_messages:
        return messages[-max_messages:]
    return messages

agent = Agent(
    'openai:gpt-4o',
    history_processor=truncate_history,
)
```

## Best Practices

### 1. Type Safety

Always use type hints for dependencies and outputs:
```python
from pydantic import BaseModel

class QueryAnalysis(BaseModel):
    intent: str
    complexity: int
    suggested_strategy: str

agent = Agent('openai:gpt-4o', output_type=QueryAnalysis)
```

### 2. Error Handling

Use `ModelRetry` for agent self-correction:
```python
from pydantic_ai import ModelRetry

@agent.tool
async def validate_citation(ctx: RunContext, citation_id: str) -> bool:
    if not is_valid_citation(citation_id):
        raise ModelRetry("Invalid citation format. Use [1], [2], etc.")
    return True
```

### 3. Caching

Cache agent instances using composite keys:
```python
from src.main.service.agents.agent_factory import AgentFactory

agent = await AgentFactory.get_agent(
    agent_type="query_analyzer",
    model_name="gpt-4o",
    user_id=user_id
)
```

### 4. Logging

Use structured logging for agent operations:
```python
from src.main.utils.logger import get_logger

logger = get_logger(__name__)

logger.info("Agent run started: user_id=%s, query=%s", user_id, query[:50])
```

### 5. Streaming Format

Always use Scrapalot's PacketEmitter:
```python
from src.main.service.streaming.packet_emitter import PacketEmitter
emitter = PacketEmitter()

# Use PacketEmitter for streaming
yield emitter.emit_message_delta(token)
yield emitter.emit_status("analyzing_query", stage="rag")
```

### 6. Concurrency Limiting (NEW in 1.54.0)

```python
# Limit concurrent agent runs to prevent overloading LLM providers
agent = Agent('openai:gpt-4o', max_concurrent=5)
```

## Configuration

Add agent settings to `configs/config.yaml`:

```yaml
agents:
  enabled: true
  default_model: "openai:gpt-4o"
  timeout: 60  # seconds
  max_retries: 3
  cache_agents: true

  model_settings:
    temperature: 0.7
    max_tokens: 2000
    top_p: 0.9

  query_analyzer:
    model: "openai:gpt-4o-mini"
    temperature: 0.3

  retrieval_orchestrator:
    model: "openai:gpt-4o"
    temperature: 0.5

  synthesis:
    model: "anthropic:claude-sonnet-4"
    temperature: 0.7
```

## Installation

Pydantic AI is installed via requirements.txt:

```txt
# Pydantic AI - Agentic AI framework (v2). Use pydantic-ai-slim with explicit extras.
pydantic-ai-slim[openai,anthropic,google,mcp]==2.9.0

# Required companion libraries (v2 minimums):
pydantic[email]==2.12.5        # >=2.12 required by pydantic-ai 2.x
openai>=2.45.0,<3.0.0          # >=2.45.0 required by pydantic-ai-slim[openai] 2.9.0
google-genai>=1.70.0,<2.0.0    # >=1.70.0 required by pydantic-ai-slim[google] 2.9.0
fastmcp==3.4.4                 # /mcp server; shares fastmcp-slim 3.x with the mcp extra (needs starlette>=1.0 -> fastapi>=0.133)
```

## API Reference (v2.9.0)

### Agent Constructor

```python
Agent(
    model='openai-chat:gpt-4o',   # provider:model string or Model object. v2: bare 'openai:' -> Responses API; use 'openai-chat:' for Chat Completions. Prefix is REQUIRED (bare 'gpt-4o' raises UserError).
    output_type=MyModel,           # Pydantic model or output mode (NativeOutput, PromptedOutput, ToolOutput)
    deps_type=MyDeps,              # Type hint for dependencies
    system_prompt="...",           # Static system prompt
    toolsets=[my_toolset],         # Toolset instances (FunctionToolset, MCPToolset, ...)
    end_strategy='graceful',       # v2 default (was 'early'): fn tools requested alongside a successful output tool still run
    capabilities=[...],            # v2: instrumentation, native tools, prepare-tools, history processors live here now
)
# v2 moves: builtin_tools= -> capabilities=[NativeTool(...)] (pydantic_ai.native_tools);
#           history_processors= -> capabilities=[ProcessHistory(...)]; instrument= -> capabilities=[Instrumentation(...)].
```

### Result Access

```python
result = await agent.run("query", deps=deps)

result.output          # The structured output (property; never .data)
result.usage           # RunUsage — v2: a PROPERTY, not result.usage()
result.all_messages()  # Full message history
```

### Streaming

```python
async with agent.run_stream("query", deps=deps) as stream:
    async for text in stream.stream_text(delta=True):
        ...
    # After the stream is consumed:
    final = await stream.get_output()   # awaitable accessor for the validated output
    stream.usage                        # RunUsage (property)

# Event stream (voice / tool phases): v2 makes run_stream_events an async CONTEXT MANAGER:
async with agent.run_stream_events("query", deps=deps) as events:
    async for ev in events:
        ...  # FunctionToolCallEvent, PartStartEvent, PartDeltaEvent, ...
```

### REMOVED / CHANGED in v2.0

| Old (v1) | New (v2) |
|----------|----------|
| `result.usage()` (method) | `result.usage` (property) — same for `StreamedRunResult` |
| bare `openai:` = Chat Completions | bare `openai:` = **Responses API**; `openai-chat:` = Chat Completions |
| prefix-less model name (`'gpt-4o'`) | must carry a provider prefix or `Agent()` raises `UserError` |
| `MCPServerSSE` / `MCPServerStreamableHTTP` | `MCPToolset(SSETransport/StreamableHttpTransport(url, headers=...), read_timeout=...).prefixed(name)` |
| `Agent(mcp_servers=[...])` | `Agent(toolsets=[...])` (also `run_stream(..., toolsets=...)`) |
| `builtin_tools=` / `pydantic_ai.builtin_tools` | `capabilities=[NativeTool(...)]` / `pydantic_ai.native_tools` |
| `agent.tool` on a context-free fn | `agent.tool_plain` (`.tool` now requires `RunContext` first param) |
| `FunctionToolset.tools` (list) | dict `{name: Tool}` (iterate `.tools.values()`, each has `.function`/`.takes_ctx`) |
| `request_tokens` / `response_tokens` | `input_tokens` / `output_tokens` |
| `Usage` | `RunUsage` |
| direct `async for ev in agent.run_stream_events(...)` | `async with agent.run_stream_events(...) as events:` |
| `end_strategy='early'` (default) | `end_strategy='graceful'` (default) |
| `OpenAIModel` | `OpenAIChatModel` (or `OpenAIResponsesModel`) |

### DEPRECATED (removed earlier, in the 1.x line)

| Old (removed) | New (use instead) |
|---------------|-------------------|
| `result_type=` | `output_type=` |
| `result_validator` | `output_validator` |
| `result.data` | `result.output` |
| `stream.get_data()` | `stream.output` |
| `GeminiModel` | `GoogleModel` |
| `google-generativeai` SDK | `google-genai` SDK |

## Testing

```python
import pytest
from pydantic_ai.models.test import TestModel

@pytest.mark.asyncio
async def test_query_analyzer():
    test_model = TestModel()
    agent = create_query_analyzer(model=test_model)

    result = await agent.run("What is climate change?")
    assert result.output.intent == "factual_question"
```

## References

- **Official Docs**: https://ai.pydantic.dev/
- **Agents Guide**: https://ai.pydantic.dev/agents/
- **Tools Guide**: https://ai.pydantic.dev/tools/
- **Toolsets Guide**: https://ai.pydantic.dev/toolsets/
- **Capabilities**: https://ai.pydantic.dev/capabilities/
- **Multi-Agent Patterns**: https://ai.pydantic.dev/multi-agent-patterns/
- **Changelog**: https://ai.pydantic.dev/changelog/

## Common Issues

### 1. Dependency Injection

**Problem**: Dependencies not accessible in tools
**Solution**: Ensure `deps_type` is set and dependencies passed to `run()`

### 2. Streaming Format

**Problem**: Frontend doesn't render agent output
**Solution**: Wrap all output via `PacketEmitter` (never raw JSON)

### 3. Tool Execution Errors

**Problem**: Tools fail with unclear errors
**Solution**: Add proper error handling and use `ModelRetry` for retries

### 4. Model Compatibility

**Problem**: Model doesn't support required features
**Solution**: Check model capabilities in Pydantic AI docs; use `builtin_tools` for provider-native features

### 5. Google Model Migration

**Problem**: `google-generativeai` import errors after upgrade
**Solution**: Replace `google-generativeai` with `google-genai` in requirements.txt. Use `GoogleModel` (not `GeminiModel`)

## Skills Checklist

When working with Pydantic AI agents, ensure you:

- [ ] Define clear agent responsibilities (single purpose)
- [ ] Use type-safe dependencies (`deps_type`)
- [ ] Implement tools with proper docstrings
- [ ] Use structured outputs (`output_type`) when appropriate
- [ ] Handle streaming with Scrapalot's `PacketEmitter`
- [ ] Cache agents using `AgentFactory`
- [ ] Add comprehensive logging
- [ ] Write tests with `TestModel`
- [ ] Consider Toolsets for grouping related tools
- [ ] Use `description` parameter for observability
- [ ] Set `max_concurrent` for rate-limited providers
- [ ] Access results via `.output` (never `.data`)
