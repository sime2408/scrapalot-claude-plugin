---
name: rag-strategy-developer
description: Use this skill when developing new RAG (Retrieval Augmented Generation) strategies, orchestrators, or chunking methods for the Scrapalot-Chat project. This includes implementing new retrieval strategies, optimizing existing ones, adding orchestrators, or creating custom chunking approaches based on research papers or novel techniques.
---

# RAG Strategy Developer

## Overview

Develop, implement, and optimize RAG strategies, orchestrators, and chunking methods for the Scrapalot-Chat production RAG application. This skill provides systematic workflows for adding new retrieval strategies, creating orchestrators, implementing chunking techniques, and ensuring they integrate seamlessly with the existing tri-modal fusion architecture (pgvector + BM25 + Neo4j).

## Core Architecture Understanding

### RAG System Structure

```
src/main/service/rag/
├── rag_strategy.py              # Base RAG strategy interface
├── rag_utils.py                 # Reranking and shared utilities
├── rag_*.py                     # Individual strategy implementations (13 strategies)
├── orchestrators/               # Strategy orchestrators (9 orchestrators)
│   ├── orchestrator_adaptive.py
│   ├── orchestrator_precision.py
│   └── ...
└── chunking/                    # Chunking strategies (17+ methods)
    ├── base_chunking.py
    ├── chunking_contextual.py
    ├── chunking_late.py
    └── ...
```

### Strategy Inheritance Pattern

All RAG strategies inherit from `RAGStrategy` base class:

```python
from src.main.service.rag.rag_strategy import RAGStrategy
from typing import AsyncGenerator, List, Optional
from uuid import UUID
from langchain.schema import Document

class RAGStrategy:
    """Base class all strategies inherit from"""
    def __init__(self, llm):
        self.llm = llm
        self.retrieved_documents: List[Document] = []

    async def execute(
        self,
        query: str,
        collection_ids: Optional[List[UUID]] = None,
        **kwargs
    ) -> AsyncGenerator[str, List[Document]]:
        """Override this - retrieval logic"""
        pass

    async def process_chat_request(
        self,
        request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """Override this - streaming response"""
        pass
```

## Task 1: Implementing New RAG Strategies

### Step-by-Step Workflow

#### 1. Research and Planning

Before coding, understand the strategy:

- **Read the paper/article** describing the technique
- **Identify core mechanisms**: How does it differ from existing strategies?
- **Map to architecture**: Which components needed (retriever, reranker, graph)?
- **List dependencies**: Any new libraries or models required?
- **Check existing strategies**: Can you extend/combine existing ones?

#### 2. Create Strategy File

Create new file: `src/main/service/rag/rag_your_strategy.py`

**Template Structure:**

