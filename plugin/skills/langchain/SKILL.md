---
name: langchain
description: LangChain v1.x reference for the Scrapalot Python AI backend — APIs, migration guides and RAG/agentic patterns, backed by a scraped copy of the current docs. Use when writing or changing LangChain code in scrapalot-chat.
---

# LangChain Documentation Expert Skill

**Type**: Project skill for Scrapalot-Chat
**Version**: LangChain v1.x (January 2026)

## Purpose

Use this skill when you need up-to-date information about LangChain v1.x features, APIs, migration guides, and best practices. This skill provides expertise in LangChain's latest documentation to help with RAG implementation, LLM integrations, and agentic workflows in Scrapalot-Chat.

## When to Use This Skill

Invoke this skill when you need to:
- Understand LangChain v1.x API changes and new features
- Migrate from LangChain 0.3.x to 1.x
- Implement LangChain RAG strategies with latest patterns
- Integrate LangChain with OpenAI, Anthropic, Google, Ollama providers
- Use LangGraph for multi-agent orchestration
- Implement streaming with the new v1.x streaming API
- Debug LangChain compatibility issues
- Find code examples for specific LangChain components
- Understand breaking changes between versions

## What This Skill Provides

### LangChain v1.x Coverage

1. **Core Components** (langchain-core 1.2.6):
   - Runnables and LCEL (LangChain Expression Language)
   - Prompts and Chat Templates
   - Output Parsers and Structured Output
   - Message Types and Chat History
   - Callbacks and Tracing

2. **LLM Integrations** (latest versions):
   - OpenAI (langchain-openai 1.1.6)
   - Anthropic (langchain-anthropic 1.3.0)
   - Google Gemini (langchain-google-genai 4.1.2)
   - Ollama (langchain-ollama 1.0.1)
   - Hugging Face (langchain-huggingface 1.2.0)

3. **RAG Components**:
   - Document Loaders and Text Splitters (v1.1.0)
   - Vector Stores and Retrievers
   - Embeddings and Reranking
   - Question Answering Chains

4. **Agents & Tools**:
   - LangGraph (v1.0.5) - Graph-based agent orchestration
   - Agent Executors and Tool Calling
   - Multi-agent Patterns
   - State Management with langgraph-checkpoint

5. **Database Integrations**:
   - PostgreSQL (langchain-postgres 0.0.16)
   - Vector Search with pgvector
   - Chat History Persistence

## Scrapalot-Chat Context

### Current LangChain Usage

Scrapalot-Chat uses LangChain for:
- **18 RAG Strategies**: Similarity, HyDE, Fusion, Parent Document, Step-Back, Decomposition, Graph Search, etc.
- **11 RAG Orchestrators**: Adaptive, Precision, Balanced, Low Latency, Knowledge-Intensive, TriModalFusion, etc.
- **16+ Chunking Strategies**: Contextual Retrieval, Late Chunking, Agentic, Hierarchical, Semantic, etc.
- **Multi-provider LLM Support**: OpenAI, Anthropic, Google, Ollama, local models
- **Vector Search**: PostgreSQL + pgvector integration
- **Streaming**: Real-time response streaming with PacketEmitter

### Key Files Using LangChain

```
scrapalot-chat/src/main/service/
├── rag/
│   ├── rag_*.py                      # 18 individual RAG strategies
│   ├── orchestrators/*.py            # 11 RAG orchestrators
│   └── chunking/chunking_*.py        # 16 chunking strategies
├── llm/
│   └── llm_manager.py                # LLM instance management
├── deep_research/
│   └── agents/*_agent.py             # Research agents using LangChain
└── agents/
    ├── rag_agents/*.py               # RAG agents (Pydantic AI + LangChain hybrid)
    └── tools/*.py                    # Agent tools using LangChain retrievers
```

## How to Use This Skill

### Basic Usage

When you need LangChain documentation, use WebSearch or WebFetch to query official docs:

```
WebSearch: "LangChain v1.x [specific topic] 2026"
WebFetch: https://python.langchain.com/docs/[topic]
```

### Documentation Sources

**Primary Sources**:
- Official Docs: https://python.langchain.com/docs/
- API Reference: https://python.langchain.com/api_reference/
- Migration Guide: https://python.langchain.com/docs/versions/migrating_chains/
- LangGraph Docs: https://langchain-ai.github.io/langgraph/

**GitHub Repositories**:
- LangChain Core: https://github.com/langchain-ai/langchain
- LangGraph: https://github.com/langchain-ai/langgraph
- Integration Templates: https://github.com/langchain-ai/langchain/tree/master/templates

### Reference Documentation

The `.claude/skills/lanchain/references/` directory contains:
- `output-lanchain_docs.md` - Comprehensive LangChain documentation snapshot

## Migration Guide: 0.3.x → 1.x

### Breaking Changes to Watch

1. **Chain Construction**:
   ```python
   # Old (0.3.x)
   from langchain.chains import LLMChain
   chain = LLMChain(llm=llm, prompt=prompt)

   # New (1.x) - Use LCEL
   from langchain_core.runnables import RunnablePassthrough
   chain = prompt | llm
   ```

2. **Streaming API**:
   ```python
   # Old (0.3.x)
   for chunk in chain.stream(input):
       print(chunk)

   # New (1.x) - Enhanced streaming
   async for event in chain.astream_events(input, version="v2"):
       if event["event"] == "on_chat_model_stream":
           print(event["data"]["chunk"])
   ```