```python
"""
RAG Your Strategy Name

Description of what this strategy does and why.

Key Features:
- Feature 1
- Feature 2
- Feature 3

Based on: [Paper/Article Name] (Year)
Author: [Original Author]
"""

from typing import AsyncGenerator, List, Optional
from uuid import UUID
from langchain.schema import Document

from src.main.service.rag.rag_strategy import RAGStrategy
from src.main.service.rag.rag_utils import (
    rerank_documents,
    process_chat_request_with_fact_check
)
from src.main.utils.logger import get_logger, timing_decorator

logger = get_logger(__name__)


class RAGYourStrategy(RAGStrategy):
    """
    Your Strategy Name

    Detailed description of the strategy approach.

    Args:
        retriever: Vector/hybrid retriever instance
        llm: Language model instance
        packet_emitter: Optional real-time packet emitter
        config: Optional strategy configuration
    """

    def __init__(
        self,
        retriever,
        llm,
        packet_emitter=None,
        config: dict = None
    ):
        super().__init__(llm)
        self.retriever = retriever
        self.packet_emitter = packet_emitter
        self.config = config or {}

        # Strategy-specific initialization
        self.top_k = self.config.get("top_k", 10)
        self.similarity_threshold = self.config.get("similarity_threshold", 0.7)

    @timing_decorator(log_level="info")
    async def execute(
        self,
        query: str,
        collection_ids: Optional[List[UUID]] = None,
        document_ids: Optional[List[UUID]] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
    ) -> AsyncGenerator[str, List[Document]]:
        """
        Execute the strategy to retrieve relevant documents.

        Args:
            query: User query string
            collection_ids: Optional collection filter
            document_ids: Optional document filter
            top_k: Number of documents to retrieve
            similarity_threshold: Minimum similarity score

        Returns:
            AsyncGenerator that yields status updates
        """
        # MUST make this a generator function
        if False:
            yield

        try:
            logger.info("Executing RAGYourStrategy for query: %s", query[:100])

            # Emit status if streaming
            if self.packet_emitter:
                await self.packet_emitter.emit_status(
                    "Analyzing query with Your Strategy..."
                )

            # Step 1: Your retrieval logic here
            # Example: Query transformation, multi-step retrieval, etc.

            # Step 2: Retrieve documents
            documents = await self.retriever.process(
                prompt=query,
                collection_ids=collection_ids,
                document_ids=document_ids,
                top_k=top_k or self.top_k,
                similarity_threshold=similarity_threshold or self.similarity_threshold
            )

            logger.info("Retrieved %d documents", len(documents))

            # Step 3: Optional reranking
            if len(documents) > 0:
                documents = await rerank_documents(
                    query=query,
                    documents=documents,
                    retriever=self.retriever
                )
                logger.info("Reranked to %d documents", len(documents))

            # Store retrieved documents
            self.retrieved_documents = documents

            return

        except Exception as e:
            logger.error("Error in RAGYourStrategy: %s", str(e), exc_info=True)
            raise

    async def process_chat_request(
        self,
        request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """
        Process chat request and stream response.

        Args:
            request: Chat request with query and settings

        Yields:
            JSON packets for streaming response
        """
        # Use shared processing function or implement custom
        async for chunk in process_chat_request_with_fact_check(request, self):
            yield chunk
```

#### 3. Register the Strategy

Add to `src/main/utils/rag_strategies.py`:

```python
from src.main.service.rag.rag_your_strategy import RAGYourStrategy

def get_rag_strategy_class(strategy_name: str):
    """Map strategy name to class"""
    strategies = {
        # ... existing strategies ...
        "your_strategy": RAGYourStrategy,
    }
    return strategies.get(strategy_name.lower())
```

#### 4. Add Configuration

Update `configs/config.yaml`:

```yaml
rag:
  strategies:
    your_strategy:
      enabled: true
      top_k: 10
      similarity_threshold: 0.7
      # Strategy-specific settings

  prompts:
    your_strategy:
      system: "System prompt for your strategy..."
      user: "User prompt template..."
```

#### 5. Write Tests

Create `tests/service/rag/test_rag_your_strategy.py`:

```python
import pytest
from uuid import uuid4
from src.main.service.rag.rag_your_strategy import RAGYourStrategy


@pytest.mark.asyncio
@pytest.mark.rag
async def test_your_strategy_execute(mock_retriever, mock_llm):
    """Test strategy execution"""
    strategy = RAGYourStrategy(
        retriever=mock_retriever,
        llm=mock_llm
    )

    query = "Test query"
    collection_ids = [uuid4()]

    # Execute strategy (it's a generator, so iterate)
    async for _ in strategy.execute(query, collection_ids):
        pass

    # Verify documents were retrieved
    assert len(strategy.retrieved_documents) > 0
    assert mock_retriever.process.called


@pytest.mark.asyncio
@pytest.mark.rag
async def test_your_strategy_empty_results(mock_retriever, mock_llm):
    """Test handling of empty results"""
    mock_retriever.process.return_value = []

    strategy = RAGYourStrategy(retriever=mock_retriever, llm=mock_llm)

    async for _ in strategy.execute("query"):
        pass

    assert len(strategy.retrieved_documents) == 0
```

#### 6. Run and Validate

```bash
# Run tests
python -m pytest tests/service/rag/test_rag_your_strategy.py -v

# Run the service and test via API
python run_service.py

# Test via curl
curl -X POST http://localhost:5000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "Test query",
    "rag_strategy": "your_strategy",
    "collection_ids": ["collection-uuid"]
  }'
```

## Task 2: Creating RAG Orchestrators

Orchestrators combine multiple strategies intelligently.

### Orchestrator Structure

Create file: `src/main/service/rag/orchestrators/orchestrator_your_name.py`

```python
"""
Your Orchestrator Name

Description of orchestration approach.

Strategy Selection Logic:
- When to use Strategy A
- When to use Strategy B
- How strategies are combined
"""

from typing import AsyncGenerator, Dict, List, Optional
from uuid import UUID
from langchain.schema import Document

from src.main.service.rag.rag_similarity_search import RAGSimilaritySearch
from src.main.service.rag.rag_fusion import RAGFusion
from src.main.service.rag.rag_hyde import RAGHyDE
# Import other strategies as needed

from src.main.utils.logger import get_logger, timing_decorator

logger = get_logger(__name__)


class RAGOrchestratorYourName:
    """
    Your Orchestrator Name

    Intelligently selects and combines RAG strategies based on:
    - Query characteristics
    - Context requirements
    - Performance targets
    """

    def __init__(
        self,
        retriever,
        llm,
        packet_emitter=None,
        config: dict = None
    ):
        self.retriever = retriever
        self.llm = llm
        self.packet_emitter = packet_emitter
        self.config = config or {}

        # Initialize strategies
        self.similarity_strategy = RAGSimilaritySearch(retriever, llm, packet_emitter)
        self.fusion_strategy = RAGFusion(retriever, llm, packet_emitter)
        self.hyde_strategy = RAGHyDE(retriever, llm, packet_emitter)

        # Orchestrator-specific settings
        self.query_analyzer_enabled = self.config.get("query_analyzer", True)

    @timing_decorator(log_level="info")
    async def select_strategy(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> str:
        """
        Analyze query and context to select optimal strategy.

        Args:
            query: User query
            context: Optional context (conversation history, metadata)

        Returns:
            Strategy name to use
        """
        # Query analysis logic
        query_lower = query.lower()
        query_length = len(query.split())

        # Example selection logic
        if query_length < 5:
            # Short queries work better with similarity search
            return "similarity"
        elif "why" in query_lower or "how" in query_lower:
            # Conceptual questions benefit from HyDE
            return "hyde"
        elif query_length > 20:
            # Complex queries benefit from fusion
            return "fusion"
        else:
            # Default to similarity
            return "similarity"

    async def execute(
        self,
        query: str,
        collection_ids: Optional[List[UUID]] = None,
        **kwargs
    ) -> AsyncGenerator[str, List[Document]]:
        """Execute orchestration logic"""
        if False:
            yield

        try:
            # Select strategy
            strategy_name = await self.select_strategy(query)
            logger.info("Selected strategy: %s", strategy_name)

            if self.packet_emitter:
                await self.packet_emitter.emit_status(
                    f"Using {strategy_name} strategy..."
                )

            # Execute selected strategy
            strategy_map = {
                "similarity": self.similarity_strategy,
                "fusion": self.fusion_strategy,
                "hyde": self.hyde_strategy,
            }

            strategy = strategy_map.get(strategy_name, self.similarity_strategy)

            async for _ in strategy.execute(query, collection_ids, **kwargs):
                pass

            # Store results
            self.retrieved_documents = strategy.retrieved_documents

            return

        except Exception as e:
            logger.error("Error in orchestrator: %s", str(e), exc_info=True)
            raise
```

## Task 3: Implementing Chunking Strategies

### Chunking Strategy Structure

Create file: `src/main/service/rag/chunking/chunking_your_method.py`