3. **Output Parsing**:
   ```python
   # Old (0.3.x)
   from langchain.output_parsers import PydanticOutputParser

   # New (1.x) - Use structured output
   from langchain_core.output_parsers import PydanticOutputParser
   # Or use .with_structured_output() method
   chain = llm.with_structured_output(OutputModel)
   ```

4. **Retriever Chains**:
   ```python
   # Old (0.3.x)
   from langchain.chains import RetrievalQA

   # New (1.x) - Use create_retrieval_chain
   from langchain.chains import create_retrieval_chain
   from langchain.chains.combine_documents import create_stuff_documents_chain
   ```

### Deprecated Patterns

**Avoid these in v1.x**:
- ❌ `langchain.chains.LLMChain` - Use LCEL instead
- ❌ `langchain.agents.initialize_agent` - Use LangGraph or create_react_agent
- ❌ `langchain.memory.ConversationBufferMemory` - Use RunnableWithMessageHistory
- ❌ Direct imports from `langchain.*` - Use specific packages (langchain-openai, etc.)

**Use these instead**:
- LCEL chains: `prompt | llm | parser`
- LangGraph for complex agents
- `RunnableWithMessageHistory` for chat memory
- Specific integration packages

## Common Queries

### RAG Implementation

**Query**: "How to implement RAG with LangChain v1.x?"
**Answer Pattern**:
```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Setup
llm = ChatOpenAI(model="gpt-4o")
embeddings = OpenAIEmbeddings()
vectorstore = PGVector(
    connection_string="postgresql://...",
    embeddings=embeddings
)

# Create retrieval chain
retriever = vectorstore.as_retriever()
prompt = ChatPromptTemplate.from_messages([...])
question_answer_chain = create_stuff_documents_chain(llm, prompt)
chain = create_retrieval_chain(retriever, question_answer_chain)

# Use
result = await chain.ainvoke({"input": "query"})
```

### Streaming

**Query**: "How to stream LangChain responses?"
**Answer Pattern**:
```python
# Token-level streaming
async for chunk in llm.astream("query"):
    print(chunk.content, end="")

# Event streaming (detailed)
async for event in chain.astream_events({"input": "query"}, version="v2"):
    kind = event["event"]
    if kind == "on_chat_model_stream":
        content = event["data"]["chunk"].content
        print(content, end="")
```

### Multi-Agent with LangGraph

**Query**: "How to create multi-agent workflows?"
**Answer Pattern**:
```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Define state
class AgentState(TypedDict):
    messages: list
    next: str

# Create graph
workflow = StateGraph(AgentState)
workflow.add_node("agent1", agent1_node)
workflow.add_node("agent2", agent2_node)
workflow.set_entry_point("agent1")
workflow.add_edge("agent1", "agent2")
workflow.add_edge("agent2", END)

# Compile with checkpointing
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
```

## Best Practices for Scrapalot-Chat

1. **Use LCEL for Chains**: Leverage composability with `|` operator
2. **Type Safety**: Use Pydantic models for structured output
3. **Async First**: Use `ainvoke()`, `astream()` for better performance
4. **Error Handling**: Wrap LangChain calls with try/except
5. **Streaming**: Use `astream_events()` for detailed streaming with PacketEmitter
6. **Caching**: Cache LLM instances (already implemented in llm_manager.py)
7. **Observability**: Use LangSmith for tracing (optional)

## Testing After Upgrade

After upgrading to LangChain v1.x, test these critical areas:

### Must Test
1. All 18 RAG strategies execute without errors
2. All 11 orchestrators work correctly
3. Streaming responses emit proper packets
4. Vector search retrieval functions correctly
5. All LLM providers (OpenAI, Anthropic, Google, Ollama) connect
6. Document chunking strategies process correctly
7. Deep research agents complete workflows
8. Pydantic AI + LangChain integration works

### Regression Tests
```bash
# Run RAG tests
python -m pytest tests/integration/test_rag_strategies.py

# Run LLM integration tests
python -m pytest tests/integration/test_llm_providers.py

# Run streaming tests
python -m pytest tests/integration/test_streaming.py
```

## Quick Reference

### Version Compatibility Matrix

| Package | Old Version | New Version | Breaking Changes |
|---------|-------------|-------------|------------------|
| langchain | 0.3.27 | 1.2.0 | ⚠️ Chain API, Agents |
| langchain-core | 0.3.75 | 1.2.6 | ⚠️ Runnables, Streaming |
| langchain-openai | 0.3.9 | 1.1.6 | Mostly compatible |
| langchain-anthropic | 0.3.14 | 1.3.0 | Mostly compatible |
| langchain-postgres | 0.0.15 | 0.0.16 | Minor changes |

### Common Error Fixes

**Error**: `ImportError: cannot import name 'LLMChain' from 'langchain.chains'`
**Fix**: Use LCEL instead: `prompt | llm`

**Error**: `TypeError: 'Chain' object is not callable`
**Fix**: Use `.invoke()` or `.ainvoke()` instead of calling directly

**Error**: `AttributeError: 'ChatOpenAI' object has no attribute 'predict'`
**Fix**: Use `.invoke()` or streaming methods

## Resources

- **Official Docs**: https://python.langchain.com/docs/
- **Migration Guide**: https://python.langchain.com/docs/versions/migrating_chains/
- **API Reference**: https://python.langchain.com/api_reference/
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **Community**: https://github.com/langchain-ai/langchain/discussions

## Support

For LangChain-specific questions:
1. Check this skill's reference documentation
2. Search official docs with WebSearch
3. Check GitHub issues for known problems
4. Use Context7 MCP for library-specific queries

---

**Last Updated**: January 4, 2026
**LangChain Version**: 1.2.0
**Maintainer**: Scrapalot-Chat Team