```python
"""
Your Chunking Method

Description of chunking approach.

Benefits:
- Benefit 1
- Benefit 2

Based on: [Paper/Technique] (Year)
"""

from typing import List
from langchain.schema import Document

from src.main.service.rag.chunking.base_chunking import BaseChunkingStrategy
from src.main.utils.logger import get_logger

logger = get_logger(__name__)


class YourChunkingStrategy(BaseChunkingStrategy):
    """
    Your Chunking Method

    Detailed description of how this chunking works.

    Args:
        chunk_size: Target size for chunks (characters)
        chunk_overlap: Overlap between chunks (characters)
        **kwargs: Additional strategy-specific parameters
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        **kwargs
    ):
        super().__init__(chunk_size, chunk_overlap)

        # Strategy-specific parameters
        self.preserve_sentences = kwargs.get("preserve_sentences", True)
        self.min_chunk_size = kwargs.get("min_chunk_size", 100)

    def chunk_text(
        self,
        text: str,
        metadata: dict = None
    ) -> List[Document]:
        """
        Chunk text using your method.

        Args:
            text: Input text to chunk
            metadata: Optional metadata to attach to chunks

        Returns:
            List of Document objects with chunks
        """
        logger.info("Chunking text with YourMethod (length: %d)", len(text))

        chunks = []

        # Your chunking logic here
        # Example: Split on sentences, paragraphs, semantic boundaries, etc.

        # Placeholder - implement actual chunking
        chunk_texts = self._split_text(text)

        for i, chunk_text in enumerate(chunk_texts):
            # Skip chunks that are too small
            if len(chunk_text) < self.min_chunk_size:
                continue

            doc = Document(
                page_content=chunk_text,
                metadata={
                    **(metadata or {}),
                    'chunk_index': i,
                    'chunk_size': len(chunk_text),
                    'chunking_method': 'your_method'
                }
            )
            chunks.append(doc)

        logger.info("Created %d chunks", len(chunks))
        return chunks

    def _split_text(self, text: str) -> List[str]:
        """
        Internal method to split text into chunks.

        Args:
            text: Text to split

        Returns:
            List of chunk strings
        """
        # Implement splitting logic
        # This is where the core chunking algorithm goes

        # Placeholder implementation
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Find natural boundary if needed
            if self.preserve_sentences and end < len(text):
                # Look for sentence boundary
                boundary = text.rfind('.', start, end)
                if boundary > start:
                    end = boundary + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start with overlap
            start = end - self.chunk_overlap

        return chunks
```

## Best Practices

### Code Quality Standards

1. **Type Hints**: All function parameters and returns must have type hints
2. **Docstrings**: Google-style docstrings for all classes and methods
3. **Logging**: Use logger for info/debug/error, never print()
4. **Error Handling**: Catch exceptions, log with exc_info=True, re-raise or convert to HTTPException
5. **Async/Await**: All I/O operations must be async
6. **Testing**: Minimum 80% coverage for new code

### RAG-Specific Best Practices

1. **Always use reranking** for better result quality (unless specific reason not to)
2. **Store retrieved documents** in self.retrieved_documents for later use
3. **Emit status updates** via packet_emitter for user feedback
4. **Use timing_decorator** on execute() methods for performance tracking
5. **Load prompts from config** - never hardcode prompts in code
6. **Handle empty results gracefully** - don't fail on zero documents
7. **Support collection and document filtering** - core requirement

### Configuration Management

All strategy configuration goes in `configs/config.yaml`:

```yaml
rag:
  strategies:
    your_strategy:
      enabled: true
      top_k: 10
      similarity_threshold: 0.7
      custom_param: value

  prompts:
    your_strategy:
      system: |
        You are a helpful assistant.
        Context: {context}
      user: |
        Question: {query}

        Answer based on the context provided.
```

Access in code:

```python
from src.main.utils.config_loader import resolved_config

config = resolved_config.get("rag", {})
strategy_config = config.get("strategies", {}).get("your_strategy", {})
top_k = strategy_config.get("top_k", 10)
```

## Testing Workflow

### Unit Tests

```bash
# Run specific strategy tests
python -m pytest tests/service/rag/test_rag_your_strategy.py -v

# Run all RAG tests
python -m pytest tests/service/rag/ -v -m rag

# Run with coverage
python -m pytest tests/service/rag/ --cov=src/main/service/rag --cov-report=html
```

### Integration Tests

Test full flow with database:

```python
@pytest.mark.integration
@pytest.mark.database_required
async def test_strategy_full_flow(db_session, test_user):
    """Test complete strategy flow with database"""
    # Create test collection and documents
    collection = create_test_collection(db_session, test_user.id)
    documents = create_test_documents(db_session, collection.id)

    # Initialize strategy with real retriever
    retriever = await RetrieverManager.get_retriever(
        db=db_session,
        user_id=test_user.id
    )

    llm = await LLMManager.get_llm(
        model_name="gpt-4o-mini",
        provider_type="openai",
        db=db_session,
        user_id=test_user.id
    )

    strategy = RAGYourStrategy(retriever, llm)

    # Execute and verify
    async for _ in strategy.execute("test query", [collection.id]):
        pass

    assert len(strategy.retrieved_documents) > 0
```

## Common Patterns

### Multi-Step Retrieval

```python
async def execute(self, query: str, **kwargs):
    if False:
        yield

    # Step 1: Transform query
    transformed_queries = await self._transform_query(query)

    # Step 2: Retrieve for each variant
    all_documents = []
    for tq in transformed_queries:
        docs = await self.retriever.process(tq, **kwargs)
        all_documents.extend(docs)

    # Step 3: Deduplicate and rerank
    unique_docs = self._deduplicate(all_documents)
    ranked_docs = await rerank_documents(query, unique_docs, self.retriever)

    self.retrieved_documents = ranked_docs
    return
```

### Hybrid Retrieval (Vector + Graph)

```python
from src.main.service.retriever.retriever_neo4j import RetrieverNeo4j

async def execute(self, query: str, collection_ids: List[UUID], **kwargs):
    if False:
        yield

    # Vector retrieval
    vector_docs = await self.retriever.process(
        query, collection_ids, top_k=20
    )

    # Graph retrieval (if Neo4j available)
    graph_docs = []
    if isinstance(self.retriever, RetrieverNeo4j):
        graph_docs = await self.retriever.graph_search(
            query, collection_ids, top_k=10
        )

    # Combine and rerank
    combined = vector_docs + graph_docs
    final_docs = await rerank_documents(query, combined, self.retriever)

    self.retrieved_documents = final_docs[:kwargs.get("top_k", 10)]
    return
```

## Task 4: Implementing Agentic RAG Strategy Routing

### Overview

Agentic RAG routing uses Pydantic AI agents to intelligently analyze queries and route them to optimal RAG strategies. This replaces manual strategy selection with AI-powered decision making.

### Key Components

**Location**: `src/main/service/agents/rag_agents/strategy_router.py`

**Pydantic Models**:
```python
from pydantic import BaseModel, Field

class QueryCharacteristics(BaseModel):
    """Analysis of query characteristics"""
    query_type: str  # factual, conceptual, relational, analytical, conversational
    complexity_score: int  # 1-5 scale
    intent: str  # information_lookup, comparison, synthesis, exploration
    domain_indicators: List[str]
    requires_multi_hop: bool
    requires_relationships: bool
    key_entities: List[str]

class StrategyRouting(BaseModel):
    """RAG strategy routing decision"""
    use_orchestrator: bool
    selected_strategy: str  # e.g., "RAGTriModalFusionOrchestrator"
    fallback_strategy: str
    reasoning: str
    confidence: float  # 0.0-1.0
    estimated_latency: str  # fast, medium, slow
    query_characteristics: QueryCharacteristics
```

### Creating Routing Agent

**System Prompt Location**: `configs/config.yaml` under `defaults.agentic_routing_system_prompt`

```python
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

def create_strategy_router_agent(
    model_name: str = "openai:gpt-4o-mini",
) -> Agent[RAGDependencies, StrategyRouting]:
    """Create RAG strategy routing agent"""

    # Load system prompt from config
    from src.main.utils.config_loader import resolved_config
    defaults = resolved_config.get("defaults", {})
    routing_prompt = defaults.get("agentic_routing_system_prompt", "")

    # Format with available strategies
    system_prompt = routing_prompt.format(
        individual_strategies=individual_strategies_text,
        orchestrators=orchestrators_text,
    )

    # Create agent with correct parameters
    agent = Agent(
        model_name,
        deps_type=RAGDependencies,
        output_type=StrategyRouting,  # Note: output_type, NOT result_type!
        system_prompt=system_prompt,
        model_settings=ModelSettings(
            timeout=30.0,
            temperature=0.0,  # Deterministic routing
        ),
    )

    return agent
```

### Streaming Routing Decisions

```python
async def route_to_rag_strategy(
    query: str,
    collection_ids: Optional[List[UUID]],
    deps: RAGDependencies,
    model_name: str = "openai:gpt-4o-mini",
) -> AsyncGenerator[str, None]:
    """Route query with streaming status updates"""

    from src.main.service.streaming.packet_emitter import PacketEmitter
    emitter = PacketEmitter()

    try:
        # Emit status (use valid UI stage: "processing")
        yield emitter.emit_status(
            "Analyzing query to select optimal RAG strategy...",
            stage="processing"  # Valid stages: init, retrieval, generation, processing, research, search, fact_check
        )

        # Get cached agent
        from src.main.service.agents.agent_factory import AgentFactory
        wrapped_agent = await AgentFactory.get_agent(
            agent_type="rag_strategy_router",
            model_name=model_name,
            user_id=deps.user_id,
        )

        # Run agent
        routing_decision = await wrapped_agent.run_sync_with_deps(
            routing_prompt,
            deps=deps,
        )

        # Emit routing decision packets
        yield emitter.emit_status(
            f"🎯 Selected strategy: {routing_decision.selected_strategy}",
            stage="processing"
        )

        # Yield final routing decision as special packet
        yield json.dumps({
            "type": "routing_decision",
            "content": routing_decision.model_dump(),
        }) + "\n"

    except Exception as e:
        logger.error("Routing failed: %s", str(e), exc_info=True)
        yield emitter.emit_error(
            f"Failed to route query: {str(e)}",
            error_code="ROUTING_FAILED"
        )
        # Yield fallback routing decision...
```

### Integration with Chat Controller

**File**: `src/main/controllers/chat.py`

```python
# Check user settings for agentic routing preference
general_settings = db.query(UserSetting).filter(...).first()
use_agentic_routing = settings_dict.get("use_agentic_routing", True)

if use_agentic_routing:
    # AI-powered routing
    routing_packets = []
    async for packet in get_agentic_rag_strategy_with_streaming(
        query=request.prompt,
        collection_ids=request.collection_ids,
        user_id=user_id,
        db=db,
    ):
        yield packet
        routing_packets.append(packet)

    strategy_name, strategy_type, strategy_class = extract_strategy_from_packets(
        routing_packets
    )
else:
    # Manual selection from user settings
    if settings_dict.get("use_orchestrator", True):
        strategy_name = settings_dict.get("rag_orchestrator", DEFAULT_RAG_ORCHESTRATOR)
        strategy_type = "orchestrator"
    else:
        strategy_name = settings_dict.get("rag_strategy", DEFAULT_RAG_STRATEGY)
        strategy_type = "individual"

    strategy_class = get_rag_strategy_class(strategy_name)
```

### UI Integration

**Settings Toggle**: `scrapalot-ui/src/components/settings/settings-tab-general.tsx`

```typescript
// State management
const [useAgenticRouting, setUseAgenticRouting] = useState<boolean>(true);

// UI Toggle Component
<Switch
  id='use-agentic-routing'
  checked={useAgenticRouting}
  onCheckedChange={setUseAgenticRouting}
/>

// Conditional rendering of manual strategy selection
{!useAgenticRouting && (
  <div>
    {/* Manual orchestrator/strategy dropdowns */}
  </div>
)}
```

**Status Indicator**: `scrapalot-ui/src/components/chat/chat-status-indicator.tsx`

Valid stage types for UI display:
- `init` - Initialization (Loader icon, blue)
- `retrieval` - Document retrieval (Search icon, violet)
- `generation` - Answer generation (Brain icon, purple)
- `processing` - Analysis/processing (Zap icon, blue) ← **Use for routing**
- `research` - Research mode (Zap icon, orange)
- `search` - Web search (Search icon, violet)
- `fact_check` - Fact checking (CheckCircle icon, green)

### Configuration

**System Prompt**: `configs/config.yaml`

```yaml
defaults:
  agentic_routing_system_prompt: |
    You are an expert RAG (Retrieval Augmented Generation) strategy router.

    Your job is to analyze user queries and route them to the optimal RAG strategy...

    {individual_strategies}
    {orchestrators}

    ## Routing Guidelines:
    1. Simple Factual Queries → RAGSimilaritySearch
    2. Metadata Filters → RAGSelfQuery
    3. Vocabulary Mismatch → RAGHyDE
    ...
```

**User Settings**: Database table `user_settings` with key `settings_general`

```json
{
  "use_agentic_routing": true,
  "use_orchestrator": true,
  "rag_orchestrator": "RAGTriModalFusionOrchestrator",
  "rag_strategy": "RAGSimilaritySearch"
}
```

### Database Migration

**File**: `alembic/versions/037_add_use_agentic_routing_setting.py`

```python
def update_user_settings_with_agentic_routing():
    """Add use_agentic_routing flag to existing users"""
    connection = op.get_bind()

    user_settings = connection.execute(
        text(f"""
            SELECT id, user_id, setting_value
            FROM {db_utils.get_table_name('user_settings')}
            WHERE setting_key = 'settings_general'
        """)
    ).fetchall()

    for setting in user_settings:
        settings_dict = json.loads(setting.setting_value)

        if "use_agentic_routing" not in settings_dict:
            settings_dict["use_agentic_routing"] = True  # Default to enabled

            connection.execute(
                text(f"""
                    UPDATE {db_utils.get_table_name('user_settings')}
                    SET setting_value = :setting_value
                    WHERE id = :setting_id
                """),
                {
                    "setting_value": json.dumps(settings_dict),
                    "setting_id": setting.id,
                },
            )
```

### Common Patterns

**Confidence Threshold Fallback**:

```python
if routing_decision.confidence < 0.5:
    logger.warning("Low confidence, falling back to RAGTriModalFusionOrchestrator")
    strategy_name = "RAGTriModalFusionOrchestrator"
    strategy_type = "orchestrator"
```

**Defense-in-Depth**:

The agentic routing check exists in two layers:
1. **Chat controller** - Checks `use_agentic_routing` upfront (fast path)
2. **Agentic routing module** - Also checks internally (defense-in-depth)

### Best Practices

1. **Always use valid stage codes** for `emit_status()` - UI won't recognize custom stages
2. **Load prompts from config** - Never hardcode routing logic in Python
3. **Use `output_type` not `result_type`** - Pydantic AI parameter naming
4. **Cache agents** via `AgentFactory` - Avoid recreating on every request
5. **Provide fallback routing** - Handle agent failures gracefully
6. **Stream thinking tokens** - Better UX with real-time updates
7. **Default to agentic routing** - Set `use_agentic_routing: true` for new users

### Testing

```python
@pytest.mark.asyncio
async def test_agentic_routing():
    from src.main.service.agents.rag_agents.strategy_router import route_to_rag_strategy

    deps = RAGDependencies(
        db=mock_db,
        user_id="test_user",
        collection_ids=[uuid4()],
    )

    packets = []
    async for packet in route_to_rag_strategy(
        query="What is climate change?",
        collection_ids=deps.collection_ids,
        deps=deps,
    ):
        packets.append(packet)

    # Verify routing decision packet exists
    assert any("routing_decision" in p for p in packets)
```

### Common Issues

1. **"Unexpected argument(s)"** → Use `output_type` not `result_type`
2. **UI not showing status** → Use valid stage codes (processing, retrieval, etc.)
3. **Routing not working** → Check `use_agentic_routing` flag in user settings
4. **Low accuracy** → Adjust routing prompt in config.yaml
5. **Slow routing** → Use faster model (gpt-4o-mini) or increase timeout

## Reference Documentation

For detailed information, consult:

- `docs/README_RAG_ARCHITECTURE.md` - Complete RAG system overview (includes agentic routing section)
- `docs/RAG_STRATEGY_COMPARISON_ANALYSIS.md` - Comparison of all 13 strategies
- `.claude/skills/pydantic-ai/SKILL.md` - Pydantic AI agent development guide
- `CLAUDE.md` - Project-wide conventions and patterns

Load when:
- Implementing complex multi-stage strategies
- Optimizing performance of existing strategies
- Understanding strategy selection in orchestrators
- Debugging retrieval issues
- Adding AI-powered query routing
