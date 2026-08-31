# Documentation

## Table of Contents

1. [Streaming - Docs by LangChain](#doc-1)
2. [Multi-agent - Docs by LangChain](#doc-2)
3. [Router - Docs by LangChain](#doc-3)
4. [Skills - Docs by LangChain](#doc-4)
5. [Handoffs - Docs by LangChain](#doc-5)
6. [Subagents - Docs by LangChain](#doc-6)
7. [Get help - Docs by LangChain](#doc-7)
8. [Component architecture - Docs by LangChain](#doc-8)
9. [Build a SQL assistant with on-demand skills - Docs by LangChain](#doc-9)
10. [Build a multi-source knowledge base with routing - Docs by LangChain](#doc-10)
11. [Build customer support with handoffs - Docs by LangChain](#doc-11)
12. [Build a personal assistant with subagents - Docs by LangChain](#doc-12)
13. [Build a voice agent with LangChain - Docs by LangChain](#doc-13)
14. [Build a SQL agent - Docs by LangChain](#doc-14)
15. [Custom workflow - Docs by LangChain](#doc-15)
16. [Build a semantic search engine with LangChain - Docs by LangChain](#doc-16)
17. [Multi-agent - Docs by LangChain](#doc-17)
18. [Build a RAG agent with LangChain - Docs by LangChain](#doc-18)
19. [Overview - Docs by LangChain](#doc-19)
20. [Changelog - Docs by LangChain](#doc-20)
21. [LangSmith Observability - Docs by LangChain](#doc-21)
22. [LangSmith Deployment - Docs by LangChain](#doc-22)
23. [Agent Chat UI - Docs by LangChain](#doc-23)
24. [Test - Docs by LangChain](#doc-24)
25. [Model Context Protocol (MCP) - Docs by LangChain](#doc-25)
26. [Retrieval - Docs by LangChain](#doc-26)
27. [LangSmith Studio - Docs by LangChain](#doc-27)
28. [Long-term memory - Docs by LangChain](#doc-28)
29. [Human-in-the-loop - Docs by LangChain](#doc-29)
30. [Runtime - Docs by LangChain](#doc-30)
31. [Context engineering in agents - Docs by LangChain](#doc-31)
32. [Guardrails - Docs by LangChain](#doc-32)
33. [Custom middleware - Docs by LangChain](#doc-33)
34. [Built-in middleware - Docs by LangChain](#doc-34)
35. [Overview - Docs by LangChain](#doc-35)
36. [Structured output - Docs by LangChain](#doc-36)
37. [Short-term memory - Docs by LangChain](#doc-37)
38. [Tools - Docs by LangChain](#doc-38)
39. [Messages - Docs by LangChain](#doc-39)
40. [Models - Docs by LangChain](#doc-40)
41. [Agents - Docs by LangChain](#doc-41)
42. [Philosophy - Docs by LangChain](#doc-42)
43. [Quickstart - Docs by LangChain](#doc-43)
44. [Install LangChain - Docs by LangChain](#doc-44)
45. [LangChain overview - Docs by LangChain](#doc-45)

---

## Streaming - Docs by LangChain {#doc-1}

**Source:** [https://docs.langchain.com/oss/python/langchain/streaming](https://docs.langchain.com/oss/python/langchain/streaming)

### Streaming

Copy page

#### ​Overview

LangChain’s streaming system lets you surface live feedback from agent runs to your application.

What’s possible with LangChain streaming:

- Stream agent progress — get state updates after each agent step.
- Stream LLM tokens — stream language model tokens as they’re generated.
- Stream custom updates — emit user-defined signals (e.g., "Fetched 10/100 records").
- Stream multiple modes — choose from updates (agent progress), messages (LLM tokens + metadata), or custom (arbitrary user data).
See the common patterns section below for additional end-to-end examples.

#### ​Supported stream modes

Pass one or more of the following stream modes as a list to the stream or astream methods:

ModeDescriptionupdatesStreams state updates after each agent step. If multiple updates are made in the same step (e.g., multiple nodes are run), those updates are streamed separately.messagesStreams tuples of (token, metadata) from any graph nodes where an LLM is invoked.customStreams custom data from inside your graph nodes using the stream writer.

#### ​Agent progress

To stream agent progress, use the stream or astream methods with stream_mode="updates". This emits an event after every agent step.

For example, if you have an agent that calls a tool once, you should see the following updates:

- LLM node: AIMessage with tool call requests
- Tool node: ToolMessage with execution result
- LLM node: Final AI response
Streaming agent progressCopyfrom langchain.agents import create_agent

```python
def get_weather(city: str) -> str:
    """Get weather for a given city."""

    return f"It's always sunny in {city}!"

agent = create_agent(
    model="gpt-5-nano",
    tools=[get_weather],
)
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
    stream_mode="updates",
):
    for step, data in chunk.items():
        print(f"step: {step}")
        print(f"content: {data['messages'][-1].content_blocks}")

OutputCopystep: model
content: [{'type': 'tool_call', 'name': 'get_weather', 'args': {'city': 'San Francisco'}, 'id': 'call_OW2NYNsNSKhRZpjW0wm2Aszd'}]

step: tools
content: [{'type': 'text', 'text': "It's always sunny in San Francisco!"}]

step: model
content: [{'type': 'text', 'text': 'It's always sunny in San Francisco!'}]
```

#### ​LLM tokens

To stream tokens as they are produced by the LLM, use stream_mode="messages". Below you can see the output of the agent streaming tool calls and the final response.

Streaming LLM tokensCopyfrom langchain.agents import create_agent

```python
def get_weather(city: str) -> str:
    """Get weather for a given city."""

    return f"It's always sunny in {city}!"

agent = create_agent(
    model="gpt-5-nano",
    tools=[get_weather],
)
for token, metadata in agent.stream(
    {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
    stream_mode="messages",
):
    print(f"node: {metadata['langgraph_node']}")
    print(f"content: {token.content_blocks}")
    print("\n")

OutputCopynode: model
content: [{'type': 'tool_call_chunk', 'id': 'call_vbCyBcP8VuneUzyYlSBZZsVa', 'name': 'get_weather', 'args': '', 'index': 0}]

node: model
content: [{'type': 'tool_call_chunk', 'id': None, 'name': None, 'args': '{"', 'index': 0}]

node: model
content: [{'type': 'tool_call_chunk', 'id': None, 'name': None, 'args': 'city', 'index': 0}]

node: model
content: [{'type': 'tool_call_chunk', 'id': None, 'name': None, 'args': '":"', 'index': 0}]

node: model
content: [{'type': 'tool_call_chunk', 'id': None, 'name': None, 'args': 'San', 'index': 0}]

node: model
content: [{'type': 'tool_call_chunk', 'id': None, 'name': None, 'args': ' Francisco', 'index': 0}]

node: model
content: [{'type': 'tool_call_chunk', 'id': None, 'name': None, 'args': '"}', 'index': 0}]

node: model
content: []

node: tools
content: [{'type': 'text', 'text': "It's always sunny in San Francisco!"}]

node: model
content: []

node: model
content: [{'type': 'text', 'text': 'Here'}]

node: model
content: [{'type': 'text', 'text': ''s'}]

node: model
content: [{'type': 'text', 'text': ' what'}]

node: model
content: [{'type': 'text', 'text': ' I'}]

node: model
content: [{'type': 'text', 'text': ' got'}]

node: model
content: [{'type': 'text', 'text': ':'}]

node: model
content: [{'type': 'text', 'text': ' "'}]

node: model
content: [{'type': 'text', 'text': "It's"}]

node: model
content: [{'type': 'text', 'text': ' always'}]

node: model
content: [{'type': 'text', 'text': ' sunny'}]

node: model
content: [{'type': 'text', 'text': ' in'}]

node: model
content: [{'type': 'text', 'text': ' San'}]

node: model
content: [{'type': 'text', 'text': ' Francisco'}]

node: model
content: [{'type': 'text', 'text': '!"\n\n'}]
See all 94 lines
```

#### ​Custom updates

To stream updates from tools as they are executed, you can use get_stream_writer.

Streaming custom updatesCopyfrom langchain.agents import create_agent
```python
from langgraph.config import get_stream_writer

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    writer = get_stream_writer()
    # stream any arbitrary data
    writer(f"Looking up data for city: {city}")
    writer(f"Acquired data for city: {city}")
    return f"It's always sunny in {city}!"

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[get_weather],
)

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
    stream_mode="custom"
):
    print(chunk)

OutputCopyLooking up data for city: San Francisco
Acquired data for city: San Francisco

If you add get_stream_writer inside your tool, you won’t be able to invoke the tool outside of a LangGraph execution context.
```

#### ​Stream multiple modes

You can specify multiple streaming modes by passing stream mode as a list: stream_mode=["updates", "custom"].

The streamed outputs will be tuples of (mode, chunk) where mode is the name of the stream mode and chunk is the data streamed by that mode.

Streaming multiple modesCopyfrom langchain.agents import create_agent
```python
from langgraph.config import get_stream_writer

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    writer = get_stream_writer()
    writer(f"Looking up data for city: {city}")
    writer(f"Acquired data for city: {city}")
    return f"It's always sunny in {city}!"

agent = create_agent(
    model="gpt-5-nano",
    tools=[get_weather],
)

for stream_mode, chunk in agent.stream(
    {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
    stream_mode=["updates", "custom"]
):
    print(f"stream_mode: {stream_mode}")
    print(f"content: {chunk}")
    print("\n")

OutputCopystream_mode: updates
content: {'model': {'messages': [AIMessage(content='', response_metadata={'token_usage': {'completion_tokens': 280, 'prompt_tokens': 132, 'total_tokens': 412, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 256, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_provider': 'openai', 'model_name': 'gpt-5-nano-2025-08-07', 'system_fingerprint': None, 'id': 'chatcmpl-C9tlgBzGEbedGYxZ0rTCz5F7OXpL7', 'service_tier': 'default', 'finish_reason': 'tool_calls', 'logprobs': None}, id='lc_run--480c07cb-e405-4411-aa7f-0520fddeed66-0', tool_calls=[{'name': 'get_weather', 'args': {'city': 'San Francisco'}, 'id': 'call_KTNQIftMrl9vgNwEfAJMVu7r', 'type': 'tool_call'}], usage_metadata={'input_tokens': 132, 'output_tokens': 280, 'total_tokens': 412, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 256}})]}}

stream_mode: custom
content: Looking up data for city: San Francisco

stream_mode: custom
content: Acquired data for city: San Francisco

stream_mode: updates
content: {'tools': {'messages': [ToolMessage(content="It's always sunny in San Francisco!", name='get_weather', tool_call_id='call_KTNQIftMrl9vgNwEfAJMVu7r')]}}

stream_mode: updates
content: {'model': {'messages': [AIMessage(content='San Francisco weather: It's always sunny in San Francisco!\n\n', response_metadata={'token_usage': {'completion_tokens': 764, 'prompt_tokens': 168, 'total_tokens': 932, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 704, 'rejected_prediction_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 0}}, 'model_provider': 'openai', 'model_name': 'gpt-5-nano-2025-08-07', 'system_fingerprint': None, 'id': 'chatcmpl-C9tljDFVki1e1haCyikBptAuXuHYG', 'service_tier': 'default', 'finish_reason': 'stop', 'logprobs': None}, id='lc_run--acbc740a-18fe-4a14-8619-da92a0d0ee90-0', usage_metadata={'input_tokens': 168, 'output_tokens': 764, 'total_tokens': 932, 'input_token_details': {'audio': 0, 'cache_read': 0}, 'output_token_details': {'audio': 0, 'reasoning': 704}})]}}
```

#### ​Common patterns

Below are examples showing common use cases for streaming.

##### ​Streaming tool calls

You may want to stream both:

- Partial JSON as tool calls are generated
- The completed, parsed tool calls that are executed
Specifying stream_mode="messages" will stream incremental message chunks generated by all LLM calls in the agent. To access the completed messages with parsed tool calls:

- If those messages are tracked in the state (as in the model node of create_agent), use stream_mode=["messages", "updates"] to access completed messages through state updates (demonstrated below).
- If those messages are not tracked in the state, use custom updates or aggregate the chunks during the streaming loop (next section).
Refer to the section below on streaming from sub-agents if your agent includes multiple LLMs.

Copyfrom typing import Any

```python
from langchain.agents import create_agent
from langchain.messages import AIMessage, AIMessageChunk, AnyMessage, ToolMessage

def get_weather(city: str) -> str:
    """Get weather for a given city."""

    return f"It's always sunny in {city}!"

agent = create_agent("openai:gpt-5.2", tools=[get_weather])

def _render_message_chunk(token: AIMessageChunk) -> None:
    if token.text:
        print(token.text, end="|")
    if token.tool_call_chunks:
        print(token.tool_call_chunks)
    # N.B. all content is available through token.content_blocks

def _render_completed_message(message: AnyMessage) -> None:
    if isinstance(message, AIMessage) and message.tool_calls:
        print(f"Tool calls: {message.tool_calls}")
    if isinstance(message, ToolMessage):
        print(f"Tool response: {message.content_blocks}")

input_message = {"role": "user", "content": "What is the weather in Boston?"}
for stream_mode, data in agent.stream(
    {"messages": [input_message]},
    stream_mode=["messages", "updates"],
):
    if stream_mode == "messages":
        token, metadata = data
        if isinstance(token, AIMessageChunk):
            _render_message_chunk(token)
    if stream_mode == "updates":
        for source, update in data.items():
            if source in ("model", "tools"):  # `source` captures node name
                _render_completed_message(update["messages"][-1])

OutputCopy[{'name': 'get_weather', 'args': '', 'id': 'call_D3Orjr89KgsLTZ9hTzYv7Hpf', 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '{"', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': 'city', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '":"', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': 'Boston', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '"}', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
Tool calls: [{'name': 'get_weather', 'args': {'city': 'Boston'}, 'id': 'call_D3Orjr89KgsLTZ9hTzYv7Hpf', 'type': 'tool_call'}]
Tool response: [{'type': 'text', 'text': "It's always sunny in Boston!"}]
The| weather| in| Boston| is| **|sun|ny|**|.|
See all 9 lines
```

###### ​Accessing completed messages

If completed messages are tracked in an agent’s state, you can use stream_mode=["messages", "updates"] as demonstrated above to access completed messages during streaming.

In some cases, completed messages are not reflected in state updates. If you have access to the agent internals, you can use custom updates to access these messages during streaming. Otherwise, you can aggregate message chunks in the streaming loop (see below).

Consider the below example, where we incorporate a stream writer into a simplified guardrail middleware. This middleware demonstrates tool calling to generate a structured “safe / unsafe” evaluation (one could also use structured outputs for this):

Copyfrom typing import Any, Literal

```python
from langchain.agents.middleware import after_agent, AgentState
from langgraph.runtime import Runtime
from langchain.messages import AIMessage
from langchain.chat_models import init_chat_model
from langgraph.config import get_stream_writer
from pydantic import BaseModel

class ResponseSafety(BaseModel):
    """Evaluate a response as safe or unsafe."""
    evaluation: Literal["safe", "unsafe"]

safety_model = init_chat_model("openai:gpt-5.2")

@after_agent(can_jump_to=["end"])
def safety_guardrail(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Model-based guardrail: Use an LLM to evaluate response safety."""
    stream_writer = get_stream_writer()
    # Get the model response
    if not state["messages"]:
        return None

    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage):
        return None

    # Use another model to evaluate safety
    model_with_tools = safety_model.bind_tools([ResponseSafety], tool_choice="any")
    result = model_with_tools.invoke(
        [
            {
                "role": "system",
                "content": "Evaluate this AI response as generally safe or unsafe.",
            }
        ],
        {"role": "user", "content": f"AI response: {last_message.text}"},
    )
    stream_writer(result)

    tool_call = result.tool_calls[0]
    if tool_call["args"]["evaluation"] == "unsafe":
        last_message.content = "I cannot provide that response. Please rephrase your request."

    return None

We can then incorporate this middleware into our agent and include its custom stream events:

Copyfrom typing import Any

from langchain.agents import create_agent
from langchain.messages import AIMessageChunk, AIMessage, AnyMessage

def get_weather(city: str) -> str:
    """Get weather for a given city."""

    return f"It's always sunny in {city}!"

agent = create_agent(
    model="openai:gpt-5.2",
    tools=[get_weather],
    middleware=[safety_guardrail],
)

def _render_message_chunk(token: AIMessageChunk) -> None:
    if token.text:
        print(token.text, end="|")
    if token.tool_call_chunks:
        print(token.tool_call_chunks)

def _render_completed_message(message: AnyMessage) -> None:
    if isinstance(message, AIMessage) and message.tool_calls:
        print(f"Tool calls: {message.tool_calls}")
    if isinstance(message, ToolMessage):
        print(f"Tool response: {message.content_blocks}")

input_message = {"role": "user", "content": "What is the weather in Boston?"}
for stream_mode, data in agent.stream(
    {"messages": [input_message]},
    stream_mode=["messages", "updates", "custom"],
):
    if stream_mode == "messages":
        token, metadata = data
        if isinstance(token, AIMessageChunk):
            _render_message_chunk(token)
    if stream_mode == "updates":
        for source, update in data.items():
            if source in ("model", "tools"):
                _render_completed_message(update["messages"][-1])
    if stream_mode == "custom":
        # access completed message in stream
        print(f"Tool calls: {data.tool_calls}")

OutputCopy[{'name': 'get_weather', 'args': '', 'id': 'call_je6LWgxYzuZ84mmoDalTYMJC', 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '{"', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': 'city', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '":"', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': 'Boston', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '"}', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
Tool calls: [{'name': 'get_weather', 'args': {'city': 'Boston'}, 'id': 'call_je6LWgxYzuZ84mmoDalTYMJC', 'type': 'tool_call'}]
Tool response: [{'type': 'text', 'text': "It's always sunny in Boston!"}]
The| weather| in| **|Boston|**| is| **|sun|ny|**|.|[{'name': 'ResponseSafety', 'args': '', 'id': 'call_O8VJIbOG4Q9nQF0T8ltVi58O', 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '{"', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': 'evaluation', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '":"', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': 'unsafe', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '"}', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
Tool calls: [{'name': 'ResponseSafety', 'args': {'evaluation': 'unsafe'}, 'id': 'call_O8VJIbOG4Q9nQF0T8ltVi58O', 'type': 'tool_call'}]
See all 15 lines

Alternatively, if you aren’t able to add custom events to the stream, you can aggregate message chunks within the streaming loop:

Copyinput_message = {"role": "user", "content": "What is the weather in Boston?"}
full_message = None
for stream_mode, data in agent.stream(
    {"messages": [input_message]},
    stream_mode=["messages", "updates"],
):
    if stream_mode == "messages":
        token, metadata = data
        if isinstance(token, AIMessageChunk):
            _render_message_chunk(token)
            full_message = token if full_message is None else full_message + token
            if token.chunk_position == "last":
                if full_message.tool_calls:
                    print(f"Tool calls: {full_message.tool_calls}")
                full_message = None
    if stream_mode == "updates":
        for source, update in data.items():
            if source == "tools":
                _render_completed_message(update["messages"][-1])
```

##### ​Streaming with human-in-the-loop

To handle human-in-the-loop interrupts, we build on the above example:

- We configure the agent with human-in-the-loop middleware and a checkpointer
- We collect interrupts generated during the "updates" stream mode
- We respond to those interrupts with a command
Copyfrom typing import Any

```python
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.messages import AIMessage, AIMessageChunk, AnyMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, Interrupt

def get_weather(city: str) -> str:
    """Get weather for a given city."""

    return f"It's always sunny in {city}!"

checkpointer = InMemorySaver()

agent = create_agent(
    "openai:gpt-5.2",
    tools=[get_weather],
    middleware=[
        HumanInTheLoopMiddleware(interrupt_on={"get_weather": True}),
    ],
    checkpointer=checkpointer,
)

def _render_message_chunk(token: AIMessageChunk) -> None:
    if token.text:
        print(token.text, end="|")
    if token.tool_call_chunks:
        print(token.tool_call_chunks)

def _render_completed_message(message: AnyMessage) -> None:
    if isinstance(message, AIMessage) and message.tool_calls:
        print(f"Tool calls: {message.tool_calls}")
    if isinstance(message, ToolMessage):
        print(f"Tool response: {message.content_blocks}")

def _render_interrupt(interrupt: Interrupt) -> None:
    interrupts = interrupt.value
    for request in interrupts["action_requests"]:
        print(request["description"])

input_message = {
    "role": "user",
    "content": (
        "Can you look up the weather in Boston and San Francisco?"
    ),
}
config = {"configurable": {"thread_id": "some_id"}}
interrupts = []
for stream_mode, data in agent.stream(
    {"messages": [input_message]},
    config=config,
    stream_mode=["messages", "updates"],
):
    if stream_mode == "messages":
        token, metadata = data
        if isinstance(token, AIMessageChunk):
            _render_message_chunk(token)
    if stream_mode == "updates":
        for source, update in data.items():
            if source in ("model", "tools"):
                _render_completed_message(update["messages"][-1])
            if source == "__interrupt__":
                interrupts.extend(update)
                _render_interrupt(update[0])

OutputCopy[{'name': 'get_weather', 'args': '', 'id': 'call_GOwNaQHeqMixay2qy80padfE', 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '{"ci', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': 'ty": ', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '"Bosto', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': 'n"}', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': 'get_weather', 'args': '', 'id': 'call_Ndb4jvWm2uMA0JDQXu37wDH6', 'index': 1, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '{"ci', 'id': None, 'index': 1, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': 'ty": ', 'id': None, 'index': 1, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '"San F', 'id': None, 'index': 1, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': 'ranc', 'id': None, 'index': 1, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': 'isco"', 'id': None, 'index': 1, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '}', 'id': None, 'index': 1, 'type': 'tool_call_chunk'}]
Tool calls: [{'name': 'get_weather', 'args': {'city': 'Boston'}, 'id': 'call_GOwNaQHeqMixay2qy80padfE', 'type': 'tool_call'}, {'name': 'get_weather', 'args': {'city': 'San Francisco'}, 'id': 'call_Ndb4jvWm2uMA0JDQXu37wDH6', 'type': 'tool_call'}]
Tool execution requires approval

Tool: get_weather
Args: {'city': 'Boston'}
Tool execution requires approval

Tool: get_weather
Args: {'city': 'San Francisco'}
See all 21 lines

We next collect a decision for each interrupt. Importantly, the order of decisions must match the order of actions we collected.

To illustrate, we will edit one tool call and accept the other:

Copydef _get_interrupt_decisions(interrupt: Interrupt) -> list[dict]:
    return [
        {
            "type": "edit",
            "edited_action": {
                "name": "get_weather",
                "args": {"city": "Boston, U.K."},
            },
        }
        if "boston" in request["description"].lower()
        else {"type": "approve"}
        for request in interrupt.value["action_requests"]
    ]

decisions = {}
for interrupt in interrupts:
    decisions[interrupt.id] = {
        "decisions": _get_interrupt_decisions(interrupt)
    }

decisions

OutputCopy{
    'a96c40474e429d661b5b32a8d86f0f3e': {
        'decisions': [
            {
                'type': 'edit',
                 'edited_action': {
                     'name': 'get_weather',
                     'args': {'city': 'Boston, U.K.'}
                 }
            },
            {'type': 'approve'},
        ]
    }
}

We can then resume by passing a command into the same streaming loop:

Copyinterrupts = []
for stream_mode, data in agent.stream(
    Command(resume=decisions),
    config=config,
    stream_mode=["messages", "updates"],
):
    # Streaming loop is unchanged
    if stream_mode == "messages":
        token, metadata = data
        if isinstance(token, AIMessageChunk):
            _render_message_chunk(token)
    if stream_mode == "updates":
        for source, update in data.items():
            if source in ("model", "tools"):
                _render_completed_message(update["messages"][-1])
            if source == "__interrupt__":
                interrupts.extend(update)
                _render_interrupt(update[0])

OutputCopyTool response: [{'type': 'text', 'text': "It's always sunny in Boston, U.K.!"}]
Tool response: [{'type': 'text', 'text': "It's always sunny in San Francisco!"}]
-| **|Boston|**|:| It|’s| always| sunny| in| Boston|,| U|.K|.|
|-| **|San| Francisco|**|:| It|’s| always| sunny| in| San| Francisco|!|
```

##### ​Streaming from sub-agents

When there are multiple LLMs at any point in an agent, it’s often necessary to disambiguate the source of messages as they are generated.

To do this, you can initialize any model with tags. These tags are then available in metadata when streaming in "messages" mode.

Below, we update the streaming tool calls example:

- We replace our tool with a call_weather_agent tool that invokes an agent internally
- We add a string tag to this LLM and the outer “supervisor” LLM
- We specify subgraphs=True when creating the stream
- Our stream processing is identical to before, but we add logic to keep track of what LLM is active
If streaming tokens from sub-agents is not needed, you can initialize the sub-agent with a name. This name is accessible on messages generated by the sub-agent when streaming updates.

First we construct the agent:

Copyfrom typing import Any

```python
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage, AnyMessage

def get_weather(city: str) -> str:
    """Get weather for a given city."""

    return f"It's always sunny in {city}!"

weather_model = init_chat_model(
    "openai:gpt-5.2",
    tags=["weather_sub_agent"],
)

weather_agent = create_agent(model=weather_model, tools=[get_weather])

def call_weather_agent(query: str) -> str:
    """Query the weather agent."""
    result = weather_agent.invoke({
        "messages": [{"role": "user", "content": query}]
    })
    return result["messages"][-1].text

supervisor_model = init_chat_model(
    "openai:gpt-5.2",
    tags=["supervisor"],
)

agent = create_agent(model=supervisor_model, tools=[call_weather_agent])

Next, we add logic to the streaming loop to report which agent is emitting tokens:

Copydef _render_message_chunk(token: AIMessageChunk) -> None:
    if token.text:
        print(token.text, end="|")
    if token.tool_call_chunks:
        print(token.tool_call_chunks)

def _render_completed_message(message: AnyMessage) -> None:
    if isinstance(message, AIMessage) and message.tool_calls:
        print(f"Tool calls: {message.tool_calls}")
    if isinstance(message, ToolMessage):
        print(f"Tool response: {message.content_blocks}")

input_message = {"role": "user", "content": "What is the weather in Boston?"}
current_agent = None
for _, stream_mode, data in agent.stream(
    {"messages": [input_message]},
    stream_mode=["messages", "updates"],
    subgraphs=True,
):
    if stream_mode == "messages":
        token, metadata = data
        if tags := metadata.get("tags", []):
            this_agent = tags[0]
            if this_agent != current_agent:
                print(f"🤖 {this_agent}: ")
                current_agent = this_agent
        if isinstance(token, AIMessage):
            _render_message_chunk(token)
    if stream_mode == "updates":
        for source, update in data.items():
            if source in ("model", "tools"):
                _render_completed_message(update["messages"][-1])

OutputCopy🤖 supervisor:
[{'name': 'call_weather_agent', 'args': '', 'id': 'call_asorzUf0mB6sb7MiKfgojp7I', 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '{"', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': 'query', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '":"', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': 'Boston', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': ' weather', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': ' right', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': ' now', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': ' and', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': " today's", 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': ' forecast', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '"}', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
Tool calls: [{'name': 'call_weather_agent', 'args': {'query': "Boston weather right now and today's forecast"}, 'id': 'call_asorzUf0mB6sb7MiKfgojp7I', 'type': 'tool_call'}]
🤖 weather_sub_agent:
[{'name': 'get_weather', 'args': '', 'id': 'call_LZ89lT8fW6w8vqck5pZeaDIx', 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '{"', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': 'city', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '":"', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': 'Boston', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '"}', 'id': None, 'index': 0, 'type': 'tool_call_chunk'}]
Tool calls: [{'name': 'get_weather', 'args': {'city': 'Boston'}, 'id': 'call_LZ89lT8fW6w8vqck5pZeaDIx', 'type': 'tool_call'}]
Tool response: [{'type': 'text', 'text': "It's always sunny in Boston!"}]
Boston| weather| right| now|:| **|Sunny|**|.

|Today|’s| forecast| for| Boston|:| **|Sunny| all| day|**|.|Tool response: [{'type': 'text', 'text': 'Boston weather right now: **Sunny**.\n\nToday’s forecast for Boston: **Sunny all day**.'}]
🤖 supervisor:
Boston| weather| right| now|:| **|Sunny|**|.

|Today|’s| forecast| for| Boston|:| **|Sunny| all| day|**|.|
See all 30 lines
```

#### ​Disable streaming

In some applications you might need to disable streaming of individual tokens for a given model. This is useful when:

- Working with multi-agent systems to control which agents stream their output
- Mixing models that support streaming with those that do not
- Deploying to LangSmith and wanting to prevent certain model outputs from being streamed to the client
Set streaming=False when initializing the model.

Copyfrom langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="gpt-4o",
    streaming=False
)

When deploying to LangSmith, set streaming=False on any models whose output you don’t want streamed to the client. This is configured in your graph code before deployment.

Not all chat model integrations support the streaming parameter. If your model doesn’t support it, use disable_streaming=True instead. This parameter is available on all chat models via the base class.

See the LangGraph streaming guide for more details.

#### ​Related

- Streaming with chat models — Stream tokens directly from a chat model without using an agent or graph
- Streaming with human-in-the-loop — Stream agent progress while handling interrupts for human review
- LangGraph streaming — Advanced streaming options including values, debug modes, and subgraph streaming
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Multi-agent - Docs by LangChain {#doc-2}

**Source:** [https://docs.langchain.com/oss/python/langchain/multi-agent/index](https://docs.langchain.com/oss/python/langchain/multi-agent/index)

### Multi-agent

Copy page

#### ​Why multi-agent?

When developers say they need “multi-agent,” they’re usually looking for one or more of these capabilities:

- Context management: Provide specialized knowledge without overwhelming the model’s context window. If context were infinite and latency zero, you could dump all knowledge into a single prompt — but since it’s not, you need patterns to selectively surface relevant information.
- Distributed development: Allow different teams to develop and maintain capabilities independently, composing them into a larger system with clear boundaries.
- Parallelization: Spawn specialized workers for subtasks and execute them concurrently for faster results.
Multi-agent patterns are particularly valuable when a single agent has too many tools and makes poor decisions about which to use, when tasks require specialized knowledge with extensive context (long prompts and domain-specific tools), or when you need to enforce sequential constraints that unlock capabilities only after certain conditions are met.

At the center of multi-agent design is context engineering—deciding what information each agent sees. The quality of your system depends on ensuring each agent has access to the right data for its task.

#### ​Patterns

Here are the main patterns for building multi-agent systems, each suited to different use cases:

PatternHow it worksSubagentsA main agent coordinates subagents as tools. All routing passes through the main agent, which decides when and how to invoke each subagent.HandoffsBehavior changes dynamically based on state. Tool calls update a state variable that triggers routing or configuration changes, switching agents or adjusting the current agent’s tools and prompt.SkillsSpecialized prompts and knowledge loaded on-demand. A single agent stays in control while loading context from skills as needed.RouterA routing step classifies input and directs it to one or more specialized agents. Results are synthesized into a combined response.Custom workflowBuild bespoke execution flows with LangGraph, mixing deterministic logic and agentic behavior. Embed other patterns as nodes in your workflow.

##### ​Choosing a pattern

Use this table to match your requirements to the right pattern:

PatternDistributed developmentParallelizationMulti-hopDirect user interactionSubagents⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐Handoffs——⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐Skills⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐Router⭐⭐⭐⭐⭐⭐⭐⭐—⭐⭐⭐

- Distributed development: Can different teams maintain components independently?
- Parallelization: Can multiple agents execute concurrently?
- Multi-hop: Does the pattern support calling multiple subagents in series?
- Direct user interaction: Can subagents converse directly with the user?
You can mix patterns! For example, a subagents architecture can invoke tools that invoke custom workflows or router agents. Subagents can even use the skills pattern to load context on-demand. The possibilities are endless!

##### ​Visual overview

Subagents Handoffs Skills RouterA main agent coordinates subagents as tools. All routing passes through the main agent.Agents transfer control to each other via tool calls. Each agent can hand off to others or respond directly to the user.A single agent loads specialized prompts and knowledge on-demand while staying in control.A routing step classifies input and directs it to specialized agents. Results are synthesized.

#### ​Performance comparison

Different patterns have different performance characteristics. Understanding these tradeoffs helps you choose the right pattern for your latency and cost requirements.

Key metrics:

- Model calls: Number of LLM invocations. More calls = higher latency (especially if sequential) and higher per-request API costs.
- Tokens processed: Total context window usage across all calls. More tokens = higher processing costs and potential context limits.

##### ​One-shot request

User: “Buy coffee”

A specialized coffee agent/skill can call a buy_coffee tool.

PatternModel callsBest fitSubagents4Handoffs3✅Skills3✅Router3✅

Subagents Handoffs Skills Router4 model calls:3 model calls:3 model calls:3 model calls:

Key insight: Handoffs, Skills, and Router are most efficient for single tasks (3 calls each). Subagents adds one extra call because results flow back through the main agent—this overhead provides centralized control.

##### ​Repeat request

Turn 1: “Buy coffee”
Turn 2: “Buy coffee again”

The user repeats the same request in the same conversation.

PatternTurn 2 callsTotal (both turns)Best fitSubagents48Handoffs25✅Skills25✅Router36

Subagents Handoffs Skills Router4 calls again → 8 total
Subagents are stateless by design—each invocation follows the same flow
The main agent maintains conversation context, but subagents start fresh each time
This provides strong context isolation but repeats the full flow
2 calls → 5 total
The coffee agent is still active from turn 1 (state persists)
No handoff needed—agent directly calls buy_coffee tool (call 1)
Agent responds to user (call 2)
Saves 1 call by skipping the handoff
2 calls → 5 total
The skill context is already loaded in conversation history
No need to reload—agent directly calls buy_coffee tool (call 1)
Agent responds to user (call 2)
Saves 1 call by reusing loaded skill
3 calls again → 6 total
Routers are stateless—each request requires an LLM routing call
Turn 2: Router LLM call (1) → Milk agent calls buy_coffee (2) → Milk agent responds (3)
Can be optimized by wrapping as a tool in a stateful agent

Key insight: Stateful patterns (Handoffs, Skills) save 40-50% of calls on repeat requests. Subagents maintain consistent cost per request—this stateless design provides strong context isolation but at the cost of repeated model calls.

##### ​Multi-domain

User: “Compare Python, JavaScript, and Rust for web development”

Each language agent/skill contains ~2000 tokens of documentation. All patterns can make parallel tool calls.

PatternModel callsTotal tokensBest fitSubagents5~9K✅Handoffs7+~14K+Skills3~15KRouter5~9K✅

Subagents Handoffs Skills Router5 calls, ~9K tokensEach subagent works in isolation with only its relevant context. Total: 9K tokens.7+ calls, ~14K+ tokensHandoffs executes sequentially—can’t research all three languages in parallel. Growing conversation history adds overhead. Total: ~14K+ tokens.3 calls, ~15K tokensAfter loading, every subsequent call processes all 6K tokens of skill documentation. Subagents processes 67% fewer tokens overall due to context isolation. Total: 15K tokens.5 calls, ~9K tokensRouter uses an LLM for routing, then invokes agents in parallel. Similar to Subagents but with explicit routing step. Total: 9K tokens.

Key insight: For multi-domain tasks, patterns with parallel execution (Subagents, Router) are most efficient. Skills has fewer calls but high token usage due to context accumulation. Handoffs is inefficient here—it must execute sequentially and can’t leverage parallel tool calling for consulting multiple domains simultaneously.

##### ​Summary

Here’s how patterns compare across all three scenarios:

PatternOne-shotRepeat requestMulti-domainSubagents4 calls8 calls (4+4)5 calls, 9K tokensHandoffs3 calls5 calls (3+2)7+ calls, 14K+ tokensSkills3 calls5 calls (3+2)3 calls, 15K tokensRouter3 calls6 calls (3+3)5 calls, 9K tokens

Choosing a pattern:

Optimize forSubagentsHandoffsSkillsRouterSingle requests✅✅✅Repeat requests✅✅Parallel execution✅✅Large-context domains✅✅Simple, focused tasks✅

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Router - Docs by LangChain {#doc-3}

**Source:** [https://docs.langchain.com/oss/python/langchain/multi-agent/router](https://docs.langchain.com/oss/python/langchain/multi-agent/router)

### Router

Copy page

#### ​Key characteristics

- Router decomposes the query
- Zero or more specialized agents are invoked in parallel
- Results are synthesized into a coherent response

#### ​When to use

Use the router pattern when you have distinct verticals (separate knowledge domains that each require their own agent), need to query multiple sources in parallel, and want to synthesize results into a combined response.

#### ​Basic implementation

The router classifies the query and directs it to the appropriate agent(s). Use Command for single-agent routing or Send for parallel fan-out to multiple agents.

Single agent Multiple agents (parallel)Use Command to route to a single specialized agent:Copyfrom langgraph.types import Command

```python
def classify_query(query: str) -> str:
    """Use LLM to classify query and determine the appropriate agent."""
    # Classification logic here
    ...

def route_query(state: State) -> Command:
    """Route to the appropriate agent based on query classification."""
    active_agent = classify_query(state["query"])

    # Route to the selected agent
    return Command(goto=active_agent)
Use Send to fan out to multiple specialized agents in parallel:Copyfrom typing import TypedDict
from langgraph.types import Send

class ClassificationResult(TypedDict):
    query: str
    agent: str

def classify_query(query: str) -> list[ClassificationResult]:
    """Use LLM to classify query and determine which agents to invoke."""
    # Classification logic here
    ...

def route_query(state: State):
    """Route to relevant agents based on query classification."""
    classifications = classify_query(state["query"])

    # Fan out to selected agents in parallel
    return [
        Send(c["agent"], {"query": c["query"]})
        for c in classifications
    ]

For a complete implementation, see the tutorial below.

Tutorial: Build a multi-source knowledge base with routingBuild a router that queries GitHub, Notion, and Slack in parallel, then synthesizes results into a coherent answer. Covers state definition, specialized agents, parallel execution with Send, and result synthesis.

​Stateless vs. stateful

Two approaches:

- Stateless routers address each request independently
- Stateful routers maintain conversation history across requests
​Stateless

Each request is routed independently—no memory between calls. For multi-turn conversations, see Stateful routers.

Router vs. Subagents: Both patterns can dispatch work to multiple agents, but they differ in how routing decisions are made:
Router: A dedicated routing step (often a single LLM call or rule-based logic) that classifies the input and dispatches to agents. The router itself typically doesn’t maintain conversation history or perform multi-turn orchestration—it’s a preprocessing step.
Subagents: An main supervisor agent dynamically decides which subagents to call as part of an ongoing conversation. The main agent maintains context, can call multiple subagents across turns, and orchestrates complex multi-step workflows.
Use a router when you have clear input categories and want deterministic or lightweight classification. Use a supervisor when you need flexible, conversation-aware orchestration where the LLM decides what to do next based on evolving context.

​Stateful

For multi-turn conversations, you need to maintain context across invocations.

​Tool wrapper

The simplest approach: wrap the stateless router as a tool that a conversational agent can call. The conversational agent handles memory and context; the router stays stateless. This avoids the complexity of managing conversation history across multiple parallel agents.

Copy@tool
def search_docs(query: str) -> str:
    """Search across multiple documentation sources."""
    result = workflow.invoke({"query": query})
    return result["final_answer"]

# Conversational agent uses the router as a tool
conversational_agent = create_agent(
    model,
    tools=[search_docs],
    prompt="You are a helpful assistant. Use search_docs to answer questions."
)

​Full persistence

If you need the router itself to maintain state, use persistence to store message history. When routing to an agent, fetch previous messages from state and selectively include them in the agent’s context—this is a lever for context engineering.

Stateful routers require custom history management. If the router switches between agents across turns, conversations may not feel fluid to end users when agents have different tones or prompts. With parallel invocation, you’ll need to maintain history at the router level (inputs and synthesized outputs) and leverage this history in routing logic. Consider the handoffs pattern or subagents pattern instead—both provide clearer semantics for multi-turn conversations.

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```

#### Tutorial: Build a multi-source knowledge base with routing

Build a router that queries GitHub, Notion, and Slack in parallel, then synthesizes results into a coherent answer. Covers state definition, specialized agents, parallel execution with Send, and result synthesis.

#### ​Stateless vs. stateful

Two approaches:

- Stateless routers address each request independently
- Stateful routers maintain conversation history across requests

#### ​Stateless

Each request is routed independently—no memory between calls. For multi-turn conversations, see Stateful routers.

Router vs. Subagents: Both patterns can dispatch work to multiple agents, but they differ in how routing decisions are made:
Router: A dedicated routing step (often a single LLM call or rule-based logic) that classifies the input and dispatches to agents. The router itself typically doesn’t maintain conversation history or perform multi-turn orchestration—it’s a preprocessing step.
Subagents: An main supervisor agent dynamically decides which subagents to call as part of an ongoing conversation. The main agent maintains context, can call multiple subagents across turns, and orchestrates complex multi-step workflows.
Use a router when you have clear input categories and want deterministic or lightweight classification. Use a supervisor when you need flexible, conversation-aware orchestration where the LLM decides what to do next based on evolving context.

#### ​Stateful

For multi-turn conversations, you need to maintain context across invocations.

##### ​Tool wrapper

The simplest approach: wrap the stateless router as a tool that a conversational agent can call. The conversational agent handles memory and context; the router stays stateless. This avoids the complexity of managing conversation history across multiple parallel agents.

Copy@tool
```python
def search_docs(query: str) -> str:
    """Search across multiple documentation sources."""
    result = workflow.invoke({"query": query})
    return result["final_answer"]

# Conversational agent uses the router as a tool
conversational_agent = create_agent(
    model,
    tools=[search_docs],
    prompt="You are a helpful assistant. Use search_docs to answer questions."
)
```

##### ​Full persistence

If you need the router itself to maintain state, use persistence to store message history. When routing to an agent, fetch previous messages from state and selectively include them in the agent’s context—this is a lever for context engineering.

Stateful routers require custom history management. If the router switches between agents across turns, conversations may not feel fluid to end users when agents have different tones or prompts. With parallel invocation, you’ll need to maintain history at the router level (inputs and synthesized outputs) and leverage this history in routing logic. Consider the handoffs pattern or subagents pattern instead—both provide clearer semantics for multi-turn conversations.

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Skills - Docs by LangChain {#doc-4}

**Source:** [https://docs.langchain.com/oss/python/langchain/multi-agent/skills](https://docs.langchain.com/oss/python/langchain/multi-agent/skills)

### Skills

Copy page

#### ​Key characteristics

- Prompt-driven specialization: Skills are primarily defined by specialized prompts
- Progressive disclosure: Skills become available based on context or user needs
- Team distribution: Different teams can develop and maintain skills independently
- Lightweight composition: Skills are simpler than full sub-agents

#### ​When to use

Use the skills pattern when you want a single agent with many possible specializations, you don’t need to enforce specific constraints between skills, or different teams need to develop capabilities independently. Common examples include coding assistants (skills for different languages or tasks), knowledge bases (skills for different domains), and creative assistants (skills for different formats).

#### ​Basic implementation

Copyfrom langchain.tools import tool
```python
from langchain.agents import create_agent

@tool
def load_skill(skill_name: str) -> str:
    """Load a specialized skill prompt.

    Available skills:
    - write_sql: SQL query writing expert
    - review_legal_doc: Legal document reviewer

    Returns the skill's prompt and context.
    """
    # Load skill content from file/database
    ...

agent = create_agent(
    model="gpt-4o",
    tools=[load_skill],
    system_prompt=(
        "You are a helpful assistant. "
        "You have access to two skills: "
        "write_sql and review_legal_doc. "
        "Use load_skill to access them."
    ),
)

For a complete implementation, see the tutorial below.

Tutorial: Build a SQL assistant with on-demand skillsLearn how to implement skills with progressive disclosure, where the agent loads specialized prompts and schemas on-demand rather than upfront.Learn more

​Extending the pattern

When writing custom implementations, you can extend the basic skills pattern in several ways:

- Dynamic tool registration: Combine progressive disclosure with state management to register new tools as skills load. For example, loading a “database_admin” skill could both add specialized context and register database-specific tools (backup, restore, migrate). This uses the same tool-and-state mechanisms used across multi-agent patterns—tools updating state to dynamically change agent capabilities.
- Hierarchical skills: Skills can define other skills in a tree structure, creating nested specializations. For instance, loading a “data_science” skill might make available sub-skills like “pandas_expert”, “visualization”, and “statistical_analysis”. Each sub-skill can be loaded independently as needed, allowing for fine-grained progressive disclosure of domain knowledge. This hierarchical approach helps manage large knowledge bases by organizing capabilities into logical groupings that can be discovered and loaded on-demand.
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```

#### Tutorial: Build a SQL assistant with on-demand skills

Learn how to implement skills with progressive disclosure, where the agent loads specialized prompts and schemas on-demand rather than upfront.

Learn more

#### ​Extending the pattern

When writing custom implementations, you can extend the basic skills pattern in several ways:

- Dynamic tool registration: Combine progressive disclosure with state management to register new tools as skills load. For example, loading a “database_admin” skill could both add specialized context and register database-specific tools (backup, restore, migrate). This uses the same tool-and-state mechanisms used across multi-agent patterns—tools updating state to dynamically change agent capabilities.
- Hierarchical skills: Skills can define other skills in a tree structure, creating nested specializations. For instance, loading a “data_science” skill might make available sub-skills like “pandas_expert”, “visualization”, and “statistical_analysis”. Each sub-skill can be loaded independently as needed, allowing for fine-grained progressive disclosure of domain knowledge. This hierarchical approach helps manage large knowledge bases by organizing capabilities into logical groupings that can be discovered and loaded on-demand.
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Handoffs - Docs by LangChain {#doc-5}

**Source:** [https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs)

### Handoffs

Copy page

#### ​Key characteristics

- State-driven behavior: Behavior changes based on a state variable (e.g., current_step or active_agent)
- Tool-based transitions: Tools update the state variable to move between states
- Direct user interaction: Each state’s configuration handles user messages directly
- Persistent state: State survives across conversation turns

#### ​When to use

Use the handoffs pattern when you need to enforce sequential constraints (unlock capabilities only after preconditions are met), the agent needs to converse directly with the user across different states, or you’re building multi-stage conversational flows. This pattern is particularly valuable for customer support scenarios where you need to collect information in a specific sequence — for example, collecting a warranty ID before processing a refund.

#### ​Basic implementation

The core mechanism is a tool that returns a Command to update state, triggering a transition to a new step or agent:

Copyfrom langchain.tools import tool
```python
from langchain.messages import ToolMessage
from langgraph.types import Command

@tool
def transfer_to_specialist(runtime) -> Command:
    """Transfer to the specialist agent."""
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content="Transferred to specialist",
                    tool_call_id=runtime.tool_call_id
                )
            ],
            "current_step": "specialist"  # Triggers behavior change
        }
    )

Why include a ToolMessage? When an LLM calls a tool, it expects a response. The ToolMessage with matching tool_call_id completes this request-response cycle—without it, the conversation history becomes malformed. This is required whenever your handoff tool updates messages.

For a complete implementation, see the tutorial below.

Tutorial: Build customer support with handoffsLearn how to build a customer support agent using the handoffs pattern, where a single agent transitions between different configurations.Learn more

​Implementation approaches

There are two ways to implement handoffs: single agent with middleware (one agent with dynamic configuration) or multiple agent subgraphs (distinct agents as graph nodes).

​Single agent with middleware

A single agent changes its behavior based on state. Middleware intercepts each model call and dynamically adjusts the system prompt and available tools. Tools update the state variable to trigger transitions:

Copyfrom langchain.tools import ToolRuntime, tool
from langchain.messages import ToolMessage
from langgraph.types import Command

@tool
def record_warranty_status(
    status: str,
    runtime: ToolRuntime[None, SupportState]
) -> Command:
    """Record warranty status and transition to next step."""
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"Warranty status recorded: {status}",
                    tool_call_id=runtime.tool_call_id
                )
            ],
            "warranty_status": status,
            "current_step": "specialist"  # Update state to trigger transition
        }
    )

Complete example: Customer support with middlewareCopyfrom langchain.agents import AgentState, create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.tools import tool, ToolRuntime
from langchain.messages import ToolMessage
from langgraph.types import Command
from typing import Callable

# 1. Define state with current_step tracker
class SupportState(AgentState):
    """Track which step is currently active."""
    current_step: str = "triage"
    warranty_status: str | None = None

# 2. Tools update current_step via Command
@tool
def record_warranty_status(
    status: str,
    runtime: ToolRuntime[None, SupportState]
) -> Command:
    """Record warranty status and transition to next step."""
    return Command(update={
        "messages": [
            ToolMessage(
                content=f"Warranty status recorded: {status}",
                tool_call_id=runtime.tool_call_id
            )
        ],
        "warranty_status": status,
        # Transition to next step
        "current_step": "specialist"
    })

# 3. Middleware applies dynamic configuration based on current_step
@wrap_model_call
def apply_step_config(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Configure agent behavior based on current_step."""
    step = request.state.get("current_step", "triage")

    # Map steps to their configurations
    configs = {
        "triage": {
            "prompt": "Collect warranty information...",
            "tools": [record_warranty_status]
        },
        "specialist": {
            "prompt": "Provide solutions based on warranty: {warranty_status}",
            "tools": [provide_solution, escalate]
        }
    }

    config = configs[step]
    request = request.override(
        system_prompt=config["prompt"].format(**request.state),
        tools=config["tools"]
    )
    return handler(request)

# 4. Create agent with middleware
agent = create_agent(
    model,
    tools=[record_warranty_status, provide_solution, escalate],
    state_schema=SupportState,
    middleware=[apply_step_config],
    checkpointer=InMemorySaver()  # Persist state across turns  #
)

​Multiple agent subgraphs

Multiple distinct agents exist as separate nodes in a graph. Handoff tools navigate between agent nodes using Command.PARENT to specify which node to execute next.

Subgraph handoffs require careful context engineering. Unlike single-agent middleware (where message history flows naturally), you must explicitly decide what messages pass between agents. Get this wrong and agents receive malformed conversation history or bloated context. See Context engineering below.

Copyfrom langchain.messages import AIMessage, ToolMessage
from langchain.tools import tool, ToolRuntime
from langgraph.types import Command

@tool
def transfer_to_sales(
    runtime: ToolRuntime,
) -> Command:
    """Transfer to the sales agent."""
    last_ai_message = next(
        msg for msg in reversed(runtime.state["messages"]) if isinstance(msg, AIMessage)
    )
    transfer_message = ToolMessage(
        content="Transferred to sales agent",
        tool_call_id=runtime.tool_call_id,
    )
    return Command(
        goto="sales_agent",
        update={
            "active_agent": "sales_agent",
            "messages": [last_ai_message, transfer_message],
        },
        graph=Command.PARENT
    )

Complete example: Sales and support with handoffsThis example shows a multi-agent system with separate sales and support agents. Each agent is a separate graph node, and handoff tools allow agents to transfer conversations to each other.Copyfrom typing import Literal

from langchain.agents import AgentState, create_agent
from langchain.messages import AIMessage, ToolMessage
from langchain.tools import tool, ToolRuntime
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from typing_extensions import NotRequired

# 1. Define state with active_agent tracker
class MultiAgentState(AgentState):
    active_agent: NotRequired[str]

# 2. Create handoff tools
@tool
def transfer_to_sales(
    runtime: ToolRuntime,
) -> Command:
    """Transfer to the sales agent."""
    last_ai_message = next(
        msg for msg in reversed(runtime.state["messages"]) if isinstance(msg, AIMessage)
    )
    transfer_message = ToolMessage(
        content="Transferred to sales agent from support agent",
        tool_call_id=runtime.tool_call_id,
    )
    return Command(
        goto="sales_agent",
        update={
            "active_agent": "sales_agent",
            "messages": [last_ai_message, transfer_message],
        },
        graph=Command.PARENT,
    )

@tool
def transfer_to_support(
    runtime: ToolRuntime,
) -> Command:
    """Transfer to the support agent."""
    last_ai_message = next(
        msg for msg in reversed(runtime.state["messages"]) if isinstance(msg, AIMessage)
    )
    transfer_message = ToolMessage(
        content="Transferred to support agent from sales agent",
        tool_call_id=runtime.tool_call_id,
    )
    return Command(
        goto="support_agent",
        update={
            "active_agent": "support_agent",
            "messages": [last_ai_message, transfer_message],
        },
        graph=Command.PARENT,
    )

# 3. Create agents with handoff tools
sales_agent = create_agent(
    model="anthropic:claude-sonnet-4-20250514",
    tools=[transfer_to_support],
    system_prompt="You are a sales agent. Help with sales inquiries. If asked about technical issues or support, transfer to the support agent.",
)

support_agent = create_agent(
    model="anthropic:claude-sonnet-4-20250514",
    tools=[transfer_to_sales],
    system_prompt="You are a support agent. Help with technical issues. If asked about pricing or purchasing, transfer to the sales agent.",
)

# 4. Create agent nodes that invoke the agents
def call_sales_agent(state: MultiAgentState) -> Command:
    """Node that calls the sales agent."""
    response = sales_agent.invoke(state)
    return response

def call_support_agent(state: MultiAgentState) -> Command:
    """Node that calls the support agent."""
    response = support_agent.invoke(state)
    return response

# 5. Create router that checks if we should end or continue
def route_after_agent(
    state: MultiAgentState,
) -> Literal["sales_agent", "support_agent", "__end__"]:
    """Route based on active_agent, or END if the agent finished without handoff."""
    messages = state.get("messages", [])

    # Check the last message - if it's an AIMessage without tool calls, we're done
    if messages:
        last_msg = messages[-1]
        if isinstance(last_msg, AIMessage) and not last_msg.tool_calls:
            return "__end__"

    # Otherwise route to the active agent
    active = state.get("active_agent", "sales_agent")
    return active if active else "sales_agent"

def route_initial(
    state: MultiAgentState,
) -> Literal["sales_agent", "support_agent"]:
    """Route to the active agent based on state, default to sales agent."""
    return state.get("active_agent") or "sales_agent"

# 6. Build the graph
builder = StateGraph(MultiAgentState)
builder.add_node("sales_agent", call_sales_agent)
builder.add_node("support_agent", call_support_agent)

# Start with conditional routing based on initial active_agent
builder.add_conditional_edges(START, route_initial, ["sales_agent", "support_agent"])

# After each agent, check if we should end or route to another agent
builder.add_conditional_edges(
    "sales_agent", route_after_agent, ["sales_agent", "support_agent", END]
)
builder.add_conditional_edges(
    "support_agent", route_after_agent, ["sales_agent", "support_agent", END]
)

graph = builder.compile()
result = graph.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Hi, I'm having trouble with my account login. Can you help?",
            }
        ]
    }
)

for msg in result["messages"]:
    msg.pretty_print()

Use single agent with middleware for most handoffs use cases—it’s simpler. Only use multiple agent subgraphs when you need bespoke agent implementations (e.g., a node that’s itself a complex graph with reflection or retrieval steps).

​Context engineering

With subgraph handoffs, you control exactly what messages flow between agents. This precision is essential for maintaining valid conversation history and avoiding context bloat that could confuse downstream agents. For more on this topic, see context engineering.

Handling context during handoffs

When handing off between agents, you need to ensure the conversation history remains valid. LLMs expect tool calls to be paired with their responses, so when using Command.PARENT to hand off to another agent, you must include both:

- The AIMessage containing the tool call (the message that triggered the handoff)
- A ToolMessage acknowledging the handoff (the artificial response to that tool call)
Without this pairing, the receiving agent will see an incomplete conversation and may produce errors or unexpected behavior.

The example below assumes only the handoff tool was called (no parallel tool calls):

Copy@tool
def transfer_to_sales(runtime: ToolRuntime) -> Command:
    # Get the AI message that triggered this handoff
    last_ai_message = runtime.state["messages"][-1]

    # Create an artificial tool response to complete the pair
    transfer_message = ToolMessage(
        content="Transferred to sales agent",
        tool_call_id=runtime.tool_call_id,
    )

    return Command(
        goto="sales_agent",
        update={
            "active_agent": "sales_agent",
            # Pass only these two messages, not the full subagent history
            "messages": [last_ai_message, transfer_message],
        },
        graph=Command.PARENT,
    )

Why not pass all subagent messages? While you could include the full subagent conversation in the handoff, this often creates problems. The receiving agent may become confused by irrelevant internal reasoning, and token costs increase unnecessarily. By passing only the handoff pair, you keep the parent graph’s context focused on high-level coordination. If the receiving agent needs additional context, consider summarizing the subagent’s work in the ToolMessage content instead of passing raw message history.

Returning control to the user

When returning control to the user (ending the agent’s turn), ensure the final message is an AIMessage. This maintains valid conversation history and signals to the user interface that the agent has finished its work.

​Implementation Considerations

As you design your multi-agent system, consider:

- Context filtering strategy: Will each agent receive full conversation history, filtered portions, or summaries? Different agents may need different context depending on their role.
- Tool semantics: Clarify whether handoff tools only update routing state or also perform side effects. For example, should transfer_to_sales() also create a support ticket, or should that be a separate action?
- Token efficiency: Balance context completeness against token costs. Summarization and selective context passing become more important as conversations grow longer.
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```

#### Tutorial: Build customer support with handoffs

Learn how to build a customer support agent using the handoffs pattern, where a single agent transitions between different configurations.

Learn more

#### ​Implementation approaches

There are two ways to implement handoffs: single agent with middleware (one agent with dynamic configuration) or multiple agent subgraphs (distinct agents as graph nodes).

##### ​Single agent with middleware

A single agent changes its behavior based on state. Middleware intercepts each model call and dynamically adjusts the system prompt and available tools. Tools update the state variable to trigger transitions:

Copyfrom langchain.tools import ToolRuntime, tool
```python
from langchain.messages import ToolMessage
from langgraph.types import Command

@tool
def record_warranty_status(
    status: str,
    runtime: ToolRuntime[None, SupportState]
) -> Command:
    """Record warranty status and transition to next step."""
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"Warranty status recorded: {status}",
                    tool_call_id=runtime.tool_call_id
                )
            ],
            "warranty_status": status,
            "current_step": "specialist"  # Update state to trigger transition
        }
    )

Complete example: Customer support with middlewareCopyfrom langchain.agents import AgentState, create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.tools import tool, ToolRuntime
from langchain.messages import ToolMessage
from langgraph.types import Command
from typing import Callable

# 1. Define state with current_step tracker
class SupportState(AgentState):
    """Track which step is currently active."""
    current_step: str = "triage"
    warranty_status: str | None = None

# 2. Tools update current_step via Command
@tool
def record_warranty_status(
    status: str,
    runtime: ToolRuntime[None, SupportState]
) -> Command:
    """Record warranty status and transition to next step."""
    return Command(update={
        "messages": [
            ToolMessage(
                content=f"Warranty status recorded: {status}",
                tool_call_id=runtime.tool_call_id
            )
        ],
        "warranty_status": status,
        # Transition to next step
        "current_step": "specialist"
    })

# 3. Middleware applies dynamic configuration based on current_step
@wrap_model_call
def apply_step_config(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Configure agent behavior based on current_step."""
    step = request.state.get("current_step", "triage")

    # Map steps to their configurations
    configs = {
        "triage": {
            "prompt": "Collect warranty information...",
            "tools": [record_warranty_status]
        },
        "specialist": {
            "prompt": "Provide solutions based on warranty: {warranty_status}",
            "tools": [provide_solution, escalate]
        }
    }

    config = configs[step]
    request = request.override(
        system_prompt=config["prompt"].format(**request.state),
        tools=config["tools"]
    )
    return handler(request)

# 4. Create agent with middleware
agent = create_agent(
    model,
    tools=[record_warranty_status, provide_solution, escalate],
    state_schema=SupportState,
    middleware=[apply_step_config],
    checkpointer=InMemorySaver()  # Persist state across turns  #
)
```

##### ​Multiple agent subgraphs

Multiple distinct agents exist as separate nodes in a graph. Handoff tools navigate between agent nodes using Command.PARENT to specify which node to execute next.

Subgraph handoffs require careful context engineering. Unlike single-agent middleware (where message history flows naturally), you must explicitly decide what messages pass between agents. Get this wrong and agents receive malformed conversation history or bloated context. See Context engineering below.

Copyfrom langchain.messages import AIMessage, ToolMessage
```python
from langchain.tools import tool, ToolRuntime
from langgraph.types import Command

@tool
def transfer_to_sales(
    runtime: ToolRuntime,
) -> Command:
    """Transfer to the sales agent."""
    last_ai_message = next(
        msg for msg in reversed(runtime.state["messages"]) if isinstance(msg, AIMessage)
    )
    transfer_message = ToolMessage(
        content="Transferred to sales agent",
        tool_call_id=runtime.tool_call_id,
    )
    return Command(
        goto="sales_agent",
        update={
            "active_agent": "sales_agent",
            "messages": [last_ai_message, transfer_message],
        },
        graph=Command.PARENT
    )

Complete example: Sales and support with handoffsThis example shows a multi-agent system with separate sales and support agents. Each agent is a separate graph node, and handoff tools allow agents to transfer conversations to each other.Copyfrom typing import Literal

from langchain.agents import AgentState, create_agent
from langchain.messages import AIMessage, ToolMessage
from langchain.tools import tool, ToolRuntime
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from typing_extensions import NotRequired

# 1. Define state with active_agent tracker
class MultiAgentState(AgentState):
    active_agent: NotRequired[str]

# 2. Create handoff tools
@tool
def transfer_to_sales(
    runtime: ToolRuntime,
) -> Command:
    """Transfer to the sales agent."""
    last_ai_message = next(
        msg for msg in reversed(runtime.state["messages"]) if isinstance(msg, AIMessage)
    )
    transfer_message = ToolMessage(
        content="Transferred to sales agent from support agent",
        tool_call_id=runtime.tool_call_id,
    )
    return Command(
        goto="sales_agent",
        update={
            "active_agent": "sales_agent",
            "messages": [last_ai_message, transfer_message],
        },
        graph=Command.PARENT,
    )

@tool
def transfer_to_support(
    runtime: ToolRuntime,
) -> Command:
    """Transfer to the support agent."""
    last_ai_message = next(
        msg for msg in reversed(runtime.state["messages"]) if isinstance(msg, AIMessage)
    )
    transfer_message = ToolMessage(
        content="Transferred to support agent from sales agent",
        tool_call_id=runtime.tool_call_id,
    )
    return Command(
        goto="support_agent",
        update={
            "active_agent": "support_agent",
            "messages": [last_ai_message, transfer_message],
        },
        graph=Command.PARENT,
    )

# 3. Create agents with handoff tools
sales_agent = create_agent(
    model="anthropic:claude-sonnet-4-20250514",
    tools=[transfer_to_support],
    system_prompt="You are a sales agent. Help with sales inquiries. If asked about technical issues or support, transfer to the support agent.",
)

support_agent = create_agent(
    model="anthropic:claude-sonnet-4-20250514",
    tools=[transfer_to_sales],
    system_prompt="You are a support agent. Help with technical issues. If asked about pricing or purchasing, transfer to the sales agent.",
)

# 4. Create agent nodes that invoke the agents
def call_sales_agent(state: MultiAgentState) -> Command:
    """Node that calls the sales agent."""
    response = sales_agent.invoke(state)
    return response

def call_support_agent(state: MultiAgentState) -> Command:
    """Node that calls the support agent."""
    response = support_agent.invoke(state)
    return response

# 5. Create router that checks if we should end or continue
def route_after_agent(
    state: MultiAgentState,
) -> Literal["sales_agent", "support_agent", "__end__"]:
    """Route based on active_agent, or END if the agent finished without handoff."""
    messages = state.get("messages", [])

    # Check the last message - if it's an AIMessage without tool calls, we're done
    if messages:
        last_msg = messages[-1]
        if isinstance(last_msg, AIMessage) and not last_msg.tool_calls:
            return "__end__"

    # Otherwise route to the active agent
    active = state.get("active_agent", "sales_agent")
    return active if active else "sales_agent"

def route_initial(
    state: MultiAgentState,
) -> Literal["sales_agent", "support_agent"]:
    """Route to the active agent based on state, default to sales agent."""
    return state.get("active_agent") or "sales_agent"

# 6. Build the graph
builder = StateGraph(MultiAgentState)
builder.add_node("sales_agent", call_sales_agent)
builder.add_node("support_agent", call_support_agent)

# Start with conditional routing based on initial active_agent
builder.add_conditional_edges(START, route_initial, ["sales_agent", "support_agent"])

# After each agent, check if we should end or route to another agent
builder.add_conditional_edges(
    "sales_agent", route_after_agent, ["sales_agent", "support_agent", END]
)
builder.add_conditional_edges(
    "support_agent", route_after_agent, ["sales_agent", "support_agent", END]
)

graph = builder.compile()
result = graph.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Hi, I'm having trouble with my account login. Can you help?",
            }
        ]
    }
)

for msg in result["messages"]:
    msg.pretty_print()

Use single agent with middleware for most handoffs use cases—it’s simpler. Only use multiple agent subgraphs when you need bespoke agent implementations (e.g., a node that’s itself a complex graph with reflection or retrieval steps).
```

###### ​Context engineering

With subgraph handoffs, you control exactly what messages flow between agents. This precision is essential for maintaining valid conversation history and avoiding context bloat that could confuse downstream agents. For more on this topic, see context engineering.

Handling context during handoffs

When handing off between agents, you need to ensure the conversation history remains valid. LLMs expect tool calls to be paired with their responses, so when using Command.PARENT to hand off to another agent, you must include both:

- The AIMessage containing the tool call (the message that triggered the handoff)
- A ToolMessage acknowledging the handoff (the artificial response to that tool call)
Without this pairing, the receiving agent will see an incomplete conversation and may produce errors or unexpected behavior.

The example below assumes only the handoff tool was called (no parallel tool calls):

Copy@tool
```python
def transfer_to_sales(runtime: ToolRuntime) -> Command:
    # Get the AI message that triggered this handoff
    last_ai_message = runtime.state["messages"][-1]

    # Create an artificial tool response to complete the pair
    transfer_message = ToolMessage(
        content="Transferred to sales agent",
        tool_call_id=runtime.tool_call_id,
    )

    return Command(
        goto="sales_agent",
        update={
            "active_agent": "sales_agent",
            # Pass only these two messages, not the full subagent history
            "messages": [last_ai_message, transfer_message],
        },
        graph=Command.PARENT,
    )

Why not pass all subagent messages? While you could include the full subagent conversation in the handoff, this often creates problems. The receiving agent may become confused by irrelevant internal reasoning, and token costs increase unnecessarily. By passing only the handoff pair, you keep the parent graph’s context focused on high-level coordination. If the receiving agent needs additional context, consider summarizing the subagent’s work in the ToolMessage content instead of passing raw message history.

Returning control to the user

When returning control to the user (ending the agent’s turn), ensure the final message is an AIMessage. This maintains valid conversation history and signals to the user interface that the agent has finished its work.
```

#### ​Implementation Considerations

As you design your multi-agent system, consider:

- Context filtering strategy: Will each agent receive full conversation history, filtered portions, or summaries? Different agents may need different context depending on their role.
- Tool semantics: Clarify whether handoff tools only update routing state or also perform side effects. For example, should transfer_to_sales() also create a support ticket, or should that be a separate action?
- Token efficiency: Balance context completeness against token costs. Summarization and selective context passing become more important as conversations grow longer.
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Subagents - Docs by LangChain {#doc-6}

**Source:** [https://docs.langchain.com/oss/python/langchain/multi-agent/subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)

### Subagents

Copy page

#### ​Key characteristics

- Centralized control: All routing passes through the main agent
- No direct user interaction: Subagents return results to the main agent, not the user (though you can use interrupts within a subagent to allow user interaction)
- Subagents via tools: Subagents are invoked via tools
- Parallel execution: The main agent can invoke multiple subagents in a single turn
Supervisor vs. Router: A supervisor agent (this pattern) is different from a router. The supervisor is a full agent that maintains conversation context and dynamically decides which subagents to call across multiple turns. A router is typically a single classification step that dispatches to agents without maintaining ongoing conversation state.

#### ​When to use

Use the subagents pattern when you have multiple distinct domains (e.g., calendar, email, CRM, database), subagents don’t need to converse directly with users, or you want centralized workflow control. For simpler cases with just a few tools, use a single agent.

Need user interaction within a subagent? While subagents typically return results to the main agent rather than conversing directly with users, you can use interrupts within a subagent to pause execution and gather user input. This is useful when a subagent needs clarification or approval before proceeding. The main agent remains the orchestrator, but the subagent can collect information from the user mid-task.

#### ​Basic implementation

The core mechanism wraps a subagent as a tool that the main agent can call:

Copyfrom langchain.tools import tool
```python
from langchain.agents import create_agent

# Create a subagent
subagent = create_agent(model="anthropic:claude-sonnet-4-20250514", tools=[...])

# Wrap it as a tool
@tool("research", description="Research a topic and return findings")
def call_research_agent(query: str):
    result = subagent.invoke({"messages": [{"role": "user", "content": query}]})
    return result["messages"][-1].content

# Main agent with subagent as a tool
main_agent = create_agent(model="anthropic:claude-sonnet-4-20250514", tools=[call_research_agent])

Tutorial: Build a personal assistant with subagentsLearn how to build a personal assistant using the subagents pattern, where a central main agent (supervisor) coordinates specialized worker agents.Learn more

​Design decisions

When implementing the subagents pattern, you’ll make several key design choices. This table summarizes the options—each is covered in detail in the sections below.

DecisionOptionsSync vs. asyncSync (blocking) vs. async (background)Tool patternsTool per agent vs. single dispatch toolSubagent inputsQuery only vs. full contextSubagent outputsSubagent result vs full conversation history

​Sync vs. async

Subagent execution can be synchronous (blocking) or asynchronous (background). Your choice depends on whether the main agent needs the result to continue.

ModeMain agent behaviorBest forTradeoffSyncWaits for subagent to completeMain agent needs result to continueSimple, but blocks the conversationAsyncContinues while subagent runs in backgroundIndependent tasks, user shouldn’t waitResponsive, but more complex

Not to be confused with Python’s async/await. Here, “async” means the main agent kicks off a background job (typically in a separate process or service) and continues without blocking.

​Synchronous (default)

By default, subagent calls are synchronous—the main agent waits for each subagent to complete before continuing. Use sync when the main agent’s next action depends on the subagent’s result.

When to use sync:

- Main agent needs the subagent’s result to formulate its response
- Tasks have order dependencies (e.g., fetch data → analyze → respond)
- Subagent failures should block the main agent’s response
Tradeoffs:

- Simple implementation—just call and wait
- User sees no response until all subagents complete
- Long-running tasks freeze the conversation
​Asynchronous

Use asynchronous execution when the subagent’s work is independent—the main agent doesn’t need the result to continue conversing with the user. The main agent kicks off a background job and remains responsive.

When to use async:

- Subagent work is independent of the main conversation flow
- Users should be able to continue chatting while work happens
- You want to run multiple independent tasks in parallel
Three-tool pattern:

- Start job: Kicks off the background task, returns a job ID
- Check status: Returns current state (pending, running, completed, failed)
- Get result: Retrieves the completed result
Handling job completion: When a job finishes, your application needs to notify the user. One approach: surface a notification that, when clicked, sends a HumanMessage like “Check job_123 and summarize the results.”

​Tool patterns

There are two main ways to expose subagents as tools:

PatternBest forTrade-offTool per agentFine-grained control over each subagent’s input/outputMore setup, but more customizationSingle dispatch toolMany agents, distributed teams, convention over configurationSimpler composition, less per-agent customization

​Tool per agent

The key idea is wrapping subagents as tools that the main agent can call:

Copyfrom langchain.tools import tool
from langchain.agents import create_agent

# Create a sub-agent
subagent = create_agent(model="...", tools=[...])

# Wrap it as a tool  #
@tool("subagent_name", description="subagent_description")
def call_subagent(query: str):
    result = subagent.invoke({"messages": [{"role": "user", "content": query}]})
    return result["messages"][-1].content

# Main agent with subagent as a tool  #
main_agent = create_agent(model="...", tools=[call_subagent])

The main agent invokes the subagent tool when it decides the task matches the subagent’s description, receives the result, and continues orchestration. See Context engineering for fine-grained control.

​Single dispatch tool

An alternative approach uses a single parameterized tool to invoke ephemeral sub-agents for independent tasks. Unlike the tool per agent approach where each sub-agent is wrapped as a separate tool, this uses a convention-based approach with a single task tool: the task description is passed as a human message to the sub-agent, and the sub-agent’s final message is returned as the tool result.

Use this approach when you want to distribute agent development across multiple teams, need to isolate complex tasks into separate context windows, need a scalable way to add new agents without modifying the coordinator, or prefer convention over customization. This approach trades flexibility in context engineering for simplicity in agent composition and strong context isolation.

Key characteristics:

- Single task tool: One parameterized tool that can invoke any registered sub-agent by name
- Convention-based invocation: Agent selected by name, task passed as human message, final message returned as tool result
- Team distribution: Different teams can develop and deploy agents independently
- Agent discovery: Sub-agents can be discovered via system prompt (listing available agents) or through progressive disclosure (loading agent information on-demand via tools)
An interesting aspect of this approach is that sub-agents may have the exact same capabilities as the main agent. In such cases, invoking a sub-agent is really about context isolation as the primary reason—allowing complex, multi-step tasks to run in isolated context windows without bloating the main agent’s conversation history. The sub-agent completes its work autonomously and returns only a concise summary, keeping the main thread focused and efficient.

Agent registry with task dispatcherCopyfrom langchain.tools import tool
from langchain.agents import create_agent

# Sub-agents developed by different teams
research_agent = create_agent(
    model="gpt-4o",
    prompt="You are a research specialist..."
)

writer_agent = create_agent(
    model="gpt-4o",
    prompt="You are a writing specialist..."
)

# Registry of available sub-agents
SUBAGENTS = {
    "research": research_agent,
    "writer": writer_agent,
}

@tool
def task(
    agent_name: str,
    description: str
) -> str:
    """Launch an ephemeral subagent for a task.

    Available agents:
    - research: Research and fact-finding
    - writer: Content creation and editing
    """
    agent = SUBAGENTS[agent_name]
    result = agent.invoke({
        "messages": [
            {"role": "user", "content": description}
        ]
    })
    return result["messages"][-1].content

# Main coordinator agent
main_agent = create_agent(
    model="gpt-4o",
    tools=[task],
    system_prompt=(
        "You coordinate specialized sub-agents. "
        "Available: research (fact-finding), "
        "writer (content creation). "
        "Use the task tool to delegate work."
    ),
)

​Context engineering

Control how context flows between the main agent and its subagents:

CategoryPurposeImpactsSubagent specsEnsure subagents are invoked when they should beMain agent routing decisionsSubagent inputsEnsure subagents can execute well with optimized contextSubagent performanceSubagent outputsEnsure the supervisor can act on subagent resultsMain agent performance

See also our comprehensive guide on context engineering for agents.

​Subagent specs

The names and descriptions associated with subagents are the primary way the main agent knows which subagents to invoke.
These are prompting levers—choose them carefully.

- Name: How the main agent refers to the sub-agent. Keep it clear and action-oriented (e.g., research_agent, code_reviewer).
- Description: What the main agent knows about the sub-agent’s capabilities. Be specific about what tasks it handles and when to use it.
For the single dispatch tool design, the main agent needs to call the task tool with the name of the subagent to invoke. The available tools can be provided to the main agent via one of the following methods:

- System prompt enumeration: List available agents in the system prompt.
- Enum constraint on dispatch tool: For small agent lists, add an enum to the agent_name field.
- Tool-based discovery: For large or dynamic agent registries, provide a separate tool (e.g., list_agents or search_agents) that returns available agents.
​Subagent inputs

Customize what context the subagent receives to execute its task. Add input that isn’t practical to capture in a static prompt—full message history, prior results, or task metadata—by pulling from the agent’s state.

Subagent inputs exampleCopyfrom langchain.agents import AgentState
from langchain.tools import tool, ToolRuntime

class CustomState(AgentState):
    example_state_key: str

@tool(
    "subagent1_name",
    description="subagent1_description"
)
def call_subagent1(query: str, runtime: ToolRuntime[None, CustomState]):
    # Apply any logic needed to transform the messages into a suitable input
    subagent_input = some_logic(query, runtime.state["messages"])
    result = subagent1.invoke({
        "messages": subagent_input,
        # You could also pass other state keys here as needed.
        # Make sure to define these in both the main and subagent's
        # state schemas.
        "example_state_key": runtime.state["example_state_key"]
    })
    return result["messages"][-1].content
See all 21 lines

​Subagent outputs

Customize what the main agent receives back so it can make good decisions. Two strategies:

- Prompt the sub-agent: Specify exactly what should be returned. A common failure mode is that the sub-agent performs tool calls or reasoning but doesn’t include results in its final message—remind it that the supervisor only sees the final output.
- Format in code: Adjust or enrich the response before returning it. For example, pass specific state keys back in addition to the final text using a Command.
Subagent outputs exampleCopyfrom typing import Annotated
from langchain.agents import AgentState
from langchain.tools import InjectedToolCallId
from langgraph.types import Command

@tool(
    "subagent1_name",
    description="subagent1_description"
)
def call_subagent1(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    result = subagent1.invoke({
        "messages": [{"role": "user", "content": query}]
    })
    return Command(update={
        # Pass back additional state from the subagent
        "example_state_key": result["example_state_key"],
        "messages": [
            ToolMessage(
                content=result["messages"][-1].content,
                tool_call_id=tool_call_id
            )
        ]
    })
See all 27 lines

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```

#### Tutorial: Build a personal assistant with subagents

Learn how to build a personal assistant using the subagents pattern, where a central main agent (supervisor) coordinates specialized worker agents.

Learn more

#### ​Design decisions

When implementing the subagents pattern, you’ll make several key design choices. This table summarizes the options—each is covered in detail in the sections below.

DecisionOptionsSync vs. asyncSync (blocking) vs. async (background)Tool patternsTool per agent vs. single dispatch toolSubagent inputsQuery only vs. full contextSubagent outputsSubagent result vs full conversation history

#### ​Sync vs. async

Subagent execution can be synchronous (blocking) or asynchronous (background). Your choice depends on whether the main agent needs the result to continue.

ModeMain agent behaviorBest forTradeoffSyncWaits for subagent to completeMain agent needs result to continueSimple, but blocks the conversationAsyncContinues while subagent runs in backgroundIndependent tasks, user shouldn’t waitResponsive, but more complex

Not to be confused with Python’s async/await. Here, “async” means the main agent kicks off a background job (typically in a separate process or service) and continues without blocking.

##### ​Synchronous (default)

By default, subagent calls are synchronous—the main agent waits for each subagent to complete before continuing. Use sync when the main agent’s next action depends on the subagent’s result.

When to use sync:

- Main agent needs the subagent’s result to formulate its response
- Tasks have order dependencies (e.g., fetch data → analyze → respond)
- Subagent failures should block the main agent’s response
Tradeoffs:

- Simple implementation—just call and wait
- User sees no response until all subagents complete
- Long-running tasks freeze the conversation

##### ​Asynchronous

Use asynchronous execution when the subagent’s work is independent—the main agent doesn’t need the result to continue conversing with the user. The main agent kicks off a background job and remains responsive.

When to use async:

- Subagent work is independent of the main conversation flow
- Users should be able to continue chatting while work happens
- You want to run multiple independent tasks in parallel
Three-tool pattern:

- Start job: Kicks off the background task, returns a job ID
- Check status: Returns current state (pending, running, completed, failed)
- Get result: Retrieves the completed result
Handling job completion: When a job finishes, your application needs to notify the user. One approach: surface a notification that, when clicked, sends a HumanMessage like “Check job_123 and summarize the results.”

#### ​Tool patterns

There are two main ways to expose subagents as tools:

PatternBest forTrade-offTool per agentFine-grained control over each subagent’s input/outputMore setup, but more customizationSingle dispatch toolMany agents, distributed teams, convention over configurationSimpler composition, less per-agent customization

##### ​Tool per agent

The key idea is wrapping subagents as tools that the main agent can call:

Copyfrom langchain.tools import tool
```python
from langchain.agents import create_agent

# Create a sub-agent
subagent = create_agent(model="...", tools=[...])

# Wrap it as a tool  #
@tool("subagent_name", description="subagent_description")
def call_subagent(query: str):
    result = subagent.invoke({"messages": [{"role": "user", "content": query}]})
    return result["messages"][-1].content

# Main agent with subagent as a tool  #
main_agent = create_agent(model="...", tools=[call_subagent])

The main agent invokes the subagent tool when it decides the task matches the subagent’s description, receives the result, and continues orchestration. See Context engineering for fine-grained control.
```

##### ​Single dispatch tool

An alternative approach uses a single parameterized tool to invoke ephemeral sub-agents for independent tasks. Unlike the tool per agent approach where each sub-agent is wrapped as a separate tool, this uses a convention-based approach with a single task tool: the task description is passed as a human message to the sub-agent, and the sub-agent’s final message is returned as the tool result.

Use this approach when you want to distribute agent development across multiple teams, need to isolate complex tasks into separate context windows, need a scalable way to add new agents without modifying the coordinator, or prefer convention over customization. This approach trades flexibility in context engineering for simplicity in agent composition and strong context isolation.

Key characteristics:

- Single task tool: One parameterized tool that can invoke any registered sub-agent by name
- Convention-based invocation: Agent selected by name, task passed as human message, final message returned as tool result
- Team distribution: Different teams can develop and deploy agents independently
- Agent discovery: Sub-agents can be discovered via system prompt (listing available agents) or through progressive disclosure (loading agent information on-demand via tools)
An interesting aspect of this approach is that sub-agents may have the exact same capabilities as the main agent. In such cases, invoking a sub-agent is really about context isolation as the primary reason—allowing complex, multi-step tasks to run in isolated context windows without bloating the main agent’s conversation history. The sub-agent completes its work autonomously and returns only a concise summary, keeping the main thread focused and efficient.

Agent registry with task dispatcherCopyfrom langchain.tools import tool
```python
from langchain.agents import create_agent

# Sub-agents developed by different teams
research_agent = create_agent(
    model="gpt-4o",
    prompt="You are a research specialist..."
)

writer_agent = create_agent(
    model="gpt-4o",
    prompt="You are a writing specialist..."
)

# Registry of available sub-agents
SUBAGENTS = {
    "research": research_agent,
    "writer": writer_agent,
}

@tool
def task(
    agent_name: str,
    description: str
) -> str:
    """Launch an ephemeral subagent for a task.

    Available agents:
    - research: Research and fact-finding
    - writer: Content creation and editing
    """
    agent = SUBAGENTS[agent_name]
    result = agent.invoke({
        "messages": [
            {"role": "user", "content": description}
        ]
    })
    return result["messages"][-1].content

# Main coordinator agent
main_agent = create_agent(
    model="gpt-4o",
    tools=[task],
    system_prompt=(
        "You coordinate specialized sub-agents. "
        "Available: research (fact-finding), "
        "writer (content creation). "
        "Use the task tool to delegate work."
    ),
)
```

#### ​Context engineering

Control how context flows between the main agent and its subagents:

CategoryPurposeImpactsSubagent specsEnsure subagents are invoked when they should beMain agent routing decisionsSubagent inputsEnsure subagents can execute well with optimized contextSubagent performanceSubagent outputsEnsure the supervisor can act on subagent resultsMain agent performance

See also our comprehensive guide on context engineering for agents.

##### ​Subagent specs

The names and descriptions associated with subagents are the primary way the main agent knows which subagents to invoke.
These are prompting levers—choose them carefully.

- Name: How the main agent refers to the sub-agent. Keep it clear and action-oriented (e.g., research_agent, code_reviewer).
- Description: What the main agent knows about the sub-agent’s capabilities. Be specific about what tasks it handles and when to use it.
For the single dispatch tool design, the main agent needs to call the task tool with the name of the subagent to invoke. The available tools can be provided to the main agent via one of the following methods:

- System prompt enumeration: List available agents in the system prompt.
- Enum constraint on dispatch tool: For small agent lists, add an enum to the agent_name field.
- Tool-based discovery: For large or dynamic agent registries, provide a separate tool (e.g., list_agents or search_agents) that returns available agents.

##### ​Subagent inputs

Customize what context the subagent receives to execute its task. Add input that isn’t practical to capture in a static prompt—full message history, prior results, or task metadata—by pulling from the agent’s state.

Subagent inputs exampleCopyfrom langchain.agents import AgentState
```python
from langchain.tools import tool, ToolRuntime

class CustomState(AgentState):
    example_state_key: str

@tool(
    "subagent1_name",
    description="subagent1_description"
)
def call_subagent1(query: str, runtime: ToolRuntime[None, CustomState]):
    # Apply any logic needed to transform the messages into a suitable input
    subagent_input = some_logic(query, runtime.state["messages"])
    result = subagent1.invoke({
        "messages": subagent_input,
        # You could also pass other state keys here as needed.
        # Make sure to define these in both the main and subagent's
        # state schemas.
        "example_state_key": runtime.state["example_state_key"]
    })
    return result["messages"][-1].content
See all 21 lines
```

##### ​Subagent outputs

Customize what the main agent receives back so it can make good decisions. Two strategies:

- Prompt the sub-agent: Specify exactly what should be returned. A common failure mode is that the sub-agent performs tool calls or reasoning but doesn’t include results in its final message—remind it that the supervisor only sees the final output.
- Format in code: Adjust or enrich the response before returning it. For example, pass specific state keys back in addition to the final text using a Command.
Subagent outputs exampleCopyfrom typing import Annotated
```python
from langchain.agents import AgentState
from langchain.tools import InjectedToolCallId
from langgraph.types import Command

@tool(
    "subagent1_name",
    description="subagent1_description"
)
def call_subagent1(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    result = subagent1.invoke({
        "messages": [{"role": "user", "content": query}]
    })
    return Command(update={
        # Pass back additional state from the subagent
        "example_state_key": result["example_state_key"],
        "messages": [
            ToolMessage(
                content=result["messages"][-1].content,
                tool_call_id=tool_call_id
            )
        ]
    })
See all 27 lines

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```


---

## Get help - Docs by LangChain {#doc-7}

**Source:** [https://docs.langchain.com/oss/python/langchain/get-help](https://docs.langchain.com/oss/python/langchain/get-help)

### Get help

Copy page

#### ​Learning resources

Start your journey or deepen your knowledge with our comprehensive learning materials.

- Chat LangChain: Ask the docs anything about LangChain, powered by real-time docs
- API Reference: Complete documentation for all LangChain packages

#### ​Community support

Get help from fellow developers and the LangChain team through our active community channels.

- Community Forum: Ask questions, share solutions, and discuss best practices
- Community Slack: Connect with other builders and get quick help

#### ​Professional support

For enterprise needs and critical applications, access dedicated support channels.

- Support portal: Submit tickets and track support requests
- LangSmith status: Real-time status of LangSmith services and APIs

#### ​Contribute

Help us improve LangChain for everyone. Whether you’re fixing bugs, adding features, or improving documentation, we welcome your contributions.

- Contributing Guide: Everything you need to know about contributing to LangChain

#### ​Stay connected

Follow us for the latest updates, announcements, and community highlights.

- X (Twitter): Daily updates and community spotlights
- LinkedIn: Professional network and company updates
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Component architecture - Docs by LangChain {#doc-8}

**Source:** [https://docs.langchain.com/oss/python/langchain/component-architecture](https://docs.langchain.com/oss/python/langchain/component-architecture)

### Component architecture

Copy page

#### ​Core component ecosystem

The diagram below shows how LangChain’s major components connect to form complete AI applications:

##### ​How components connect

Each component layer builds on the previous ones:

- Input processing – Transform raw data into structured documents
- Embedding & storage – Convert text into searchable vector representations
- Retrieval – Find relevant information based on user queries
- Generation – Use AI models to create responses, optionally with tools
- Orchestration – Coordinate everything through agents and memory systems

#### ​Component categories

LangChain organizes components into these main categories:

CategoryPurposeKey ComponentsUse CasesModelsAI reasoning and generationChat models, LLMs, Embedding modelsText generation, reasoning, semantic understandingToolsExternal capabilitiesAPIs, databases, etc.Web search, data access, computationsAgentsOrchestration and reasoningReAct agents, tool calling agentsNondeterministic workflows, decision makingMemoryContext preservationMessage history, custom stateConversations, stateful interactionsRetrieversInformation accessVector retrievers, web retrieversRAG, knowledge base searchDocument processingData ingestionLoaders, splitters, transformersPDF processing, web scrapingVector StoresSemantic searchChroma, Pinecone, FAISSSimilarity search, embeddings storage

#### ​Common patterns

##### ​RAG (Retrieval-Augmented Generation)

##### ​Agent with tools

##### ​Multi-agent system

#### ​Learn more

Now that you understand how components relate to each other, explore specific areas:

- Building your first RAG system
- Creating agents
- Working with tools
- Setting up memory
- Browse integrations
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Build a SQL assistant with on-demand skills - Docs by LangChain {#doc-9}

**Source:** [https://docs.langchain.com/oss/python/langchain/multi-agent/skills-sql-assistant](https://docs.langchain.com/oss/python/langchain/multi-agent/skills-sql-assistant)

### Build a SQL assistant with on-demand skills

Copy page

#### ​How it works

Here’s the flow when a user asks for a SQL query:

Why progressive disclosure:

- Reduces context usage - load only the 2-3 skills needed for a task, not all available skills
- Enables team autonomy - different teams can develop specialized skills independently (similar to other multi-agent architectures)
- Scales efficiently - add dozens or hundreds of skills without overwhelming context
- Simplifies conversation history - single agent with one conversation thread
What are skills: Skills, as popularized by Claude Code, are primarily prompt-based: self-contained units of specialized instructions for specific business tasks. In Claude Code, skills are exposed as directories with files on the file system, discovered through file operations. Skills guide behavior through prompts and can provide information about tool usage or include sample code for a coding agent to execute.

Skills with progressive disclosure can be viewed as a form of RAG (Retrieval-Augmented Generation), where each skill is a retrieval unit—though not necessarily backed by embeddings or keyword search, but by tools for browsing content (like file operations or, in this tutorial, direct lookup).

Trade-offs:

- Latency: Loading skills on-demand requires additional tool calls, which adds latency to the first request that needs each skill
- Workflow control: Basic implementations rely on prompting to guide skill usage - you cannot enforce hard constraints like “always try skill A before skill B” without custom logic
Implementing your own skills systemWhen building your own skills implementation (as we do in this tutorial), the core concept is progressive disclosure - loading information on-demand. Beyond that, you have full flexibility in implementation:
Storage: databases, S3, in-memory data structures, or any backend
Discovery: direct lookup (this tutorial), RAG for large skill collections, file system scanning, or API calls
Loading logic: customize latency characteristics and add logic to search through skill content or rank relevance
Side effects: define what happens when a skill loads, such as exposing tools associated with that skill (covered in section 8)
This flexibility lets you optimize for your specific requirements around performance, storage, and workflow control.

#### ​Setup

##### ​Installation

This tutorial requires the langchain package:

pipuvcondaCopypip install langchain

For more details, see our Installation guide.

##### ​LangSmith

Set up LangSmith to inspect what is happening inside your agent. Then set the following environment variables:

bashpythonCopyexport LANGSMITH_TRACING="true"
export LANGSMITH_API_KEY="..."

##### ​Select an LLM

Select a chat model from LangChain’s suite of integrations:

OpenAI Anthropic Azure Google Gemini AWS Bedrock HuggingFace👉 Read the OpenAI chat model integration docsCopypip install -U "langchain[openai]"
init_chat_modelModel ClassCopyimport os
```python
from langchain.chat_models import init_chat_model

os.environ["OPENAI_API_KEY"] = "sk-..."

model = init_chat_model("gpt-4.1")
👉 Read the Anthropic chat model integration docsCopypip install -U "langchain[anthropic]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["ANTHROPIC_API_KEY"] = "sk-..."

model = init_chat_model("claude-sonnet-4-5-20250929")
👉 Read the Azure chat model integration docsCopypip install -U "langchain[openai]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["AZURE_OPENAI_API_KEY"] = "..."
os.environ["AZURE_OPENAI_ENDPOINT"] = "..."
os.environ["OPENAI_API_VERSION"] = "2025-03-01-preview"

model = init_chat_model(
    "azure_openai:gpt-4.1",
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
)
👉 Read the Google GenAI chat model integration docsCopypip install -U "langchain[google-genai]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["GOOGLE_API_KEY"] = "..."

model = init_chat_model("google_genai:gemini-2.5-flash-lite")
👉 Read the AWS Bedrock chat model integration docsCopypip install -U "langchain[aws]"
init_chat_modelModel ClassCopyfrom langchain.chat_models import init_chat_model

# Follow the steps here to configure your credentials:
# https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html

model = init_chat_model(
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
    model_provider="bedrock_converse",
)
👉 Read the HuggingFace chat model integration docsCopypip install -U "langchain[huggingface]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["HUGGINGFACEHUB_API_TOKEN"] = "hf_..."

model = init_chat_model(
    "microsoft/Phi-3-mini-4k-instruct",
    model_provider="huggingface",
    temperature=0.7,
    max_tokens=1024,
)
```

#### ​1. Define skills

First, define the structure for skills. Each skill has a name, a brief description (shown in the system prompt), and full content (loaded on-demand):

Copyfrom typing import TypedDict

```python
class Skill(TypedDict):
    """A skill that can be progressively disclosed to the agent."""
    name: str  # Unique identifier for the skill
    description: str  # 1-2 sentence description to show in system prompt
    content: str  # Full skill content with detailed instructions

Now define example skills for a SQL query assistant. The skills are designed to be lightweight in description (shown to the agent upfront) but detailed in content (loaded only when needed):

View complete skill definitionsCopySKILLS: list[Skill] = [
    {
        "name": "sales_analytics",
        "description": "Database schema and business logic for sales data analysis including customers, orders, and revenue.",
        "content": """# Sales Analytics Schema

## Tables

### customers
- customer_id (PRIMARY KEY)
- name
- email
- signup_date
- status (active/inactive)
- customer_tier (bronze/silver/gold/platinum)

### orders
- order_id (PRIMARY KEY)
- customer_id (FOREIGN KEY -> customers)
- order_date
- status (pending/completed/cancelled/refunded)
- total_amount
- sales_region (north/south/east/west)

### order_items
- item_id (PRIMARY KEY)
- order_id (FOREIGN KEY -> orders)
- product_id
- quantity
- unit_price
- discount_percent

## Business Logic

**Active customers**: status = 'active' AND signup_date <= CURRENT_DATE - INTERVAL '90 days'

**Revenue calculation**: Only count orders with status = 'completed'. Use total_amount from orders table, which already accounts for discounts.

**Customer lifetime value (CLV)**: Sum of all completed order amounts for a customer.

**High-value orders**: Orders with total_amount > 1000

## Example Query

-- Get top 10 customers by revenue in the last quarter
SELECT
    c.customer_id,
    c.name,
    c.customer_tier,
    SUM(o.total_amount) as total_revenue
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status = 'completed'
  AND o.order_date >= CURRENT_DATE - INTERVAL '3 months'
GROUP BY c.customer_id, c.name, c.customer_tier
ORDER BY total_revenue DESC
LIMIT 10;
""",
    },
    {
        "name": "inventory_management",
        "description": "Database schema and business logic for inventory tracking including products, warehouses, and stock levels.",
        "content": """# Inventory Management Schema

## Tables

### products
- product_id (PRIMARY KEY)
- product_name
- sku
- category
- unit_cost
- reorder_point (minimum stock level before reordering)
- discontinued (boolean)

### warehouses
- warehouse_id (PRIMARY KEY)
- warehouse_name
- location
- capacity

### inventory
- inventory_id (PRIMARY KEY)
- product_id (FOREIGN KEY -> products)
- warehouse_id (FOREIGN KEY -> warehouses)
- quantity_on_hand
- last_updated

### stock_movements
- movement_id (PRIMARY KEY)
- product_id (FOREIGN KEY -> products)
- warehouse_id (FOREIGN KEY -> warehouses)
- movement_type (inbound/outbound/transfer/adjustment)
- quantity (positive for inbound, negative for outbound)
- movement_date
- reference_number

## Business Logic

**Available stock**: quantity_on_hand from inventory table where quantity_on_hand > 0

**Products needing reorder**: Products where total quantity_on_hand across all warehouses is less than or equal to the product's reorder_point

**Active products only**: Exclude products where discontinued = true unless specifically analyzing discontinued items

**Stock valuation**: quantity_on_hand * unit_cost for each product

## Example Query

-- Find products below reorder point across all warehouses
SELECT
    p.product_id,
    p.product_name,
    p.reorder_point,
    SUM(i.quantity_on_hand) as total_stock,
    p.unit_cost,
    (p.reorder_point - SUM(i.quantity_on_hand)) as units_to_reorder
FROM products p
JOIN inventory i ON p.product_id = i.product_id
WHERE p.discontinued = false
GROUP BY p.product_id, p.product_name, p.reorder_point, p.unit_cost
HAVING SUM(i.quantity_on_hand) <= p.reorder_point
ORDER BY units_to_reorder DESC;
""",
    },
]
```

#### ​2. Create skill loading tool

Create a tool to load full skill content on-demand:

Copyfrom langchain.tools import tool

```python
@tool
def load_skill(skill_name: str) -> str:
    """Load the full content of a skill into the agent's context.

    Use this when you need detailed information about how to handle a specific
    type of request. This will provide you with comprehensive instructions,
    policies, and guidelines for the skill area.

    Args:
        skill_name: The name of the skill to load (e.g., "expense_reporting", "travel_booking")
    """
    # Find and return the requested skill
    for skill in SKILLS:
        if skill["name"] == skill_name:
            return f"Loaded skill: {skill_name}\n\n{skill['content']}"

    # Skill not found
    available = ", ".join(s["name"] for s in SKILLS)
    return f"Skill '{skill_name}' not found. Available skills: {available}"

The load_skill tool returns the full skill content as a string, which becomes part of the conversation as a ToolMessage. For more details on creating and using tools, see the Tools guide.
```

#### ​3. Build skill middleware

Create custom middleware that injects skill descriptions into the system prompt. This middleware makes skills discoverable without loading their full content upfront.

This guide demonstrates creating custom middleware. For a comprehensive guide on middleware concepts and patterns, see the custom middleware documentation.

Copyfrom langchain.agents.middleware import ModelRequest, ModelResponse, AgentMiddleware
```python
from langchain.messages import SystemMessage
from typing import Callable

class SkillMiddleware(AgentMiddleware):
    """Middleware that injects skill descriptions into the system prompt."""

    # Register the load_skill tool as a class variable
    tools = [load_skill]

    def __init__(self):
        """Initialize and generate the skills prompt from SKILLS."""
        # Build skills prompt from the SKILLS list
        skills_list = []
        for skill in SKILLS:
            skills_list.append(
                f"- **{skill['name']}**: {skill['description']}"
            )
        self.skills_prompt = "\n".join(skills_list)

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Sync: Inject skill descriptions into system prompt."""
        # Build the skills addendum
        skills_addendum = (
            f"\n\n## Available Skills\n\n{self.skills_prompt}\n\n"
            "Use the load_skill tool when you need detailed information "
            "about handling a specific type of request."
        )

        # Append to system message content blocks
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": skills_addendum}
        ]
        new_system_message = SystemMessage(content=new_content)
        modified_request = request.override(system_message=new_system_message)
        return handler(modified_request)

The middleware appends skill descriptions to the system prompt, making the agent aware of available skills without loading their full content. The load_skill tool is registered as a class variable, making it available to the agent.

Production consideration: This tutorial loads the skill list in __init__ for simplicity. In a production system, you may want to load skills in the before_agent hook instead, allowing them to be refreshed periodically to reflect up-to-date changes (e.g., when new skills are added or existing ones are modified). See the before_agent hook documentation for details.
```

#### ​4. Create the agent with skill support

Now create the agent with the skill middleware and a checkpointer for state persistence:

Copyfrom langchain.agents import create_agent
```python
from langgraph.checkpoint.memory import InMemorySaver

# Create the agent with skill support
agent = create_agent(
    model,
    system_prompt=(
        "You are a SQL query assistant that helps users "
        "write queries against business databases."
    ),
    middleware=[SkillMiddleware()],
    checkpointer=InMemorySaver(),
)

The agent now has access to skill descriptions in its system prompt and can call load_skill to retrieve full skill content when needed. The checkpointer maintains conversation history across turns.
```

#### ​5. Test progressive disclosure

Test the agent with a question that requires skill-specific knowledge:

Copyimport uuid

# Configuration for this conversation thread
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

# Ask for a SQL query
result = agent.invoke(
```
    {
        "messages": [
            {
                "role": "user",
                "content": (
                    "Write a SQL query to find all customers "
                    "who made orders over $1000 in the last month"
                ),
            }
        ]
    },
    config
)

# Print the conversation
for message in result["messages"]:
    if hasattr(message, 'pretty_print'):
        message.pretty_print()
    else:
        print(f"{message.type}: {message.content}")

Expected output:

Copy================================ Human Message =================================

Write a SQL query to find all customers who made orders over $1000 in the last month
================================== Ai Message ==================================
Tool Calls:
  load_skill (call_abc123)
 Call ID: call_abc123
  Args:
    skill_name: sales_analytics
================================= Tool Message =================================
Name: load_skill

Loaded skill: sales_analytics

# Sales Analytics Schema

## Tables

### customers
- customer_id (PRIMARY KEY)
- name
- email
- signup_date
- status (active/inactive)
- customer_tier (bronze/silver/gold/platinum)

### orders
- order_id (PRIMARY KEY)
- customer_id (FOREIGN KEY -> customers)
- order_date
- status (pending/completed/cancelled/refunded)
- total_amount
- sales_region (north/south/east/west)

[... rest of schema ...]

## Business Logic

**High-value orders**: Orders with `total_amount > 1000`
**Revenue calculation**: Only count orders with `status = 'completed'`

================================== Ai Message ==================================

Here's a SQL query to find all customers who made orders over $1000 in the last month:

\`\`\`sql
SELECT DISTINCT
    c.customer_id,
    c.name,
    c.email,
    c.customer_tier
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.total_amount > 1000
  AND o.status = 'completed'
  AND o.order_date >= CURRENT_DATE - INTERVAL '1 month'
ORDER BY c.customer_id;
\`\`\`

This query:
- Joins customers with their orders
- Filters for high-value orders (>$1000) using the total_amount field
- Only includes completed orders (as per the business logic)
- Restricts to orders from the last month
- Returns distinct customers to avoid duplicates if they made multiple qualifying orders

The agent saw the lightweight skill description in its system prompt, recognized the question required sales database knowledge, called load_skill("sales_analytics") to get the full schema and business logic, and then used that information to write a correct query following the database conventions.
```

#### ​6. Advanced: Add constraints with custom state

Optional: Track loaded skills and enforce tool constraintsYou can add constraints to enforce that certain tools are only available after specific skills have been loaded. This requires tracking which skills have been loaded in custom agent state.​Define custom stateFirst, extend the agent state to track loaded skills:Copyfrom langchain.agents.middleware import AgentState

class CustomState(AgentState):
    skills_loaded: NotRequired[list[str]]  # Track which skills have been loaded  #
​Update load_skill to modify stateModify the load_skill tool to update state when a skill is loaded:Copyfrom langgraph.types import Command
from langchain.tools import tool, ToolRuntime
from langchain.messages import ToolMessage

@tool
def load_skill(skill_name: str, runtime: ToolRuntime) -> Command:
    """Load the full content of a skill into the agent's context.

    Use this when you need detailed information about how to handle a specific
    type of request. This will provide you with comprehensive instructions,
    policies, and guidelines for the skill area.

    Args:
        skill_name: The name of the skill to load
    """
    # Find and return the requested skill
    for skill in SKILLS:
        if skill["name"] == skill_name:
            skill_content = f"Loaded skill: {skill_name}\n\n{skill['content']}"

            # Update state to track loaded skill
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            content=skill_content,
                            tool_call_id=runtime.tool_call_id,
                        )
                    ],
                    "skills_loaded": [skill_name],
                }
            )

    # Skill not found
    available = ", ".join(s["name"] for s in SKILLS)
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"Skill '{skill_name}' not found. Available skills: {available}",
                    tool_call_id=runtime.tool_call_id,
                )
            ]
        }
    )
​Create constrained toolCreate a tool that’s only usable after a specific skill has been loaded:Copy@tool
def write_sql_query(
    query: str,
    vertical: str,
    runtime: ToolRuntime,
) -> str:
    """Write and validate a SQL query for a specific business vertical.

    This tool helps format and validate SQL queries. You must load the
    appropriate skill first to understand the database schema.

    Args:
        query: The SQL query to write
        vertical: The business vertical (sales_analytics or inventory_management)
    """
    # Check if the required skill has been loaded
    skills_loaded = runtime.state.get("skills_loaded", [])

    if vertical not in skills_loaded:
        return (
            f"Error: You must load the '{vertical}' skill first "
            f"to understand the database schema before writing queries. "
            f"Use load_skill('{vertical}') to load the schema."
        )

    # Validate and format the query
    return (
        f"SQL Query for {vertical}:\n\n"
        f"```sql\n{query}\n```\n\n"
        f"✓ Query validated against {vertical} schema\n"
        f"Ready to execute against the database."
    )
​Update middleware and agentUpdate the middleware to use the custom state schema:Copyclass SkillMiddleware(AgentMiddleware[CustomState]):
    """Middleware that injects skill descriptions into the system prompt."""

    state_schema = CustomState
    tools = [load_skill, write_sql_query]

    # ... rest of the middleware implementation stays the same
Create the agent with the middleware that registers the constrained tool:Copyagent = create_agent(
    model,
    system_prompt=(
        "You are a SQL query assistant that helps users "
        "write queries against business databases."
    ),
    middleware=[SkillMiddleware()],
    checkpointer=InMemorySaver(),
)
Now if the agent tries to use write_sql_query before loading the required skill, it will receive an error message prompting it to load the appropriate skill (e.g., sales_analytics or inventory_management) first. This ensures the agent has the necessary schema knowledge before attempting to validate queries.

​Complete example

View complete runnable scriptHere’s a complete, runnable implementation combining all the pieces from this tutorial:Copyimport uuid
from typing import TypedDict, NotRequired
from langchain.tools import tool
from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, ModelResponse, AgentMiddleware
from langchain.messages import SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from typing import Callable

# Define skill structure
class Skill(TypedDict):
    """A skill that can be progressively disclosed to the agent."""
    name: str
    description: str
    content: str

# Define skills with schemas and business logic
SKILLS: list[Skill] = [
    {
        "name": "sales_analytics",
        "description": "Database schema and business logic for sales data analysis including customers, orders, and revenue.",
        "content": """# Sales Analytics Schema

## Tables

### customers
- customer_id (PRIMARY KEY)
- name
- email
- signup_date
- status (active/inactive)
- customer_tier (bronze/silver/gold/platinum)

### orders
- order_id (PRIMARY KEY)
- customer_id (FOREIGN KEY -> customers)
- order_date
- status (pending/completed/cancelled/refunded)
- total_amount
- sales_region (north/south/east/west)

### order_items
- item_id (PRIMARY KEY)
- order_id (FOREIGN KEY -> orders)
- product_id
- quantity
- unit_price
- discount_percent

## Business Logic

**Active customers**: status = 'active' AND signup_date <= CURRENT_DATE - INTERVAL '90 days'

**Revenue calculation**: Only count orders with status = 'completed'. Use total_amount from orders table, which already accounts for discounts.

**Customer lifetime value (CLV)**: Sum of all completed order amounts for a customer.

**High-value orders**: Orders with total_amount > 1000

## Example Query

-- Get top 10 customers by revenue in the last quarter
SELECT
    c.customer_id,
    c.name,
    c.customer_tier,
    SUM(o.total_amount) as total_revenue
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status = 'completed'
  AND o.order_date >= CURRENT_DATE - INTERVAL '3 months'
GROUP BY c.customer_id, c.name, c.customer_tier
ORDER BY total_revenue DESC
LIMIT 10;
""",
    },
    {
        "name": "inventory_management",
        "description": "Database schema and business logic for inventory tracking including products, warehouses, and stock levels.",
        "content": """# Inventory Management Schema

## Tables

### products
- product_id (PRIMARY KEY)
- product_name
- sku
- category
- unit_cost
- reorder_point (minimum stock level before reordering)
- discontinued (boolean)

### warehouses
- warehouse_id (PRIMARY KEY)
- warehouse_name
- location
- capacity

### inventory
- inventory_id (PRIMARY KEY)
- product_id (FOREIGN KEY -> products)
- warehouse_id (FOREIGN KEY -> warehouses)
- quantity_on_hand
- last_updated

### stock_movements
- movement_id (PRIMARY KEY)
- product_id (FOREIGN KEY -> products)
- warehouse_id (FOREIGN KEY -> warehouses)
- movement_type (inbound/outbound/transfer/adjustment)
- quantity (positive for inbound, negative for outbound)
- movement_date
- reference_number

## Business Logic

**Available stock**: quantity_on_hand from inventory table where quantity_on_hand > 0

**Products needing reorder**: Products where total quantity_on_hand across all warehouses is less than or equal to the product's reorder_point

**Active products only**: Exclude products where discontinued = true unless specifically analyzing discontinued items

**Stock valuation**: quantity_on_hand * unit_cost for each product

## Example Query

-- Find products below reorder point across all warehouses
SELECT
    p.product_id,
    p.product_name,
    p.reorder_point,
    SUM(i.quantity_on_hand) as total_stock,
    p.unit_cost,
    (p.reorder_point - SUM(i.quantity_on_hand)) as units_to_reorder
FROM products p
JOIN inventory i ON p.product_id = i.product_id
WHERE p.discontinued = false
GROUP BY p.product_id, p.product_name, p.reorder_point, p.unit_cost
HAVING SUM(i.quantity_on_hand) <= p.reorder_point
ORDER BY units_to_reorder DESC;
""",
    },
]

# Create skill loading tool
@tool
def load_skill(skill_name: str) -> str:
    """Load the full content of a skill into the agent's context.

    Use this when you need detailed information about how to handle a specific
    type of request. This will provide you with comprehensive instructions,
    policies, and guidelines for the skill area.

    Args:
        skill_name: The name of the skill to load (e.g., "sales_analytics", "inventory_management")
    """
    # Find and return the requested skill
    for skill in SKILLS:
        if skill["name"] == skill_name:
            return f"Loaded skill: {skill_name}\n\n{skill['content']}"

    # Skill not found
    available = ", ".join(s["name"] for s in SKILLS)
    return f"Skill '{skill_name}' not found. Available skills: {available}"

# Create skill middleware
class SkillMiddleware(AgentMiddleware):
    """Middleware that injects skill descriptions into the system prompt."""

    # Register the load_skill tool as a class variable
    tools = [load_skill]

    def __init__(self):
        """Initialize and generate the skills prompt from SKILLS."""
        # Build skills prompt from the SKILLS list
        skills_list = []
        for skill in SKILLS:
            skills_list.append(
                f"- **{skill['name']}**: {skill['description']}"
            )
        self.skills_prompt = "\n".join(skills_list)

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Sync: Inject skill descriptions into system prompt."""
        # Build the skills addendum
        skills_addendum = (
            f"\n\n## Available Skills\n\n{self.skills_prompt}\n\n"
            "Use the load_skill tool when you need detailed information "
            "about handling a specific type of request."
        )

        # Append to system message content blocks
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": skills_addendum}
        ]
        new_system_message = SystemMessage(content=new_content)
        modified_request = request.override(system_message=new_system_message)
        return handler(modified_request)

# Initialize your chat model (replace with your model)
# Example: from langchain_anthropic import ChatAnthropic
# model = ChatAnthropic(model="claude-3-5-sonnet-20241022")
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model="gpt-4")

# Create the agent with skill support
agent = create_agent(
    model,
    system_prompt=(
        "You are a SQL query assistant that helps users "
        "write queries against business databases."
    ),
    middleware=[SkillMiddleware()],
    checkpointer=InMemorySaver(),
)

# Example usage
if __name__ == "__main__":
    # Configuration for this conversation thread
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Ask for a SQL query
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Write a SQL query to find all customers "
                        "who made orders over $1000 in the last month"
                    ),
                }
            ]
        },
        config
    )

    # Print the conversation
    for message in result["messages"]:
        if hasattr(message, 'pretty_print'):
            message.pretty_print()
        else:
            print(f"{message.type}: {message.content}")
This complete example includes:
Skill definitions with full database schemas
The load_skill tool for on-demand loading
SkillMiddleware that injects skill descriptions into the system prompt
Agent creation with middleware and checkpointer
Example usage showing how the agent loads skills and writes SQL queries
To run this, you’ll need to:
Install required packages: pip install langchain langchain-openai langgraph
Set your API key (e.g., export OPENAI_API_KEY=...)
Replace the model initialization with your preferred LLM provider

​Implementation variations

View implementation options and trade-offsThis tutorial implemented skills as in-memory Python dictionaries loaded through tool calls. However, there are several ways to implement progressive disclosure with skills:Storage backends:
In-memory (this tutorial): Skills defined as Python data structures, fast access, no I/O overhead
File system (Claude Code approach): Skills as directories with files, discovered via file operations like read_file
Remote storage: Skills in S3, databases, Notion, or APIs, fetched on-demand
Skill discovery (how the agent learns which skills exist):
System prompt listing: Skill descriptions in system prompt (used in this tutorial)
File-based: Discover skills by scanning directories (Claude Code approach)
Registry-based: Query a skill registry service or API for available skills
Dynamic lookup: List available skills via a tool call
Progressive disclosure strategies (how skill content is loaded):
Single load: Load entire skill content in one tool call (used in this tutorial)
Paginated: Load skill content in multiple pages/chunks for large skills
Search-based: Search within a specific skill’s content for relevant sections (e.g., using grep/read operations on skill files)
Hierarchical: Load skill overview first, then drill into specific subsections
Size considerations (uncalibrated mental model - optimize for your system):
Small skills (< 1K tokens / ~750 words): Can be included directly in system prompt and cached with prompt caching for cost savings and faster responses
Medium skills (1-10K tokens / ~750-7.5K words): Benefit from on-demand loading to avoid context overhead (this tutorial)
Large skills (> 10K tokens / ~7.5K words, or > 5-10% of context window): Should use progressive disclosure techniques like pagination, search-based loading, or hierarchical exploration to avoid consuming excessive context
The choice depends on your requirements: in-memory is fastest but requires redeployment for skill updates, while file-based or remote storage enables dynamic skill management without code changes.

​Progressive disclosure and context engineering

Combining with few-shot prompting and other techniquesProgressive disclosure is fundamentally a context engineering technique - you’re managing what information is available to the agent and when. This tutorial focused on loading database schemas, but the same principles apply to other types of context.​Combining with few-shot promptingFor the SQL query use case, you could extend progressive disclosure to dynamically load few-shot examples that match the user’s query:Example approach:
User asks: “Find customers who haven’t ordered in 6 months”
Agent loads sales_analytics schema (as shown in this tutorial)
Agent also loads 2-3 relevant example queries (via semantic search or tag-based lookup):

Query for finding inactive customers
Query with date-based filtering
Query joining customers and orders tables

Agent writes query using both schema knowledge AND example patterns
This combination of progressive disclosure (loading schemas on-demand) and dynamic few-shot prompting (loading relevant examples) creates a powerful context engineering pattern that scales to large knowledge bases while providing high-quality, grounded outputs.

​Next steps

- Learn about middleware for more dynamic agent behaviors
- Explore context engineering techniques for managing agent context
- Explore the handoffs pattern for sequential workflows
- Read the subagents pattern for parallel task routing
- See multi-agent patterns for other approaches to specialized agents
- Use LangSmith to debug and monitor skill loading
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.

##### ​Define custom state

First, extend the agent state to track loaded skills:

Copyfrom langchain.agents.middleware import AgentState

```python
class CustomState(AgentState):
    skills_loaded: NotRequired[list[str]]  # Track which skills have been loaded  #
```

##### ​Update load_skill to modify state

Modify the load_skill tool to update state when a skill is loaded:

Copyfrom langgraph.types import Command
```python
from langchain.tools import tool, ToolRuntime
from langchain.messages import ToolMessage

@tool
def load_skill(skill_name: str, runtime: ToolRuntime) -> Command:
    """Load the full content of a skill into the agent's context.

    Use this when you need detailed information about how to handle a specific
    type of request. This will provide you with comprehensive instructions,
    policies, and guidelines for the skill area.

    Args:
        skill_name: The name of the skill to load
    """
    # Find and return the requested skill
    for skill in SKILLS:
        if skill["name"] == skill_name:
            skill_content = f"Loaded skill: {skill_name}\n\n{skill['content']}"

            # Update state to track loaded skill
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            content=skill_content,
                            tool_call_id=runtime.tool_call_id,
                        )
                    ],
                    "skills_loaded": [skill_name],
                }
            )

    # Skill not found
    available = ", ".join(s["name"] for s in SKILLS)
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"Skill '{skill_name}' not found. Available skills: {available}",
                    tool_call_id=runtime.tool_call_id,
                )
            ]
        }
    )
```

##### ​Create constrained tool

Create a tool that’s only usable after a specific skill has been loaded:

Copy@tool
def write_sql_query(
    query: str,
    vertical: str,
    runtime: ToolRuntime,
) -> str:
    """Write and validate a SQL query for a specific business vertical.

    This tool helps format and validate SQL queries. You must load the
    appropriate skill first to understand the database schema.

    Args:
        query: The SQL query to write
        vertical: The business vertical (sales_analytics or inventory_management)
    """
    # Check if the required skill has been loaded
    skills_loaded = runtime.state.get("skills_loaded", [])

    if vertical not in skills_loaded:
        return (
            f"Error: You must load the '{vertical}' skill first "
            f"to understand the database schema before writing queries. "
            f"Use load_skill('{vertical}') to load the schema."
        )

    # Validate and format the query
    return (
        f"SQL Query for {vertical}:\n\n"
        f"```sql\n{query}\n```\n\n"
        f"✓ Query validated against {vertical} schema\n"
        f"Ready to execute against the database."
    )

##### ​Update middleware and agent

Update the middleware to use the custom state schema:

Copyclass SkillMiddleware(AgentMiddleware[CustomState]):
    """Middleware that injects skill descriptions into the system prompt."""

    state_schema = CustomState
    tools = [load_skill, write_sql_query]

    # ... rest of the middleware implementation stays the same

Create the agent with the middleware that registers the constrained tool:

Copyagent = create_agent(
    model,
    system_prompt=(
        "You are a SQL query assistant that helps users "
        "write queries against business databases."
    ),
    middleware=[SkillMiddleware()],
    checkpointer=InMemorySaver(),
)

Now if the agent tries to use write_sql_query before loading the required skill, it will receive an error message prompting it to load the appropriate skill (e.g., sales_analytics or inventory_management) first. This ensures the agent has the necessary schema knowledge before attempting to validate queries.

#### ​Complete example

View complete runnable scriptHere’s a complete, runnable implementation combining all the pieces from this tutorial:Copyimport uuid
```python
from typing import TypedDict, NotRequired
from langchain.tools import tool
from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, ModelResponse, AgentMiddleware
from langchain.messages import SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from typing import Callable

# Define skill structure
class Skill(TypedDict):
    """A skill that can be progressively disclosed to the agent."""
    name: str
    description: str
    content: str

# Define skills with schemas and business logic
SKILLS: list[Skill] = [
    {
        "name": "sales_analytics",
        "description": "Database schema and business logic for sales data analysis including customers, orders, and revenue.",
        "content": """# Sales Analytics Schema

## Tables

### customers
- customer_id (PRIMARY KEY)
- name
- email
- signup_date
- status (active/inactive)
- customer_tier (bronze/silver/gold/platinum)

### orders
- order_id (PRIMARY KEY)
- customer_id (FOREIGN KEY -> customers)
- order_date
- status (pending/completed/cancelled/refunded)
- total_amount
- sales_region (north/south/east/west)

### order_items
- item_id (PRIMARY KEY)
- order_id (FOREIGN KEY -> orders)
- product_id
- quantity
- unit_price
- discount_percent

## Business Logic

**Active customers**: status = 'active' AND signup_date <= CURRENT_DATE - INTERVAL '90 days'

**Revenue calculation**: Only count orders with status = 'completed'. Use total_amount from orders table, which already accounts for discounts.

**Customer lifetime value (CLV)**: Sum of all completed order amounts for a customer.

**High-value orders**: Orders with total_amount > 1000

## Example Query

-- Get top 10 customers by revenue in the last quarter
SELECT
    c.customer_id,
    c.name,
    c.customer_tier,
    SUM(o.total_amount) as total_revenue
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status = 'completed'
  AND o.order_date >= CURRENT_DATE - INTERVAL '3 months'
GROUP BY c.customer_id, c.name, c.customer_tier
ORDER BY total_revenue DESC
LIMIT 10;
""",
    },
    {
        "name": "inventory_management",
        "description": "Database schema and business logic for inventory tracking including products, warehouses, and stock levels.",
        "content": """# Inventory Management Schema

## Tables

### products
- product_id (PRIMARY KEY)
- product_name
- sku
- category
- unit_cost
- reorder_point (minimum stock level before reordering)
- discontinued (boolean)

### warehouses
- warehouse_id (PRIMARY KEY)
- warehouse_name
- location
- capacity

### inventory
- inventory_id (PRIMARY KEY)
- product_id (FOREIGN KEY -> products)
- warehouse_id (FOREIGN KEY -> warehouses)
- quantity_on_hand
- last_updated

### stock_movements
- movement_id (PRIMARY KEY)
- product_id (FOREIGN KEY -> products)
- warehouse_id (FOREIGN KEY -> warehouses)
- movement_type (inbound/outbound/transfer/adjustment)
- quantity (positive for inbound, negative for outbound)
- movement_date
- reference_number

## Business Logic

**Available stock**: quantity_on_hand from inventory table where quantity_on_hand > 0

**Products needing reorder**: Products where total quantity_on_hand across all warehouses is less than or equal to the product's reorder_point

**Active products only**: Exclude products where discontinued = true unless specifically analyzing discontinued items

**Stock valuation**: quantity_on_hand * unit_cost for each product

## Example Query

-- Find products below reorder point across all warehouses
SELECT
    p.product_id,
    p.product_name,
    p.reorder_point,
    SUM(i.quantity_on_hand) as total_stock,
    p.unit_cost,
    (p.reorder_point - SUM(i.quantity_on_hand)) as units_to_reorder
FROM products p
JOIN inventory i ON p.product_id = i.product_id
WHERE p.discontinued = false
GROUP BY p.product_id, p.product_name, p.reorder_point, p.unit_cost
HAVING SUM(i.quantity_on_hand) <= p.reorder_point
ORDER BY units_to_reorder DESC;
""",
    },
]

# Create skill loading tool
@tool
def load_skill(skill_name: str) -> str:
    """Load the full content of a skill into the agent's context.

    Use this when you need detailed information about how to handle a specific
    type of request. This will provide you with comprehensive instructions,
    policies, and guidelines for the skill area.

    Args:
        skill_name: The name of the skill to load (e.g., "sales_analytics", "inventory_management")
    """
    # Find and return the requested skill
    for skill in SKILLS:
        if skill["name"] == skill_name:
            return f"Loaded skill: {skill_name}\n\n{skill['content']}"

    # Skill not found
    available = ", ".join(s["name"] for s in SKILLS)
    return f"Skill '{skill_name}' not found. Available skills: {available}"

# Create skill middleware
class SkillMiddleware(AgentMiddleware):
    """Middleware that injects skill descriptions into the system prompt."""

    # Register the load_skill tool as a class variable
    tools = [load_skill]

    def __init__(self):
        """Initialize and generate the skills prompt from SKILLS."""
        # Build skills prompt from the SKILLS list
        skills_list = []
        for skill in SKILLS:
            skills_list.append(
                f"- **{skill['name']}**: {skill['description']}"
            )
        self.skills_prompt = "\n".join(skills_list)

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Sync: Inject skill descriptions into system prompt."""
        # Build the skills addendum
        skills_addendum = (
            f"\n\n## Available Skills\n\n{self.skills_prompt}\n\n"
            "Use the load_skill tool when you need detailed information "
            "about handling a specific type of request."
        )

        # Append to system message content blocks
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": skills_addendum}
        ]
        new_system_message = SystemMessage(content=new_content)
        modified_request = request.override(system_message=new_system_message)
        return handler(modified_request)

# Initialize your chat model (replace with your model)
# Example: from langchain_anthropic import ChatAnthropic
# model = ChatAnthropic(model="claude-3-5-sonnet-20241022")
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model="gpt-4")

# Create the agent with skill support
agent = create_agent(
    model,
    system_prompt=(
        "You are a SQL query assistant that helps users "
        "write queries against business databases."
    ),
    middleware=[SkillMiddleware()],
    checkpointer=InMemorySaver(),
)

# Example usage
if __name__ == "__main__":
    # Configuration for this conversation thread
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Ask for a SQL query
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Write a SQL query to find all customers "
                        "who made orders over $1000 in the last month"
                    ),
                }
            ]
        },
        config
    )

    # Print the conversation
    for message in result["messages"]:
        if hasattr(message, 'pretty_print'):
            message.pretty_print()
        else:
            print(f"{message.type}: {message.content}")
This complete example includes:
Skill definitions with full database schemas
The load_skill tool for on-demand loading
SkillMiddleware that injects skill descriptions into the system prompt
Agent creation with middleware and checkpointer
Example usage showing how the agent loads skills and writes SQL queries
To run this, you’ll need to:
Install required packages: pip install langchain langchain-openai langgraph
Set your API key (e.g., export OPENAI_API_KEY=...)
Replace the model initialization with your preferred LLM provider
```

#### ​Implementation variations

View implementation options and trade-offsThis tutorial implemented skills as in-memory Python dictionaries loaded through tool calls. However, there are several ways to implement progressive disclosure with skills:Storage backends:
In-memory (this tutorial): Skills defined as Python data structures, fast access, no I/O overhead
File system (Claude Code approach): Skills as directories with files, discovered via file operations like read_file
Remote storage: Skills in S3, databases, Notion, or APIs, fetched on-demand
Skill discovery (how the agent learns which skills exist):
System prompt listing: Skill descriptions in system prompt (used in this tutorial)
File-based: Discover skills by scanning directories (Claude Code approach)
Registry-based: Query a skill registry service or API for available skills
Dynamic lookup: List available skills via a tool call
Progressive disclosure strategies (how skill content is loaded):
Single load: Load entire skill content in one tool call (used in this tutorial)
Paginated: Load skill content in multiple pages/chunks for large skills
Search-based: Search within a specific skill’s content for relevant sections (e.g., using grep/read operations on skill files)
Hierarchical: Load skill overview first, then drill into specific subsections
Size considerations (uncalibrated mental model - optimize for your system):
Small skills (< 1K tokens / ~750 words): Can be included directly in system prompt and cached with prompt caching for cost savings and faster responses
Medium skills (1-10K tokens / ~750-7.5K words): Benefit from on-demand loading to avoid context overhead (this tutorial)
Large skills (> 10K tokens / ~7.5K words, or > 5-10% of context window): Should use progressive disclosure techniques like pagination, search-based loading, or hierarchical exploration to avoid consuming excessive context
The choice depends on your requirements: in-memory is fastest but requires redeployment for skill updates, while file-based or remote storage enables dynamic skill management without code changes.

#### ​Progressive disclosure and context engineering

Combining with few-shot prompting and other techniquesProgressive disclosure is fundamentally a context engineering technique - you’re managing what information is available to the agent and when. This tutorial focused on loading database schemas, but the same principles apply to other types of context.​Combining with few-shot promptingFor the SQL query use case, you could extend progressive disclosure to dynamically load few-shot examples that match the user’s query:Example approach:
User asks: “Find customers who haven’t ordered in 6 months”
Agent loads sales_analytics schema (as shown in this tutorial)
Agent also loads 2-3 relevant example queries (via semantic search or tag-based lookup):

Query for finding inactive customers
Query with date-based filtering
Query joining customers and orders tables

Agent writes query using both schema knowledge AND example patterns
This combination of progressive disclosure (loading schemas on-demand) and dynamic few-shot prompting (loading relevant examples) creates a powerful context engineering pattern that scales to large knowledge bases while providing high-quality, grounded outputs.

​Next steps

- Learn about middleware for more dynamic agent behaviors
- Explore context engineering techniques for managing agent context
- Explore the handoffs pattern for sequential workflows
- Read the subagents pattern for parallel task routing
- See multi-agent patterns for other approaches to specialized agents
- Use LangSmith to debug and monitor skill loading
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.

##### ​Combining with few-shot prompting

For the SQL query use case, you could extend progressive disclosure to dynamically load few-shot examples that match the user’s query:

Example approach:

- User asks: “Find customers who haven’t ordered in 6 months”
- Agent loads sales_analytics schema (as shown in this tutorial)
- Agent also loads 2-3 relevant example queries (via semantic search or tag-based lookup):

Query for finding inactive customers
Query with date-based filtering
Query joining customers and orders tables
- Query for finding inactive customers
- Query with date-based filtering
- Query joining customers and orders tables
- Agent writes query using both schema knowledge AND example patterns
This combination of progressive disclosure (loading schemas on-demand) and dynamic few-shot prompting (loading relevant examples) creates a powerful context engineering pattern that scales to large knowledge bases while providing high-quality, grounded outputs.

#### ​Next steps

- Learn about middleware for more dynamic agent behaviors
- Explore context engineering techniques for managing agent context
- Explore the handoffs pattern for sequential workflows
- Read the subagents pattern for parallel task routing
- See multi-agent patterns for other approaches to specialized agents
- Use LangSmith to debug and monitor skill loading
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Build a multi-source knowledge base with routing - Docs by LangChain {#doc-10}

**Source:** [https://docs.langchain.com/oss/python/langchain/multi-agent/router-knowledge-base](https://docs.langchain.com/oss/python/langchain/multi-agent/router-knowledge-base)

### Build a multi-source knowledge base with routing

Copy page

#### ​Overview

The router pattern is a multi-agent architecture where a routing step classifies input and directs it to specialized agents, with results synthesized into a combined response. This pattern excels when your organization’s knowledge lives across distinct verticals—separate knowledge domains that each require their own agent with specialized tools and prompts.

In this tutorial, you’ll build a multi-source knowledge base router that demonstrates these benefits through a realistic enterprise scenario. The system will coordinate three specialists:

- A GitHub agent that searches code, issues, and pull requests.
- A Notion agent that searches internal documentation and wikis.
- A Slack agent that searches relevant threads and discussions.
When a user asks “How do I authenticate API requests?”, the router decomposes the query into source-specific sub-questions, routes them to the relevant agents in parallel, and synthesizes results into a coherent answer.

##### ​Why use a router?

The router pattern provides several advantages:

- Parallel execution: Query multiple sources simultaneously, reducing latency compared to sequential approaches.
- Specialized agents: Each vertical has focused tools and prompts optimized for its domain.
- Selective routing: Not every query needs every source—the router intelligently selects relevant verticals.
- Targeted sub-questions: Each agent receives a question tailored to its domain, improving result quality.
- Clean synthesis: Results from multiple sources are combined into a single, coherent response.

##### ​Concepts

We will cover the following concepts:

- Multi-agent systems
- StateGraph for workflow orchestration
- Send API for parallel execution
Router vs. Subagents: The subagents pattern can also route to multiple agents. Use the router pattern when you need specialized preprocessing, custom routing logic, or want explicit control over parallel execution. Use the subagents pattern when you want the LLM to decide which agents to call dynamically.

#### ​Setup

##### ​Installation

This tutorial requires the langchain and langgraph packages:

pipuvcondaCopypip install langchain langgraph

For more details, see our Installation guide.

##### ​LangSmith

Set up LangSmith to inspect what is happening inside your agent. Then set the following environment variables:

bashpythonCopyexport LANGSMITH_TRACING="true"
export LANGSMITH_API_KEY="..."

##### ​Select an LLM

Select a chat model from LangChain’s suite of integrations:

OpenAI Anthropic Azure Google Gemini AWS Bedrock HuggingFace👉 Read the OpenAI chat model integration docsCopypip install -U "langchain[openai]"
init_chat_modelModel ClassCopyimport os
```python
from langchain.chat_models import init_chat_model

os.environ["OPENAI_API_KEY"] = "sk-..."

model = init_chat_model("gpt-4.1")
👉 Read the Anthropic chat model integration docsCopypip install -U "langchain[anthropic]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["ANTHROPIC_API_KEY"] = "sk-..."

model = init_chat_model("claude-sonnet-4-5-20250929")
👉 Read the Azure chat model integration docsCopypip install -U "langchain[openai]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["AZURE_OPENAI_API_KEY"] = "..."
os.environ["AZURE_OPENAI_ENDPOINT"] = "..."
os.environ["OPENAI_API_VERSION"] = "2025-03-01-preview"

model = init_chat_model(
    "azure_openai:gpt-4.1",
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
)
👉 Read the Google GenAI chat model integration docsCopypip install -U "langchain[google-genai]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["GOOGLE_API_KEY"] = "..."

model = init_chat_model("google_genai:gemini-2.5-flash-lite")
👉 Read the AWS Bedrock chat model integration docsCopypip install -U "langchain[aws]"
init_chat_modelModel ClassCopyfrom langchain.chat_models import init_chat_model

# Follow the steps here to configure your credentials:
# https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html

model = init_chat_model(
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
    model_provider="bedrock_converse",
)
👉 Read the HuggingFace chat model integration docsCopypip install -U "langchain[huggingface]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["HUGGINGFACEHUB_API_TOKEN"] = "hf_..."

model = init_chat_model(
    "microsoft/Phi-3-mini-4k-instruct",
    model_provider="huggingface",
    temperature=0.7,
    max_tokens=1024,
)
```

#### ​1. Define state

First, define the state schemas. We use three types:

- AgentInput: Simple state passed to each subagent (just a query)
- AgentOutput: Result returned by each subagent (source name + result)
- RouterState: Main workflow state tracking the query, classifications, results, and final answer
Copyfrom typing import Annotated, Literal, TypedDict
```python
import operator

class AgentInput(TypedDict):
    """Simple input state for each subagent."""
    query: str

class AgentOutput(TypedDict):
    """Output from each subagent."""
    source: str
    result: str

class Classification(TypedDict):
    """A single routing decision: which agent to call with what query."""
    source: Literal["github", "notion", "slack"]
    query: str

class RouterState(TypedDict):
    query: str
    classifications: list[Classification]
    results: Annotated[list[AgentOutput], operator.add]  # Reducer collects parallel results
    final_answer: str

The results field uses a reducer (operator.add in Python, a concat function in JS) to collect outputs from parallel agent executions into a single list.
```

#### ​2. Define tools for each vertical

Create tools for each knowledge domain. In a production system, these would call actual APIs. For this tutorial, we use stub implementations that return mock data. We define 7 tools across 3 verticals: GitHub (search code, issues, PRs), Notion (search docs, get page), and Slack (search messages, get thread).

Copyfrom langchain.tools import tool

```python
@tool
def search_code(query: str, repo: str = "main") -> str:
    """Search code in GitHub repositories."""
    return f"Found code matching '{query}' in {repo}: authentication middleware in src/auth.py"

@tool
def search_issues(query: str) -> str:
    """Search GitHub issues and pull requests."""
    return f"Found 3 issues matching '{query}': #142 (API auth docs), #89 (OAuth flow), #203 (token refresh)"

@tool
def search_prs(query: str) -> str:
    """Search pull requests for implementation details."""
    return f"PR #156 added JWT authentication, PR #178 updated OAuth scopes"

@tool
def search_notion(query: str) -> str:
    """Search Notion workspace for documentation."""
    return f"Found documentation: 'API Authentication Guide' - covers OAuth2 flow, API keys, and JWT tokens"

@tool
def get_page(page_id: str) -> str:
    """Get a specific Notion page by ID."""
    return f"Page content: Step-by-step authentication setup instructions"

@tool
def search_slack(query: str) -> str:
    """Search Slack messages and threads."""
    return f"Found discussion in #engineering: 'Use Bearer tokens for API auth, see docs for refresh flow'"

@tool
def get_thread(thread_id: str) -> str:
    """Get a specific Slack thread."""
    return f"Thread discusses best practices for API key rotation"
See all 43 lines
```

#### ​3. Create specialized agents

Create an agent for each vertical. Each agent has domain-specific tools and a prompt optimized for its knowledge source. All three follow the same pattern—only the tools and system prompt differ.

Copyfrom langchain.agents import create_agent
```python
from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-4o")

github_agent = create_agent(
    model,
    tools=[search_code, search_issues, search_prs],
    system_prompt=(
        "You are a GitHub expert. Answer questions about code, "
        "API references, and implementation details by searching "
        "repositories, issues, and pull requests."
    ),
)

notion_agent = create_agent(
    model,
    tools=[search_notion, get_page],
    system_prompt=(
        "You are a Notion expert. Answer questions about internal "
        "processes, policies, and team documentation by searching "
        "the organization's Notion workspace."
    ),
)

slack_agent = create_agent(
    model,
    tools=[search_slack, get_thread],
    system_prompt=(
        "You are a Slack expert. Answer questions by searching "
        "relevant threads and discussions where team members have "
        "shared knowledge and solutions."
    ),
)
See all 34 lines
```

#### ​4. Build the router workflow

Now build the router workflow using a StateGraph. The workflow has four main steps:

- Classify: Analyze the query and determine which agents to invoke with what sub-questions
- Route: Fan out to selected agents in parallel using Send
- Query agents: Each agent receives a simple AgentInput and returns an AgentOutput
- Synthesize: Combine collected results into a coherent response
Copyfrom pydantic import BaseModel, Field
```python
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

router_llm = init_chat_model("openai:gpt-4o-mini")

# Define structured output schema for the classifier
class ClassificationResult(BaseModel):
    """Result of classifying a user query into agent-specific sub-questions."""
    classifications: list[Classification] = Field(
        description="List of agents to invoke with their targeted sub-questions"
    )

def classify_query(state: RouterState) -> dict:
    """Classify query and determine which agents to invoke."""
    structured_llm = router_llm.with_structured_output(ClassificationResult)

    result = structured_llm.invoke([
        {
            "role": "system",
            "content": """Analyze this query and determine which knowledge bases to consult.
For each relevant source, generate a targeted sub-question optimized for that source.

Available sources:
- github: Code, API references, implementation details, issues, pull requests
- notion: Internal documentation, processes, policies, team wikis
- slack: Team discussions, informal knowledge sharing, recent conversations

Return ONLY the sources that are relevant to the query. Each source should have
a targeted sub-question optimized for that specific knowledge domain.

Example for "How do I authenticate API requests?":
- github: "What authentication code exists? Search for auth middleware, JWT handling"
- notion: "What authentication documentation exists? Look for API auth guides"
(slack omitted because it's not relevant for this technical question)"""
        },
        {"role": "user", "content": state["query"]}
    ])

    return {"classifications": result.classifications}

def route_to_agents(state: RouterState) -> list[Send]:
    """Fan out to agents based on classifications."""
    return [
        Send(c["source"], {"query": c["query"]})
        for c in state["classifications"]
    ]

def query_github(state: AgentInput) -> dict:
    """Query the GitHub agent."""
    result = github_agent.invoke({
        "messages": [{"role": "user", "content": state["query"]}]
    })
    return {"results": [{"source": "github", "result": result["messages"][-1].content}]}

def query_notion(state: AgentInput) -> dict:
    """Query the Notion agent."""
    result = notion_agent.invoke({
        "messages": [{"role": "user", "content": state["query"]}]
    })
    return {"results": [{"source": "notion", "result": result["messages"][-1].content}]}

def query_slack(state: AgentInput) -> dict:
    """Query the Slack agent."""
    result = slack_agent.invoke({
        "messages": [{"role": "user", "content": state["query"]}]
    })
    return {"results": [{"source": "slack", "result": result["messages"][-1].content}]}

def synthesize_results(state: RouterState) -> dict:
    """Combine results from all agents into a coherent answer."""
    if not state["results"]:
        return {"final_answer": "No results found from any knowledge source."}

    # Format results for synthesis
    formatted = [
        f"**From {r['source'].title()}:**\n{r['result']}"
        for r in state["results"]
    ]

    synthesis_response = router_llm.invoke([
        {
            "role": "system",
            "content": f"""Synthesize these search results to answer the original question: "{state['query']}"

- Combine information from multiple sources without redundancy
- Highlight the most relevant and actionable information
- Note any discrepancies between sources
- Keep the response concise and well-organized"""
        },
        {"role": "user", "content": "\n\n".join(formatted)}
    ])

    return {"final_answer": synthesis_response.content}
```

#### ​5. Compile the workflow

Now assemble the workflow by connecting nodes with edges. The key is using add_conditional_edges with the routing function to enable parallel execution:

Copyworkflow = (
    StateGraph(RouterState)
    .add_node("classify", classify_query)
    .add_node("github", query_github)
    .add_node("notion", query_notion)
    .add_node("slack", query_slack)
    .add_node("synthesize", synthesize_results)
    .add_edge(START, "classify")
    .add_conditional_edges("classify", route_to_agents, ["github", "notion", "slack"])
    .add_edge("github", "synthesize")
    .add_edge("notion", "synthesize")
    .add_edge("slack", "synthesize")
    .add_edge("synthesize", END)
    .compile()
)

The add_conditional_edges call connects the classify node to the agent nodes through the route_to_agents function. When route_to_agents returns multiple Send objects, those nodes execute in parallel.

#### ​6. Use the router

Test your router with queries that span multiple knowledge domains:

```
Copyresult = workflow.invoke({
    "query": "How do I authenticate API requests?"
})

print("Original query:", result["query"])
print("\nClassifications:")
for c in result["classifications"]:
    print(f"  {c['source']}: {c['query']}")
print("\n" + "=" * 60 + "\n")
print("Final Answer:")
print(result["final_answer"])

Expected output:

CopyOriginal query: How do I authenticate API requests?

Classifications:
  github: What authentication code exists? Search for auth middleware, JWT handling
  notion: What authentication documentation exists? Look for API auth guides

============================================================

Final Answer:
To authenticate API requests, you have several options:

1. **JWT Tokens**: The recommended approach for most use cases.
   Implementation details are in `src/auth.py` (PR #156).

2. **OAuth2 Flow**: For third-party integrations, follow the OAuth2
   flow documented in Notion's 'API Authentication Guide'.

3. **API Keys**: For server-to-server communication, use Bearer tokens
   in the Authorization header.

For token refresh handling, see issue #203 and PR #178 for the latest
OAuth scope updates.

The router analyzed the query, classified it to determine which agents to invoke (GitHub and Notion, but not Slack for this technical question), queried both agents in parallel, and synthesized the results into a coherent answer.
```

#### ​7. Understanding the architecture

The router workflow follows a clear pattern:

##### ​Classification phase

The classify_query function uses structured output to analyze the user’s query and determine which agents to invoke. This is where the routing intelligence lives:

- Uses a Pydantic model (Python) or Zod schema (JS) to ensure valid output
- Returns a list of Classification objects, each with a source and targeted query
- Only includes relevant sources—irrelevant ones are simply omitted
This structured approach is more reliable than free-form JSON parsing and makes the routing logic explicit.

##### ​Parallel execution with Send

The route_to_agents function maps classifications to Send objects. Each Send specifies the target node and the state to pass:

Copy# Classifications: [{"source": "github", "query": "..."}, {"source": "notion", "query": "..."}]
# Becomes:
[Send("github", {"query": "..."}), Send("notion", {"query": "..."})]
# Both agents execute simultaneously, each receiving only the query it needs

Each agent node receives a simple AgentInput with just a query field—not the full router state. This keeps the interface clean and explicit.

##### ​Result collection with reducers

Agent results flow back to the main state via a reducer. Each agent returns:

Copy{"results": [{"source": "github", "result": "..."}]}

The reducer (operator.add in Python) concatenates these lists, collecting all parallel results into state["results"].

##### ​Synthesis phase

After all agents complete, the synthesize_results function iterates over the collected results:

- Waits for all parallel branches to complete (LangGraph handles this automatically)
- References the original query to ensure the answer addresses what the user asked
- Combines information from all sources without redundancy
Partial results: In this tutorial, all selected agents must complete before synthesis. For more advanced patterns where you want to handle partial results or timeouts, see the map-reduce guide.

#### ​8. Complete working example

Here’s everything together in a runnable script:

Show View complete codeCopy"""
Multi-Source Knowledge Router Example

This example demonstrates the router pattern for multi-agent systems.
A router classifies queries, routes them to specialized agents in parallel,
and synthesizes results into a combined response.
"""

```python
import operator
from typing import Annotated, Literal, TypedDict

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from pydantic import BaseModel, Field

# State definitions
class AgentInput(TypedDict):
    """Simple input state for each subagent."""
    query: str

class AgentOutput(TypedDict):
    """Output from each subagent."""
    source: str
    result: str

class Classification(TypedDict):
    """A single routing decision: which agent to call with what query."""
    source: Literal["github", "notion", "slack"]
    query: str

class RouterState(TypedDict):
    query: str
    classifications: list[Classification]
    results: Annotated[list[AgentOutput], operator.add]
    final_answer: str

# Structured output schema for classifier
class ClassificationResult(BaseModel):
    """Result of classifying a user query into agent-specific sub-questions."""
    classifications: list[Classification] = Field(
        description="List of agents to invoke with their targeted sub-questions"
    )

# Tools
@tool
def search_code(query: str, repo: str = "main") -> str:
    """Search code in GitHub repositories."""
    return f"Found code matching '{query}' in {repo}: authentication middleware in src/auth.py"

@tool
def search_issues(query: str) -> str:
    """Search GitHub issues and pull requests."""
    return f"Found 3 issues matching '{query}': #142 (API auth docs), #89 (OAuth flow), #203 (token refresh)"

@tool
def search_prs(query: str) -> str:
    """Search pull requests for implementation details."""
    return f"PR #156 added JWT authentication, PR #178 updated OAuth scopes"

@tool
def search_notion(query: str) -> str:
    """Search Notion workspace for documentation."""
    return f"Found documentation: 'API Authentication Guide' - covers OAuth2 flow, API keys, and JWT tokens"

@tool
def get_page(page_id: str) -> str:
    """Get a specific Notion page by ID."""
    return f"Page content: Step-by-step authentication setup instructions"

@tool
def search_slack(query: str) -> str:
    """Search Slack messages and threads."""
    return f"Found discussion in #engineering: 'Use Bearer tokens for API auth, see docs for refresh flow'"

@tool
def get_thread(thread_id: str) -> str:
    """Get a specific Slack thread."""
    return f"Thread discusses best practices for API key rotation"

# Models and agents
model = init_chat_model("openai:gpt-4o")
router_llm = init_chat_model("openai:gpt-4o-mini")

github_agent = create_agent(
    model,
    tools=[search_code, search_issues, search_prs],
    system_prompt=(
        "You are a GitHub expert. Answer questions about code, "
        "API references, and implementation details by searching "
        "repositories, issues, and pull requests."
    ),
)

notion_agent = create_agent(
    model,
    tools=[search_notion, get_page],
    system_prompt=(
        "You are a Notion expert. Answer questions about internal "
        "processes, policies, and team documentation by searching "
        "the organization's Notion workspace."
    ),
)

slack_agent = create_agent(
    model,
    tools=[search_slack, get_thread],
    system_prompt=(
        "You are a Slack expert. Answer questions by searching "
        "relevant threads and discussions where team members have "
        "shared knowledge and solutions."
    ),
)

# Workflow nodes
def classify_query(state: RouterState) -> dict:
    """Classify query and determine which agents to invoke."""
    structured_llm = router_llm.with_structured_output(ClassificationResult)

    result = structured_llm.invoke([
        {
            "role": "system",
            "content": """Analyze this query and determine which knowledge bases to consult.
For each relevant source, generate a targeted sub-question optimized for that source.

Available sources:
- github: Code, API references, implementation details, issues, pull requests
- notion: Internal documentation, processes, policies, team wikis
- slack: Team discussions, informal knowledge sharing, recent conversations

Return ONLY the sources that are relevant to the query."""
        },
        {"role": "user", "content": state["query"]}
    ])

    return {"classifications": result.classifications}

def route_to_agents(state: RouterState) -> list[Send]:
    """Fan out to agents based on classifications."""
    return [
        Send(c["source"], {"query": c["query"]})
        for c in state["classifications"]
    ]

def query_github(state: AgentInput) -> dict:
    """Query the GitHub agent."""
    result = github_agent.invoke({
        "messages": [{"role": "user", "content": state["query"]}]
    })
    return {"results": [{"source": "github", "result": result["messages"][-1].content}]}

def query_notion(state: AgentInput) -> dict:
    """Query the Notion agent."""
    result = notion_agent.invoke({
        "messages": [{"role": "user", "content": state["query"]}]
    })
    return {"results": [{"source": "notion", "result": result["messages"][-1].content}]}

def query_slack(state: AgentInput) -> dict:
    """Query the Slack agent."""
    result = slack_agent.invoke({
        "messages": [{"role": "user", "content": state["query"]}]
    })
    return {"results": [{"source": "slack", "result": result["messages"][-1].content}]}

def synthesize_results(state: RouterState) -> dict:
    """Combine results from all agents into a coherent answer."""
    if not state["results"]:
        return {"final_answer": "No results found from any knowledge source."}

    formatted = [
        f"**From {r['source'].title()}:**\n{r['result']}"
        for r in state["results"]
    ]

    synthesis_response = router_llm.invoke([
        {
            "role": "system",
            "content": f"""Synthesize these search results to answer the original question: "{state['query']}"

- Combine information from multiple sources without redundancy
- Highlight the most relevant and actionable information
- Note any discrepancies between sources
- Keep the response concise and well-organized"""
        },
        {"role": "user", "content": "\n\n".join(formatted)}
    ])

    return {"final_answer": synthesis_response.content}

# Build workflow
workflow = (
    StateGraph(RouterState)
    .add_node("classify", classify_query)
    .add_node("github", query_github)
    .add_node("notion", query_notion)
    .add_node("slack", query_slack)
    .add_node("synthesize", synthesize_results)
    .add_edge(START, "classify")
    .add_conditional_edges("classify", route_to_agents, ["github", "notion", "slack"])
    .add_edge("github", "synthesize")
    .add_edge("notion", "synthesize")
    .add_edge("slack", "synthesize")
    .add_edge("synthesize", END)
    .compile()
)

if __name__ == "__main__":
    result = workflow.invoke({
        "query": "How do I authenticate API requests?"
    })

    print("Original query:", result["query"])
    print("\nClassifications:")
    for c in result["classifications"]:
        print(f"  {c['source']}: {c['query']}")
    print("\n" + "=" * 60 + "\n")
    print("Final Answer:")
    print(result["final_answer"])
```

#### ​9. Advanced: Stateful routers

The router we’ve built so far is stateless—each request is handled independently with no memory between calls. For multi-turn conversations, you need a stateful approach.

##### ​Tool wrapper approach

The simplest way to add conversation memory is to wrap the stateless router as a tool that a conversational agent can call:

Copyfrom langgraph.checkpoint.memory import InMemorySaver

```python
@tool
def search_knowledge_base(query: str) -> str:
    """Search across multiple knowledge sources (GitHub, Notion, Slack).

    Use this to find information about code, documentation, or team discussions.
    """
    result = workflow.invoke({"query": query})
    return result["final_answer"]

conversational_agent = create_agent(
    model,
    tools=[search_knowledge_base],
    system_prompt=(
        "You are a helpful assistant that answers questions about our organization. "
        "Use the search_knowledge_base tool to find information across our code, "
        "documentation, and team discussions."
    ),
    checkpointer=InMemorySaver(),
)

This approach keeps the router stateless while the conversational agent handles memory and context. The user can have a multi-turn conversation, and the agent will call the router tool as needed.

Copyconfig = {"configurable": {"thread_id": "user-123"}}

result = conversational_agent.invoke(
    {"messages": [{"role": "user", "content": "How do I authenticate API requests?"}]},
    config
)
print(result["messages"][-1].content)

result = conversational_agent.invoke(
    {"messages": [{"role": "user", "content": "What about rate limiting for those endpoints?"}]},
    config
)
print(result["messages"][-1].content)

The tool wrapper approach is recommended for most use cases. It provides clean separation: the router handles multi-source querying, while the conversational agent handles context and memory.
```

##### ​Full persistence approach

If you need the router itself to maintain state—for example, to use previous search results in routing decisions—use persistence to store message history at the router level.

Stateful routers add complexity. When routing to different agents across turns, conversations may feel inconsistent if agents have different tones or prompts. Consider the handoffs pattern or subagents pattern instead—both provide clearer semantics for multi-turn conversations with different agents.

#### ​10. Key takeaways

The router pattern excels when you have:

- Distinct verticals: Separate knowledge domains that each require specialized tools and prompts
- Parallel query needs: Questions that benefit from querying multiple sources simultaneously
- Synthesis requirements: Results from multiple sources need to be combined into a coherent response
The pattern has three phases: decompose (analyze the query and generate targeted sub-questions), route (execute queries in parallel), and synthesize (combine results).

When to use the router patternUse the router pattern when you have multiple independent knowledge sources, need low-latency parallel queries, and want explicit control over routing logic.For simpler cases with dynamic tool selection, consider the subagents pattern. For workflows where agents need to converse with users sequentially, consider handoffs.

#### ​Next steps

- Learn about handoffs for agent-to-agent conversations
- Explore the subagents pattern for centralized orchestration
- Read the multi-agent overview to compare different patterns
- Use LangSmith to debug and monitor your router
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Build customer support with handoffs - Docs by LangChain {#doc-11}

**Source:** [https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs-customer-support](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs-customer-support)

### Build customer support with handoffs

Copy page

#### ​Setup

##### ​Installation

This tutorial requires the langchain package:

pipuvcondaCopypip install langchain

For more details, see our Installation guide.

##### ​LangSmith

Set up LangSmith to inspect what is happening inside your agent. Then set the following environment variables:

bashpythonCopyexport LANGSMITH_TRACING="true"
export LANGSMITH_API_KEY="..."

##### ​Select an LLM

Select a chat model from LangChain’s suite of integrations:

OpenAI Anthropic Azure Google Gemini AWS Bedrock HuggingFace👉 Read the OpenAI chat model integration docsCopypip install -U "langchain[openai]"
init_chat_modelModel ClassCopyimport os
```python
from langchain.chat_models import init_chat_model

os.environ["OPENAI_API_KEY"] = "sk-..."

model = init_chat_model("gpt-4.1")
👉 Read the Anthropic chat model integration docsCopypip install -U "langchain[anthropic]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["ANTHROPIC_API_KEY"] = "sk-..."

model = init_chat_model("claude-sonnet-4-5-20250929")
👉 Read the Azure chat model integration docsCopypip install -U "langchain[openai]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["AZURE_OPENAI_API_KEY"] = "..."
os.environ["AZURE_OPENAI_ENDPOINT"] = "..."
os.environ["OPENAI_API_VERSION"] = "2025-03-01-preview"

model = init_chat_model(
    "azure_openai:gpt-4.1",
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
)
👉 Read the Google GenAI chat model integration docsCopypip install -U "langchain[google-genai]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["GOOGLE_API_KEY"] = "..."

model = init_chat_model("google_genai:gemini-2.5-flash-lite")
👉 Read the AWS Bedrock chat model integration docsCopypip install -U "langchain[aws]"
init_chat_modelModel ClassCopyfrom langchain.chat_models import init_chat_model

# Follow the steps here to configure your credentials:
# https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html

model = init_chat_model(
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
    model_provider="bedrock_converse",
)
👉 Read the HuggingFace chat model integration docsCopypip install -U "langchain[huggingface]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["HUGGINGFACEHUB_API_TOKEN"] = "hf_..."

model = init_chat_model(
    "microsoft/Phi-3-mini-4k-instruct",
    model_provider="huggingface",
    temperature=0.7,
    max_tokens=1024,
)
```

#### ​1. Define custom state

First, define a custom state schema that tracks which step is currently active:

Copyfrom langchain.agents import AgentState
```python
from typing_extensions import NotRequired
from typing import Literal

# Define the possible workflow steps
SupportStep = Literal["warranty_collector", "issue_classifier", "resolution_specialist"]

class SupportState(AgentState):
    """State for customer support workflow."""
    current_step: NotRequired[SupportStep]
    warranty_status: NotRequired[Literal["in_warranty", "out_of_warranty"]]
    issue_type: NotRequired[Literal["hardware", "software"]]

The current_step field is the core of the state machine pattern - it determines which configuration (prompt + tools) is loaded on each turn.
```

#### ​2. Create tools that manage workflow state

Create tools that update the workflow state. These tools allow the agent to record information and transition to the next step.

The key is using Command to update state, including the current_step field:

Copyfrom langchain.tools import tool, ToolRuntime
```python
from langchain.messages import ToolMessage
from langgraph.types import Command

@tool
def record_warranty_status(
    status: Literal["in_warranty", "out_of_warranty"],
    runtime: ToolRuntime[None, SupportState],
) -> Command:
    """Record the customer's warranty status and transition to issue classification."""
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"Warranty status recorded as: {status}",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
            "warranty_status": status,
            "current_step": "issue_classifier",
        }
    )

@tool
def record_issue_type(
    issue_type: Literal["hardware", "software"],
    runtime: ToolRuntime[None, SupportState],
) -> Command:
    """Record the type of issue and transition to resolution specialist."""
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"Issue type recorded as: {issue_type}",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
            "issue_type": issue_type,
            "current_step": "resolution_specialist",
        }
    )

@tool
def escalate_to_human(reason: str) -> str:
    """Escalate the case to a human support specialist."""
    # In a real system, this would create a ticket, notify staff, etc.
    return f"Escalating to human support. Reason: {reason}"

@tool
def provide_solution(solution: str) -> str:
    """Provide a solution to the customer's issue."""
    return f"Solution provided: {solution}"

Notice how record_warranty_status and record_issue_type return Command objects that update both the data (warranty_status, issue_type) AND the current_step. This is how the state machine works - tools control workflow progression.
```

#### ​3. Define step configurations

Define prompts and tools for each step. First, define the prompts for each step:

View complete prompt definitionsCopy# Define prompts as constants for easy reference
WARRANTY_COLLECTOR_PROMPT = """You are a customer support agent helping with device issues.

CURRENT STAGE: Warranty verification

At this step, you need to:
1. Greet the customer warmly
2. Ask if their device is under warranty
3. Use record_warranty_status to record their response and move to the next step

Be conversational and friendly. Don't ask multiple questions at once."""

ISSUE_CLASSIFIER_PROMPT = """You are a customer support agent helping with device issues.

CURRENT STAGE: Issue classification
CUSTOMER INFO: Warranty status is {warranty_status}

At this step, you need to:
1. Ask the customer to describe their issue
2. Determine if it's a hardware issue (physical damage, broken parts) or software issue (app crashes, performance)
3. Use record_issue_type to record the classification and move to the next step

If unclear, ask clarifying questions before classifying."""

RESOLUTION_SPECIALIST_PROMPT = """You are a customer support agent helping with device issues.

CURRENT STAGE: Resolution
CUSTOMER INFO: Warranty status is {warranty_status}, issue type is {issue_type}

At this step, you need to:
1. For SOFTWARE issues: provide troubleshooting steps using provide_solution
2. For HARDWARE issues:
   - If IN WARRANTY: explain warranty repair process using provide_solution
   - If OUT OF WARRANTY: escalate_to_human for paid repair options

Be specific and helpful in your solutions."""

Then map step names to their configurations using a dictionary:

Copy# Step configuration: maps step name to (prompt, tools, required_state)
```
STEP_CONFIG = {
    "warranty_collector": {
        "prompt": WARRANTY_COLLECTOR_PROMPT,
        "tools": [record_warranty_status],
        "requires": [],
    },
    "issue_classifier": {
        "prompt": ISSUE_CLASSIFIER_PROMPT,
        "tools": [record_issue_type],
        "requires": ["warranty_status"],
    },
    "resolution_specialist": {
        "prompt": RESOLUTION_SPECIALIST_PROMPT,
        "tools": [provide_solution, escalate_to_human],
        "requires": ["warranty_status", "issue_type"],
    },
}

This dictionary-based configuration makes it easy to:

- See all steps at a glance
- Add new steps (just add another entry)
- Understand the workflow dependencies (requires field)
- Use prompt templates with state variables (e.g., {warranty_status})
```

#### ​4. Create step-based middleware

Create middleware that reads current_step from state and applies the appropriate configuration. We’ll use the @wrap_model_call decorator for a clean implementation:

Copyfrom langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
```python
from typing import Callable

@wrap_model_call
def apply_step_config(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """Configure agent behavior based on the current step."""
    # Get current step (defaults to warranty_collector for first interaction)
    current_step = request.state.get("current_step", "warranty_collector")

    # Look up step configuration
    stage_config = STEP_CONFIG[current_step]

    # Validate required state exists
    for key in stage_config["requires"]:
        if request.state.get(key) is None:
            raise ValueError(f"{key} must be set before reaching {current_step}")

    # Format prompt with state values (supports {warranty_status}, {issue_type}, etc.)
    system_prompt = stage_config["prompt"].format(**request.state)

    # Inject system prompt and step-specific tools
    request = request.override(
        system_prompt=system_prompt,
        tools=stage_config["tools"],
    )

    return handler(request)

This middleware:

- Reads current step: Gets current_step from state (defaults to “warranty_collector”).
- Looks up configuration: Finds the matching entry in STEP_CONFIG.
- Validates dependencies: Ensures required state fields exist.
- Formats prompt: Injects state values into the prompt template.
- Applies configuration: Overrides the system prompt and available tools.
The request.override() method is key - it allows us to dynamically change the agent’s behavior based on state without creating separate agent instances.
```

#### ​5. Create the agent

Now create the agent with the step-based middleware and a checkpointer for state persistence:

Copyfrom langchain.agents import create_agent
```python
from langgraph.checkpoint.memory import InMemorySaver

# Collect all tools from all step configurations
all_tools = [
    record_warranty_status,
    record_issue_type,
    provide_solution,
    escalate_to_human,
]

# Create the agent with step-based configuration
agent = create_agent(
    model,
    tools=all_tools,
    state_schema=SupportState,
    middleware=[apply_step_config],
    checkpointer=InMemorySaver(),
)

Why a checkpointer? The checkpointer maintains state across conversation turns. Without it, the current_step state would be lost between user messages, breaking the workflow.
```

#### ​6. Test the workflow

Test the complete workflow:

Copyfrom langchain.messages import HumanMessage
```python
import uuid

# Configuration for this conversation thread
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

# Turn 1: Initial message - starts with warranty_collector step
print("=== Turn 1: Warranty Collection ===")
result = agent.invoke(
    {"messages": [HumanMessage("Hi, my phone screen is cracked")]},
    config
)
for msg in result['messages']:
    msg.pretty_print()

# Turn 2: User responds about warranty
print("\n=== Turn 2: Warranty Response ===")
result = agent.invoke(
    {"messages": [HumanMessage("Yes, it's still under warranty")]},
    config
)
for msg in result['messages']:
    msg.pretty_print()
print(f"Current step: {result.get('current_step')}")

# Turn 3: User describes the issue
print("\n=== Turn 3: Issue Description ===")
result = agent.invoke(
    {"messages": [HumanMessage("The screen is physically cracked from dropping it")]},
    config
)
for msg in result['messages']:
    msg.pretty_print()
print(f"Current step: {result.get('current_step')}")

# Turn 4: Resolution
print("\n=== Turn 4: Resolution ===")
result = agent.invoke(
    {"messages": [HumanMessage("What should I do?")]},
    config
)
for msg in result['messages']:
    msg.pretty_print()

Expected flow:

- Warranty verification step: Asks about warranty status
- Issue classification step: Asks about the problem, determines it’s hardware
- Resolution step: Provides warranty repair instructions
```

#### ​7. Understanding state transitions

Let’s trace what happens at each turn:

##### ​Turn 1: Initial message

```
Copy{
    "messages": [HumanMessage("Hi, my phone screen is cracked")],
    "current_step": "warranty_collector"  # Default value
}

Middleware applies:

- System prompt: WARRANTY_COLLECTOR_PROMPT
- Tools: [record_warranty_status]
```

##### ​Turn 2: After warranty recorded

Tool call: record_warranty_status("in_warranty") returns:

```
CopyCommand(update={
    "warranty_status": "in_warranty",
    "current_step": "issue_classifier"  # State transition!
})

Next turn, middleware applies:

- System prompt: ISSUE_CLASSIFIER_PROMPT (formatted with warranty_status="in_warranty")
- Tools: [record_issue_type]
```

##### ​Turn 3: After issue classified

Tool call: record_issue_type("hardware") returns:

```
CopyCommand(update={
    "issue_type": "hardware",
    "current_step": "resolution_specialist"  # State transition!
})

Next turn, middleware applies:

- System prompt: RESOLUTION_SPECIALIST_PROMPT (formatted with warranty_status and issue_type)
- Tools: [provide_solution, escalate_to_human]
The key insight: Tools drive the workflow by updating current_step, and middleware responds by applying the appropriate configuration on the next turn.
```

#### ​8. Manage message history

As the agent progresses through steps, message history grows. Use summarization middleware to compress earlier messages while preserving conversational context:

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model,
    tools=all_tools,
    state_schema=SupportState,
    middleware=[
        apply_step_config,
        SummarizationMiddleware(
            model="gpt-4o-mini",
            trigger=("tokens", 4000),
            keep=("messages", 10)
        )
    ],
    checkpointer=InMemorySaver(),
)

See the short-term memory guide for other memory management techniques.
```

#### ​9. Add flexibility: Go back

Some workflows need to allow users to return to previous steps to correct information (e.g., changing warranty status or issue classification). However, not all transitions make sense—for example, you typically can’t go back once a refund has been processed. For this support workflow, we’ll add tools to return to the warranty verification and issue classification steps.

If your workflow requires arbitrary transitions between most steps, consider whether you need a structured workflow at all. This pattern works best when steps follow a clear sequential progression with occasional backwards transitions for corrections.

Add “go back” tools to the resolution step:

Copy@tool
```python
def go_back_to_warranty() -> Command:
    """Go back to warranty verification step."""
    return Command(update={"current_step": "warranty_collector"})

@tool
def go_back_to_classification() -> Command:
    """Go back to issue classification step."""
    return Command(update={"current_step": "issue_classifier"})

# Update the resolution_specialist configuration to include these tools
STEP_CONFIG["resolution_specialist"]["tools"].extend([
    go_back_to_warranty,
    go_back_to_classification
])

Update the resolution specialist’s prompt to mention these tools:

CopyRESOLUTION_SPECIALIST_PROMPT = """You are a customer support agent helping with device issues.

CURRENT STAGE: Resolution
CUSTOMER INFO: Warranty status is {warranty_status}, issue type is {issue_type}

At this step, you need to:
1. For SOFTWARE issues: provide troubleshooting steps using provide_solution
2. For HARDWARE issues:
   - If IN WARRANTY: explain warranty repair process using provide_solution
   - If OUT OF WARRANTY: escalate_to_human for paid repair options

If the customer indicates any information was wrong, use:
- go_back_to_warranty to correct warranty status
- go_back_to_classification to correct issue type

Be specific and helpful in your solutions."""

Now the agent can handle corrections:

Copyresult = agent.invoke(
    {"messages": [HumanMessage("Actually, I made a mistake - my device is out of warranty")]},
    config
)
# Agent will call go_back_to_warranty and restart the warranty verification step
```

#### ​Complete example

Here’s everything together in a runnable script:

Show Complete codeCopy"""
Customer Support State Machine Example

This example demonstrates the state machine pattern.
A single agent dynamically changes its behavior based on the current_step state,
creating a state machine for sequential information collection.
"""

```python
import uuid

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from typing import Callable, Literal
from typing_extensions import NotRequired

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse, SummarizationMiddleware
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, ToolMessage
from langchain.tools import tool, ToolRuntime

model = init_chat_model("anthropic:claude-3-5-sonnet-latest")

# Define the possible workflow steps
SupportStep = Literal["warranty_collector", "issue_classifier", "resolution_specialist"]

class SupportState(AgentState):
    """State for customer support workflow."""

    current_step: NotRequired[SupportStep]
    warranty_status: NotRequired[Literal["in_warranty", "out_of_warranty"]]
    issue_type: NotRequired[Literal["hardware", "software"]]

@tool
def record_warranty_status(
    status: Literal["in_warranty", "out_of_warranty"],
    runtime: ToolRuntime[None, SupportState],
) -> Command:
    """Record the customer's warranty status and transition to issue classification."""
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"Warranty status recorded as: {status}",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
            "warranty_status": status,
            "current_step": "issue_classifier",
        }
    )

@tool
def record_issue_type(
    issue_type: Literal["hardware", "software"],
    runtime: ToolRuntime[None, SupportState],
) -> Command:
    """Record the type of issue and transition to resolution specialist."""
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"Issue type recorded as: {issue_type}",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
            "issue_type": issue_type,
            "current_step": "resolution_specialist",
        }
    )

@tool
def escalate_to_human(reason: str) -> str:
    """Escalate the case to a human support specialist."""
    # In a real system, this would create a ticket, notify staff, etc.
    return f"Escalating to human support. Reason: {reason}"

@tool
def provide_solution(solution: str) -> str:
    """Provide a solution to the customer's issue."""
    return f"Solution provided: {solution}"

# Define prompts as constants
WARRANTY_COLLECTOR_PROMPT = """You are a customer support agent helping with device issues.

CURRENT STEP: Warranty verification

At this step, you need to:
1. Greet the customer warmly
2. Ask if their device is under warranty
3. Use record_warranty_status to record their response and move to the next step

Be conversational and friendly. Don't ask multiple questions at once."""

ISSUE_CLASSIFIER_PROMPT = """You are a customer support agent helping with device issues.

CURRENT STEP: Issue classification
CUSTOMER INFO: Warranty status is {warranty_status}

At this step, you need to:
1. Ask the customer to describe their issue
2. Determine if it's a hardware issue (physical damage, broken parts) or software issue (app crashes, performance)
3. Use record_issue_type to record the classification and move to the next step

If unclear, ask clarifying questions before classifying."""

RESOLUTION_SPECIALIST_PROMPT = """You are a customer support agent helping with device issues.

CURRENT STEP: Resolution
CUSTOMER INFO: Warranty status is {warranty_status}, issue type is {issue_type}

At this step, you need to:
1. For SOFTWARE issues: provide troubleshooting steps using provide_solution
2. For HARDWARE issues:
   - If IN WARRANTY: explain warranty repair process using provide_solution
   - If OUT OF WARRANTY: escalate_to_human for paid repair options

Be specific and helpful in your solutions."""

# Step configuration: maps step name to (prompt, tools, required_state)
STEP_CONFIG = {
    "warranty_collector": {
        "prompt": WARRANTY_COLLECTOR_PROMPT,
        "tools": [record_warranty_status],
        "requires": [],
    },
    "issue_classifier": {
        "prompt": ISSUE_CLASSIFIER_PROMPT,
        "tools": [record_issue_type],
        "requires": ["warranty_status"],
    },
    "resolution_specialist": {
        "prompt": RESOLUTION_SPECIALIST_PROMPT,
        "tools": [provide_solution, escalate_to_human],
        "requires": ["warranty_status", "issue_type"],
    },
}

@wrap_model_call
def apply_step_config(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """Configure agent behavior based on the current step."""
    # Get current step (defaults to warranty_collector for first interaction)
    current_step = request.state.get("current_step", "warranty_collector")

    # Look up step configuration
    step_config = STEP_CONFIG[current_step]

    # Validate required state exists
    for key in step_config["requires"]:
        if request.state.get(key) is None:
            raise ValueError(f"{key} must be set before reaching {current_step}")

    # Format prompt with state values
    system_prompt = step_config["prompt"].format(**request.state)

    # Inject system prompt and step-specific tools
    request = request.override(
        system_prompt=system_prompt,
        tools=step_config["tools"],
    )

    return handler(request)

# Collect all tools from all step configurations
all_tools = [
    record_warranty_status,
    record_issue_type,
    provide_solution,
    escalate_to_human,
]

# Create the agent with step-based configuration and summarization
agent = create_agent(
    model,
    tools=all_tools,
    state_schema=SupportState,
    middleware=[
        apply_step_config,
        SummarizationMiddleware(
            model="gpt-4o-mini",
            trigger=("tokens", 4000),
            keep=("messages", 10)
        )
    ],
    checkpointer=InMemorySaver(),
)

# ============================================================================
# Test the workflow
# ============================================================================

if __name__ == "__main__":
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    result = agent.invoke(
        {"messages": [HumanMessage("Hi, my phone screen is cracked")]},
        config
    )

    result = agent.invoke(
        {"messages": [HumanMessage("Yes, it's still under warranty")]},
        config
    )

    result = agent.invoke(
        {"messages": [HumanMessage("The screen is physically cracked from dropping it")]},
        config
    )

    result = agent.invoke(
        {"messages": [HumanMessage("What should I do?")]},
        config
    )
    for msg in result['messages']:
        msg.pretty_print()
```

#### ​Next steps

- Learn about the subagents pattern for centralized orchestration
- Explore middleware for more dynamic behaviors
- Read the multi-agent overview to compare patterns
- Use LangSmith to debug and monitor your multi-agent system
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Build a personal assistant with subagents - Docs by LangChain {#doc-12}

**Source:** [https://docs.langchain.com/oss/python/langchain/multi-agent/subagents-personal-assistant](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents-personal-assistant)

### Build a personal assistant with subagents

Copy page

#### ​Overview

The supervisor pattern is a multi-agent architecture where a central supervisor agent coordinates specialized worker agents. This approach excels when tasks require different types of expertise. Rather than building one agent that manages tool selection across domains, you create focused specialists coordinated by a supervisor who understands the overall workflow.

In this tutorial, you’ll build a personal assistant system that demonstrates these benefits through a realistic workflow. The system will coordinate two specialists with fundamentally different responsibilities:

- A calendar agent that handles scheduling, availability checking, and event management.
- An email agent that manages communication, drafts messages, and sends notifications.
We will also incorporate human-in-the-loop review to allow users to approve, edit, and reject actions (such as outbound emails) as desired.

##### ​Why use a supervisor?

Multi-agent architectures allow you to partition tools across workers, each with their own individual prompts or instructions. Consider an agent with direct access to all calendar and email APIs: it must choose from many similar tools, understand exact formats for each API, and handle multiple domains simultaneously. If performance degrades, it may be helpful to separate related tools and associated prompts into logical groups (in part to manage iterative improvements).

##### ​Concepts

We will cover the following concepts:

- Multi-agent systems
- Human-in-the-loop review

#### ​Setup

##### ​Installation

This tutorial requires the langchain package:

pipcondaCopypip install langchain

For more details, see our Installation guide.

##### ​LangSmith

Set up LangSmith to inspect what is happening inside your agent. Then set the following environment variables:

bashpythonCopyexport LANGSMITH_TRACING="true"
export LANGSMITH_API_KEY="..."

##### ​Components

We will need to select a chat model from LangChain’s suite of integrations:

OpenAI Anthropic Azure Google Gemini AWS Bedrock HuggingFace👉 Read the OpenAI chat model integration docsCopypip install -U "langchain[openai]"
init_chat_modelModel ClassCopyimport os
```python
from langchain.chat_models import init_chat_model

os.environ["OPENAI_API_KEY"] = "sk-..."

model = init_chat_model("gpt-4.1")
👉 Read the Anthropic chat model integration docsCopypip install -U "langchain[anthropic]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["ANTHROPIC_API_KEY"] = "sk-..."

model = init_chat_model("claude-sonnet-4-5-20250929")
👉 Read the Azure chat model integration docsCopypip install -U "langchain[openai]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["AZURE_OPENAI_API_KEY"] = "..."
os.environ["AZURE_OPENAI_ENDPOINT"] = "..."
os.environ["OPENAI_API_VERSION"] = "2025-03-01-preview"

model = init_chat_model(
    "azure_openai:gpt-4.1",
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
)
👉 Read the Google GenAI chat model integration docsCopypip install -U "langchain[google-genai]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["GOOGLE_API_KEY"] = "..."

model = init_chat_model("google_genai:gemini-2.5-flash-lite")
👉 Read the AWS Bedrock chat model integration docsCopypip install -U "langchain[aws]"
init_chat_modelModel ClassCopyfrom langchain.chat_models import init_chat_model

# Follow the steps here to configure your credentials:
# https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html

model = init_chat_model(
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
    model_provider="bedrock_converse",
)
👉 Read the HuggingFace chat model integration docsCopypip install -U "langchain[huggingface]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["HUGGINGFACEHUB_API_TOKEN"] = "hf_..."

model = init_chat_model(
    "microsoft/Phi-3-mini-4k-instruct",
    model_provider="huggingface",
    temperature=0.7,
    max_tokens=1024,
)
```

#### ​1. Define tools

Start by defining the tools that require structured inputs. In real applications, these would call actual APIs (Google Calendar, SendGrid, etc.). For this tutorial, you’ll use stubs to demonstrate the pattern.

Copyfrom langchain.tools import tool

```python
@tool
def create_calendar_event(
    title: str,
    start_time: str,       # ISO format: "2024-01-15T14:00:00"
    end_time: str,         # ISO format: "2024-01-15T15:00:00"
    attendees: list[str],  # email addresses
    location: str = ""
) -> str:
    """Create a calendar event. Requires exact ISO datetime format."""
    # Stub: In practice, this would call Google Calendar API, Outlook API, etc.
    return f"Event created: {title} from {start_time} to {end_time} with {len(attendees)} attendees"

@tool
def send_email(
    to: list[str],  # email addresses
    subject: str,
    body: str,
    cc: list[str] = []
) -> str:
    """Send an email via email API. Requires properly formatted addresses."""
    # Stub: In practice, this would call SendGrid, Gmail API, etc.
    return f"Email sent to {', '.join(to)} - Subject: {subject}"

@tool
def get_available_time_slots(
    attendees: list[str],
    date: str,  # ISO format: "2024-01-15"
    duration_minutes: int
) -> list[str]:
    """Check calendar availability for given attendees on a specific date."""
    # Stub: In practice, this would query calendar APIs
    return ["09:00", "14:00", "16:00"]
```

#### ​2. Create specialized sub-agents

Next, we’ll create specialized sub-agents that handle each domain.

##### ​Create a calendar agent

The calendar agent understands natural language scheduling requests and translates them into precise API calls. It handles date parsing, availability checking, and event creation.

Copyfrom langchain.agents import create_agent

CALENDAR_AGENT_PROMPT = (
    "You are a calendar scheduling assistant. "
    "Parse natural language scheduling requests (e.g., 'next Tuesday at 2pm') "
    "into proper ISO datetime formats. "
    "Use get_available_time_slots to check availability when needed. "
    "Use create_calendar_event to schedule events. "
    "Always confirm what was scheduled in your final response."
)

calendar_agent = create_agent(
    model,
    tools=[create_calendar_event, get_available_time_slots],
    system_prompt=CALENDAR_AGENT_PROMPT,
)

Test the calendar agent to see how it handles natural language scheduling:

Copyquery = "Schedule a team meeting next Tuesday at 2pm for 1 hour"

for step in calendar_agent.stream(
    {"messages": [{"role": "user", "content": query}]}
):
    for update in step.values():
        for message in update.get("messages", []):
            message.pretty_print()

Copy================================== Ai Message ==================================
Tool Calls:
  get_available_time_slots (call_EIeoeIi1hE2VmwZSfHStGmXp)
 Call ID: call_EIeoeIi1hE2VmwZSfHStGmXp
  Args:
    attendees: []
    date: 2024-06-18
    duration_minutes: 60
================================= Tool Message =================================
Name: get_available_time_slots

["09:00", "14:00", "16:00"]
================================== Ai Message ==================================
Tool Calls:
  create_calendar_event (call_zgx3iJA66Ut0W8S3NpT93kEB)
 Call ID: call_zgx3iJA66Ut0W8S3NpT93kEB
  Args:
    title: Team Meeting
    start_time: 2024-06-18T14:00:00
    end_time: 2024-06-18T15:00:00
    attendees: []
================================= Tool Message =================================
Name: create_calendar_event

Event created: Team Meeting from 2024-06-18T14:00:00 to 2024-06-18T15:00:00 with 0 attendees
================================== Ai Message ==================================

The team meeting has been scheduled for next Tuesday, June 18th, at 2:00 PM and will last for 1 hour. If you need to add attendees or a location, please let me know!

The agent parses “next Tuesday at 2pm” into ISO format (“2024-01-16T14:00:00”), calculates the end time, calls create_calendar_event, and returns a natural language confirmation.

##### ​Create an email agent

The email agent handles message composition and sending. It focuses on extracting recipient information, crafting appropriate subject lines and body text, and managing email communication.

CopyEMAIL_AGENT_PROMPT = (
    "You are an email assistant. "
    "Compose professional emails based on natural language requests. "
    "Extract recipient information and craft appropriate subject lines and body text. "
    "Use send_email to send the message. "
    "Always confirm what was sent in your final response."
)

email_agent = create_agent(
    model,
    tools=[send_email],
    system_prompt=EMAIL_AGENT_PROMPT,
)

Test the email agent with a natural language request:

Copyquery = "Send the design team a reminder about reviewing the new mockups"

for step in email_agent.stream(
    {"messages": [{"role": "user", "content": query}]}
):
    for update in step.values():
        for message in update.get("messages", []):
            message.pretty_print()

Copy================================== Ai Message ==================================
Tool Calls:
  send_email (call_OMl51FziTVY6CRZvzYfjYOZr)
 Call ID: call_OMl51FziTVY6CRZvzYfjYOZr
  Args:
    to: ['design-team@example.com']
    subject: Reminder: Please Review the New Mockups
    body: Hi Design Team,

This is a friendly reminder to review the new mockups at your earliest convenience. Your feedback is important to ensure that we stay on track with our project timeline.

Please let me know if you have any questions or need additional information.

Thank you!

Best regards,
================================= Tool Message =================================
Name: send_email

Email sent to design-team@example.com - Subject: Reminder: Please Review the New Mockups
================================== Ai Message ==================================

I've sent a reminder to the design team asking them to review the new mockups. If you need any further communication on this topic, just let me know!

The agent infers the recipient from the informal request, crafts a professional subject line and body, calls send_email, and returns a confirmation. Each sub-agent has a narrow focus with domain-specific tools and prompts, allowing it to excel at its specific task.

#### ​3. Wrap sub-agents as tools

Now wrap each sub-agent as a tool that the supervisor can invoke. This is the key architectural step that creates the layered system. The supervisor will see high-level tools like “schedule_event”, not low-level tools like “create_calendar_event”.

Copy@tool
```python
def schedule_event(request: str) -> str:
    """Schedule calendar events using natural language.

    Use this when the user wants to create, modify, or check calendar appointments.
    Handles date/time parsing, availability checking, and event creation.

    Input: Natural language scheduling request (e.g., 'meeting with design team
    next Tuesday at 2pm')
    """
    result = calendar_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text

@tool
def manage_email(request: str) -> str:
    """Send emails using natural language.

    Use this when the user wants to send notifications, reminders, or any email
    communication. Handles recipient extraction, subject generation, and email
    composition.

    Input: Natural language email request (e.g., 'send them a reminder about
    the meeting')
    """
    result = email_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text

The tool descriptions help the supervisor decide when to use each tool, so make them clear and specific. We return only the sub-agent’s final response, as the supervisor doesn’t need to see intermediate reasoning or tool calls.
```

#### ​4. Create the supervisor agent

Now create the supervisor that orchestrates the sub-agents. The supervisor only sees high-level tools and makes routing decisions at the domain level, not the individual API level.

CopySUPERVISOR_PROMPT = (
    "You are a helpful personal assistant. "
    "You can schedule calendar events and send emails. "
    "Break down user requests into appropriate tool calls and coordinate the results. "
    "When a request involves multiple actions, use multiple tools in sequence."
)

supervisor_agent = create_agent(
    model,
    tools=[schedule_event, manage_email],
    system_prompt=SUPERVISOR_PROMPT,
)

#### ​5. Use the supervisor

Now test your complete system with complex requests that require coordination across multiple domains:

##### ​Example 1: Simple single-domain request

Copyquery = "Schedule a team standup for tomorrow at 9am"

for step in supervisor_agent.stream(
    {"messages": [{"role": "user", "content": query}]}
):
    for update in step.values():
        for message in update.get("messages", []):
            message.pretty_print()

Copy================================== Ai Message ==================================
Tool Calls:
  schedule_event (call_mXFJJDU8bKZadNUZPaag8Lct)
 Call ID: call_mXFJJDU8bKZadNUZPaag8Lct
  Args:
    request: Schedule a team standup for tomorrow at 9am with Alice and Bob.
================================= Tool Message =================================
Name: schedule_event

The team standup has been scheduled for tomorrow at 9:00 AM with Alice and Bob. If you need to make any changes or add more details, just let me know!
================================== Ai Message ==================================

The team standup with Alice and Bob is scheduled for tomorrow at 9:00 AM. If you need any further arrangements or adjustments, please let me know!

The supervisor identifies this as a calendar task, calls schedule_event, and the calendar agent handles date parsing and event creation.

For full transparency into the information flow, including prompts and responses for each chat model call, check out the LangSmith trace for the above run.

##### ​Example 2: Complex multi-domain request

Copyquery = (
    "Schedule a meeting with the design team next Tuesday at 2pm for 1 hour, "
    "and send them an email reminder about reviewing the new mockups."
)

for step in supervisor_agent.stream(
    {"messages": [{"role": "user", "content": query}]}
):
    for update in step.values():
        for message in update.get("messages", []):
            message.pretty_print()

Copy================================== Ai Message ==================================
Tool Calls:
  schedule_event (call_YA68mqF0koZItCFPx0kGQfZi)
 Call ID: call_YA68mqF0koZItCFPx0kGQfZi
  Args:
    request: meeting with the design team next Tuesday at 2pm for 1 hour
  manage_email (call_XxqcJBvVIuKuRK794ZIzlLxx)
 Call ID: call_XxqcJBvVIuKuRK794ZIzlLxx
  Args:
    request: send the design team an email reminder about reviewing the new mockups
================================= Tool Message =================================
Name: schedule_event

Your meeting with the design team is scheduled for next Tuesday, June 18th, from 2:00pm to 3:00pm. Let me know if you need to add more details or make any changes!
================================= Tool Message =================================
Name: manage_email

I've sent an email reminder to the design team requesting them to review the new mockups. If you need to include more information or recipients, just let me know!
================================== Ai Message ==================================

Your meeting with the design team is scheduled for next Tuesday, June 18th, from 2:00pm to 3:00pm.

I've also sent an email reminder to the design team, asking them to review the new mockups.

Let me know if you'd like to add more details to the meeting or include additional information in the email!

The supervisor recognizes this requires both calendar and email actions, calls schedule_event for the meeting, then calls manage_email for the reminder. Each sub-agent completes its task, and the supervisor synthesizes both results into a coherent response.

Refer to the LangSmith trace to see the detailed information flow for the above run, including individual chat model prompts and responses.

##### ​Complete working example

Here’s everything together in a runnable script:

Show View complete codeCopy"""
Personal Assistant Supervisor Example

This example demonstrates the tool calling pattern for multi-agent systems.
A supervisor agent coordinates specialized sub-agents (calendar and email)
that are wrapped as tools.
"""

```python
from langchain.tools import tool
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

# ============================================================================
# Step 1: Define low-level API tools (stubbed)
# ============================================================================

@tool
def create_calendar_event(
    title: str,
    start_time: str,  # ISO format: "2024-01-15T14:00:00"
    end_time: str,    # ISO format: "2024-01-15T15:00:00"
    attendees: list[str],  # email addresses
    location: str = ""
) -> str:
    """Create a calendar event. Requires exact ISO datetime format."""
    return f"Event created: {title} from {start_time} to {end_time} with {len(attendees)} attendees"

@tool
def send_email(
    to: list[str],      # email addresses
    subject: str,
    body: str,
    cc: list[str] = []
) -> str:
    """Send an email via email API. Requires properly formatted addresses."""
    return f"Email sent to {', '.join(to)} - Subject: {subject}"

@tool
def get_available_time_slots(
    attendees: list[str],
    date: str,  # ISO format: "2024-01-15"
    duration_minutes: int
) -> list[str]:
    """Check calendar availability for given attendees on a specific date."""
    return ["09:00", "14:00", "16:00"]

# ============================================================================
# Step 2: Create specialized sub-agents
# ============================================================================

model = init_chat_model("claude-haiku-4-5-20251001")  # for example

calendar_agent = create_agent(
    model,
    tools=[create_calendar_event, get_available_time_slots],
    system_prompt=(
        "You are a calendar scheduling assistant. "
        "Parse natural language scheduling requests (e.g., 'next Tuesday at 2pm') "
        "into proper ISO datetime formats. "
        "Use get_available_time_slots to check availability when needed. "
        "Use create_calendar_event to schedule events. "
        "Always confirm what was scheduled in your final response."
    )
)

email_agent = create_agent(
    model,
    tools=[send_email],
    system_prompt=(
        "You are an email assistant. "
        "Compose professional emails based on natural language requests. "
        "Extract recipient information and craft appropriate subject lines and body text. "
        "Use send_email to send the message. "
        "Always confirm what was sent in your final response."
    )
)

# ============================================================================
# Step 3: Wrap sub-agents as tools for the supervisor
# ============================================================================

@tool
def schedule_event(request: str) -> str:
    """Schedule calendar events using natural language.

    Use this when the user wants to create, modify, or check calendar appointments.
    Handles date/time parsing, availability checking, and event creation.

    Input: Natural language scheduling request (e.g., 'meeting with design team
    next Tuesday at 2pm')
    """
    result = calendar_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text

@tool
def manage_email(request: str) -> str:
    """Send emails using natural language.

    Use this when the user wants to send notifications, reminders, or any email
    communication. Handles recipient extraction, subject generation, and email
    composition.

    Input: Natural language email request (e.g., 'send them a reminder about
    the meeting')
    """
    result = email_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text

# ============================================================================
# Step 4: Create the supervisor agent
# ============================================================================

supervisor_agent = create_agent(
    model,
    tools=[schedule_event, manage_email],
    system_prompt=(
        "You are a helpful personal assistant. "
        "You can schedule calendar events and send emails. "
        "Break down user requests into appropriate tool calls and coordinate the results. "
        "When a request involves multiple actions, use multiple tools in sequence."
    )
)

# ============================================================================
# Step 5: Use the supervisor
# ============================================================================

if __name__ == "__main__":
    # Example: User request requiring both calendar and email coordination
    user_request = (
        "Schedule a meeting with the design team next Tuesday at 2pm for 1 hour, "
        "and send them an email reminder about reviewing the new mockups."
    )

    print("User Request:", user_request)
    print("\n" + "="*80 + "\n")

    for step in supervisor_agent.stream(
        {"messages": [{"role": "user", "content": user_request}]}
    ):
        for update in step.values():
            for message in update.get("messages", []):
                message.pretty_print()
```

##### ​Understanding the architecture

Your system has three layers. The bottom layer contains rigid API tools that require exact formats. The middle layer contains sub-agents that accept natural language, translate it to structured API calls, and return natural language confirmations. The top layer contains the supervisor that routes to high-level capabilities and synthesizes results.

This separation of concerns provides several benefits: each layer has a focused responsibility, you can add new domains without affecting existing ones, and you can test and iterate on each layer independently.

#### ​6. Add human-in-the-loop review

It can be prudent to incorporate human-in-the-loop review of sensitive actions. LangChain includes built-in middleware to review tool calls, in this case the tools invoked by sub-agents.

Let’s add human-in-the-loop review to both sub-agents:

- We configure the create_calendar_event and send_email tools to interrupt, permitting all response types (approve, edit, reject)
- We add a checkpointer only to the top-level agent. This is required to pause and resume execution.
Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver

calendar_agent = create_agent(
    model,
    tools=[create_calendar_event, get_available_time_slots],
    system_prompt=CALENDAR_AGENT_PROMPT,
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={"create_calendar_event": True},
            description_prefix="Calendar event pending approval",
        ),
    ],
)

email_agent = create_agent(
    model,
    tools=[send_email],
    system_prompt=EMAIL_AGENT_PROMPT,
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={"send_email": True},
            description_prefix="Outbound email pending approval",
        ),
    ],
)

supervisor_agent = create_agent(
    model,
    tools=[schedule_event, manage_email],
    system_prompt=SUPERVISOR_PROMPT,
    checkpointer=InMemorySaver(),
)

Let’s repeat the query. Note that we gather interrupt events into a list to access downstream:

Copyquery = (
    "Schedule a meeting with the design team next Tuesday at 2pm for 1 hour, "
    "and send them an email reminder about reviewing the new mockups."
)

config = {"configurable": {"thread_id": "6"}}

interrupts = []
for step in supervisor_agent.stream(
    {"messages": [{"role": "user", "content": query}]},
    config,
):
    for update in step.values():
        if isinstance(update, dict):
            for message in update.get("messages", []):
                message.pretty_print()
        else:
            interrupt_ = update[0]
            interrupts.append(interrupt_)
            print(f"\nINTERRUPTED: {interrupt_.id}")

Copy================================== Ai Message ==================================
Tool Calls:
  schedule_event (call_t4Wyn32ohaShpEZKuzZbl83z)
 Call ID: call_t4Wyn32ohaShpEZKuzZbl83z
  Args:
    request: Schedule a meeting with the design team next Tuesday at 2pm for 1 hour.
  manage_email (call_JWj4vDJ5VMnvkySymhCBm4IR)
 Call ID: call_JWj4vDJ5VMnvkySymhCBm4IR
  Args:
    request: Send an email reminder to the design team about reviewing the new mockups before our meeting next Tuesday at 2pm.

INTERRUPTED: 4f994c9721682a292af303ec1a46abb7

INTERRUPTED: 2b56f299be313ad8bc689eff02973f16

This time we’ve interrupted execution. Let’s inspect the interrupt events:

Copyfor interrupt_ in interrupts:
    for request in interrupt_.value["action_requests"]:
        print(f"INTERRUPTED: {interrupt_.id}")
        print(f"{request['description']}\n")

CopyINTERRUPTED: 4f994c9721682a292af303ec1a46abb7
Calendar event pending approval

Tool: create_calendar_event
Args: {'title': 'Meeting with the Design Team', 'start_time': '2024-06-18T14:00:00', 'end_time': '2024-06-18T15:00:00', 'attendees': ['design team']}

INTERRUPTED: 2b56f299be313ad8bc689eff02973f16
Outbound email pending approval

Tool: send_email
Args: {'to': ['designteam@example.com'], 'subject': 'Reminder: Review New Mockups Before Meeting Next Tuesday at 2pm', 'body': "Hello Team,\n\nThis is a reminder to review the new mockups ahead of our meeting scheduled for next Tuesday at 2pm. Your feedback and insights will be valuable for our discussion and next steps.\n\nPlease ensure you've gone through the designs and are ready to share your thoughts during the meeting.\n\nThank you!\n\nBest regards,\n[Your Name]"}

We can specify decisions for each interrupt by referring to its ID using a Command. Refer to the human-in-the-loop guide for additional details. For demonstration purposes, here we will accept the calendar event, but edit the subject of the outbound email:

Copyfrom langgraph.types import Command

resume = {}
for interrupt_ in interrupts:
    if interrupt_.id == "2b56f299be313ad8bc689eff02973f16":
        # Edit email
        edited_action = interrupt_.value["action_requests"][0].copy()
        edited_action["arguments"]["subject"] = "Mockups reminder"
        resume[interrupt_.id] = {
            "decisions": [{"type": "edit", "edited_action": edited_action}]
        }
    else:
        resume[interrupt_.id] = {"decisions": [{"type": "approve"}]}

interrupts = []
for step in supervisor_agent.stream(
    Command(resume=resume),
    config,
):
    for update in step.values():
        if isinstance(update, dict):
            for message in update.get("messages", []):
                message.pretty_print()
        else:
            interrupt_ = update[0]
            interrupts.append(interrupt_)
            print(f"\nINTERRUPTED: {interrupt_.id}")

Copy================================= Tool Message =================================
Name: schedule_event

Your meeting with the design team has been scheduled for next Tuesday, June 18th, from 2:00 pm to 3:00 pm.
================================= Tool Message =================================
Name: manage_email

Your email reminder to the design team has been sent. Here’s what was sent:

- Recipient: designteam@example.com
- Subject: Mockups reminder
- Body: A reminder to review the new mockups before the meeting next Tuesday at 2pm, with a request for feedback and readiness for discussion.

Let me know if you need any further assistance!
================================== Ai Message ==================================

- Your meeting with the design team has been scheduled for next Tuesday, June 18th, from 2:00 pm to 3:00 pm.
- An email reminder has been sent to the design team about reviewing the new mockups before the meeting.

Let me know if you need any further assistance!

The run proceeds with our input.
```

#### ​7. Advanced: Control information flow

By default, sub-agents receive only the request string from the supervisor. You might want to pass additional context, such as conversation history or user preferences.

##### ​Pass additional conversational context to sub-agents

Copyfrom langchain.tools import tool, ToolRuntime

```python
@tool
def schedule_event(
    request: str,
    runtime: ToolRuntime
) -> str:
    """Schedule calendar events using natural language."""
    # Customize context received by sub-agent
    original_user_message = next(
        message for message in runtime.state["messages"]
        if message.type == "human"
    )
    prompt = (
        "You are assisting with the following user inquiry:\n\n"
        f"{original_user_message.text}\n\n"
        "You are tasked with the following sub-request:\n\n"
        f"{request}"
    )
    result = calendar_agent.invoke({
        "messages": [{"role": "user", "content": prompt}],
    })
    return result["messages"][-1].text

This allows sub-agents to see the full conversation context, which can be useful for resolving ambiguities like “schedule it for the same time tomorrow” (referencing a previous conversation).

You can see the full context received by the sub agent in the chat model call of the LangSmith trace.
```

##### ​Control what supervisor receives

You can also customize what information flows back to the supervisor:

Copyimport json

```python
@tool
def schedule_event(request: str) -> str:
    """Schedule calendar events using natural language."""
    result = calendar_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })

    # Option 1: Return just the confirmation message
    return result["messages"][-1].text

    # Option 2: Return structured data
    # return json.dumps({
    #     "status": "success",
    #     "event_id": "evt_123",
    #     "summary": result["messages"][-1].text
    # })

Important: Make sure sub-agent prompts emphasize that their final message should contain all relevant information. A common failure mode is sub-agents that perform tool calls but don’t include the results in their final response.
```

#### ​8. Key takeaways

The supervisor pattern creates layers of abstraction where each layer has a clear responsibility. When designing a supervisor system, start with clear domain boundaries and give each sub-agent focused tools and prompts. Write clear tool descriptions for the supervisor, test each layer independently before integration, and control information flow based on your specific needs.

When to use the supervisor patternUse the supervisor pattern when you have multiple distinct domains (calendar, email, CRM, database), each domain has multiple tools or complex logic, you want centralized workflow control, and sub-agents don’t need to converse directly with users.For simpler cases with just a few tools, use a single agent. When agents need to have conversations with users, use handoffs instead. For peer-to-peer collaboration between agents, consider other multi-agent patterns.

#### ​Next steps

Learn about handoffs for agent-to-agent conversations, explore context engineering to fine-tune information flow, read the multi-agent overview to compare different patterns, and use LangSmith to debug and monitor your multi-agent system.

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Build a voice agent with LangChain - Docs by LangChain {#doc-13}

**Source:** [https://docs.langchain.com/oss/python/langchain/voice-agent](https://docs.langchain.com/oss/python/langchain/voice-agent)

### Build a voice agent with LangChain

Copy page

#### ​Overview

Chat interfaces have dominated how we interact with AI, but recent breakthroughs in multimodal AI are opening up exciting new possibilities. High-quality generative models and expressive text-to-speech (TTS) systems now make it possible to build agents that feel less like tools and more like conversational partners.

Voice agents are one example of this. Instead of relying on a keyboard and mouse to type inputs into an agent, you can use spoken words to interact with it. This can be a more natural and engaging way to interact with AI, and can be especially useful for certain contexts.

##### ​What are voice agents?

Voice agents are agents that can engage in natural spoken conversations with users. These agents combine speech recognition, natural language processing, generative AI, and text-to-speech technologies to create seamless, natural conversations.

They’re suited for a variety of use cases, including:

- Customer support
- Personal assistants
- Hands-free interfaces
- Coaching and training

##### ​How do voice agents work?

At a high level, every voice agent needs to handle three tasks:

- Listen - capture audio and transcribe it
- Think - interpret intent, reason, plan
- Speak - generate audio and stream it back to the user
The difference lies in how these steps are sequenced and coupled. In practice, production agents follow one of two main architectures:

###### ​1. STT > Agent > TTS Architecture (The “Sandwich”)

The Sandwich architecture composes three distinct components: speech-to-text (STT), a text-based LangChain agent, and text-to-speech (TTS).

Pros:

- Full control over each component (swap STT/TTS providers as needed)
- Access to latest capabilities from modern text-modality models
- Transparent behavior with clear boundaries between components
Cons:

- Requires orchestrating multiple services
- Additional complexity in managing the pipeline
- Conversion from speech to text loses information (e.g., tone, emotion)

###### ​2. Speech-to-Speech Architecture (S2S)

Speech-to-speech uses a multimodal model that processes audio input and generates audio output natively.

Pros:

- Simpler architecture with fewer moving parts
- Typically lower latency for simple interactions
- Direct audio processing captures tone and other nuances of speech
Cons:

- Limited model options, greater risk of provider lock-in
- Features may lag behind text-modality models
- Less transparency in how audio is processed
- Reduced controllability and customization options
This guide demonstrates the sandwich architecture to balance performance, controllability, and access to modern model capabilities. The sandwich can achieve sub-700ms latency with some STT and TTS providers while maintaining control over modular components.

##### ​Demo Application Overview

We’ll walk through building a voice-based agent using the sandwich architecture. The agent will manage orders for a sandwich shop. The application will demonstrate all three components of the sandwich architecture, using AssemblyAI for STT and Cartesia for TTS (although adapters can be built for most providers).

An end-to-end reference application is available in the voice-sandwich-demo repository. We will walk through that application here.

The demo uses WebSockets for real-time bidirectional communication between the browser and server. The same architecture can be adapted for other transports like telephony systems (Twilio, Vonage) or WebRTC connections.

##### ​Architecture

The demo implements a streaming pipeline where each stage processes data asynchronously:

Client (Browser)

- Captures microphone audio and encodes it as PCM
- Establishes WebSocket connection to the backend server
- Streams audio chunks to the server in real-time
- Receives and plays back synthesized speech audio
Server (Python)

- Accepts WebSocket connections from clients
- Orchestrates the three-step pipeline:

Speech-to-text (STT): Forwards audio to the STT provider (e.g., AssemblyAI), receives transcript events
Agent: Processes transcripts with LangChain agent, streams response tokens
Text-to-speech (TTS): Sends agent responses to the TTS provider (e.g., Cartesia), receives audio chunks
- Speech-to-text (STT): Forwards audio to the STT provider (e.g., AssemblyAI), receives transcript events
- Agent: Processes transcripts with LangChain agent, streams response tokens
- Text-to-speech (TTS): Sends agent responses to the TTS provider (e.g., Cartesia), receives audio chunks
- Returns synthesized audio to the client for playback
The pipeline uses async generators to enable streaming at each stage. This allows downstream components to begin processing before upstream stages complete, minimizing end-to-end latency.

#### ​Setup

For detailed installation instructions and setup, see the repository README.

#### ​1. Speech-to-text

The STT stage transforms an incoming audio stream into text transcripts. The implementation uses a producer-consumer pattern to handle audio streaming and transcript reception concurrently.

##### ​Key Concepts

Producer-Consumer Pattern: Audio chunks are sent to the STT service concurrently with receiving transcript events. This allows transcription to begin before all audio has arrived.

Event Types:

- stt_chunk: Partial transcripts provided as the STT service processes audio
- stt_output: Final, formatted transcripts that trigger agent processing
WebSocket Connection: Maintains a persistent connection to AssemblyAI’s real-time STT API, configured for 16kHz PCM audio with automatic turn formatting.

##### ​Implementation

Copyfrom typing import AsyncIterator
```python
import asyncio
from assemblyai_stt import AssemblyAISTT
from events import VoiceAgentEvent

async def stt_stream(
    audio_stream: AsyncIterator[bytes],
) -> AsyncIterator[VoiceAgentEvent]:
    """
    Transform stream: Audio (Bytes) → Voice Events (VoiceAgentEvent)

    Uses a producer-consumer pattern where:
    - Producer: Reads audio chunks and sends them to AssemblyAI
    - Consumer: Receives transcription events from AssemblyAI
    """
    stt = AssemblyAISTT(sample_rate=16000)

    async def send_audio():
        """Background task that pumps audio chunks to AssemblyAI."""
        try:
            async for audio_chunk in audio_stream:
                await stt.send_audio(audio_chunk)
        finally:
            # Signal completion when audio stream ends
            await stt.close()

    # Launch audio sending in background
    send_task = asyncio.create_task(send_audio())

    try:
        # Receive and yield transcription events as they arrive
        async for event in stt.receive_events():
            yield event
    finally:
        # Cleanup
        with contextlib.suppress(asyncio.CancelledError):
            send_task.cancel()
            await send_task
        await stt.close()

The application implements an AssemblyAI client to manage the WebSocket connection and message parsing. See below for implementations; similar adapters can be constructed for other STT providers.

AssemblyAI ClientCopyclass AssemblyAISTT:
    def __init__(self, api_key: str | None = None, sample_rate: int = 16000):
        self.api_key = api_key or os.getenv("ASSEMBLYAI_API_KEY")
        self.sample_rate = sample_rate
        self._ws: WebSocketClientProtocol | None = None

    async def send_audio(self, audio_chunk: bytes) -> None:
        """Send PCM audio bytes to AssemblyAI."""
        ws = await self._ensure_connection()
        await ws.send(audio_chunk)

    async def receive_events(self) -> AsyncIterator[STTEvent]:
        """Yield STT events as they arrive from AssemblyAI."""
        async for raw_message in self._ws:
            message = json.loads(raw_message)

            if message["type"] == "Turn":
                # Final formatted transcript
                if message.get("turn_is_formatted"):
                    yield STTOutputEvent.create(message["transcript"])
                # Partial transcript
                else:
                    yield STTChunkEvent.create(message["transcript"])

    async def _ensure_connection(self) -> WebSocketClientProtocol:
        """Establish WebSocket connection if not already connected."""
        if self._ws is None:
            url = f"wss://streaming.assemblyai.com/v3/ws?sample_rate={self.sample_rate}&format_turns=true"
            self._ws = await websockets.connect(
                url,
                additional_headers={"Authorization": self.api_key}
            )
        return self._ws
```

#### ​2. LangChain agent

The agent stage processes text transcripts through a LangChain agent and streams the response tokens. In this case, we stream all text content blocks generated by the agent.

##### ​Key Concepts

Streaming Responses: The agent uses stream_mode="messages" to emit response tokens as they’re generated, rather than waiting for the complete response. This enables the TTS stage to begin synthesis immediately.

Conversation Memory: A checkpointer maintains conversation state across turns using a unique thread ID. This allows the agent to reference previous exchanges in the conversation.

##### ​Implementation

Copyfrom uuid import uuid4
```python
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

# Define agent tools
def add_to_order(item: str, quantity: int) -> str:
    """Add an item to the customer's sandwich order."""
    return f"Added {quantity} x {item} to the order."

def confirm_order(order_summary: str) -> str:
    """Confirm the final order with the customer."""
    return f"Order confirmed: {order_summary}. Sending to kitchen."

# Create agent with tools and memory
agent = create_agent(
    model="anthropic:claude-haiku-4-5",  # Select your model
    tools=[add_to_order, confirm_order],
    system_prompt="""You are a helpful sandwich shop assistant.
    Your goal is to take the user's order. Be concise and friendly.
    Do NOT use emojis, special characters, or markdown.
    Your responses will be read by a text-to-speech engine.""",
    checkpointer=InMemorySaver(),
)

async def agent_stream(
    event_stream: AsyncIterator[VoiceAgentEvent],
) -> AsyncIterator[VoiceAgentEvent]:
    """
    Transform stream: Voice Events → Voice Events (with Agent Responses)

    Passes through all upstream events and adds agent_chunk events
    when processing STT transcripts.
    """
    # Generate unique thread ID for conversation memory
    thread_id = str(uuid4())

    async for event in event_stream:
        # Pass through all upstream events
        yield event

        # Process final transcripts through the agent
        if event.type == "stt_output":
            # Stream agent response with conversation context
            stream = agent.astream(
                {"messages": [HumanMessage(content=event.transcript)]},
                {"configurable": {"thread_id": thread_id}},
                stream_mode="messages",
            )

            # Yield agent response chunks as they arrive
            async for message, _ in stream:
                if message.text:
                    yield AgentChunkEvent.create(message.text)
```

#### ​3. Text-to-speech

The TTS stage synthesizes agent response text into audio and streams it back to the client. Like the STT stage, it uses a producer-consumer pattern to handle concurrent text sending and audio reception.

##### ​Key Concepts

Concurrent Processing: The implementation merges two async streams:

- Upstream processing: Passes through all events and sends agent text chunks to the TTS provider
- Audio reception: Receives synthesized audio chunks from the TTS provider
Streaming TTS: Some providers (such as Cartesia) begin synthesizing audio as soon as it receives text, enabling audio playback to start before the agent finishes generating its complete response.

Event Passthrough: All upstream events flow through unchanged, allowing the client or other observers to track the full pipeline state.

##### ​Implementation

Copyfrom cartesia_tts import CartesiaTTS
```python
from utils import merge_async_iters

async def tts_stream(
    event_stream: AsyncIterator[VoiceAgentEvent],
) -> AsyncIterator[VoiceAgentEvent]:
    """
    Transform stream: Voice Events → Voice Events (with Audio)

    Merges two concurrent streams:
    1. process_upstream(): passes through events and sends text to Cartesia
    2. tts.receive_events(): yields audio chunks from Cartesia
    """
    tts = CartesiaTTS()

    async def process_upstream() -> AsyncIterator[VoiceAgentEvent]:
        """Process upstream events and send agent text to Cartesia."""
        async for event in event_stream:
            # Pass through all events
            yield event
            # Send agent text to Cartesia for synthesis
            if event.type == "agent_chunk":
                await tts.send_text(event.text)

    try:
        # Merge upstream events with TTS audio events
        # Both streams run concurrently
        async for event in merge_async_iters(
            process_upstream(),
            tts.receive_events()
        ):
            yield event
    finally:
        await tts.close()

The application implements an Cartesia client to manage the WebSocket connection and audio streaming. See below for implementations; similar adapters can be constructed for other TTS providers.

Cartesia ClientCopyimport base64
import json
import websockets

class CartesiaTTS:
    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_id: str = "f6ff7c0c-e396-40a9-a70b-f7607edb6937",
        model_id: str = "sonic-3",
        sample_rate: int = 24000,
        encoding: str = "pcm_s16le",
    ):
        self.api_key = api_key or os.getenv("CARTESIA_API_KEY")
        self.voice_id = voice_id
        self.model_id = model_id
        self.sample_rate = sample_rate
        self.encoding = encoding
        self._ws: WebSocketClientProtocol | None = None

    def _generate_context_id(self) -> str:
        """Generate a valid context_id for Cartesia."""
        timestamp = int(time.time() * 1000)
        counter = self._context_counter
        self._context_counter += 1
        return f"ctx_{timestamp}_{counter}"

    async def send_text(self, text: str | None) -> None:
        """Send text to Cartesia for synthesis."""
        if not text or not text.strip():
            return

        ws = await self._ensure_connection()
        payload = {
            "model_id": self.model_id,
            "transcript": text,
            "voice": {
                "mode": "id",
                "id": self.voice_id,
            },
            "output_format": {
                "container": "raw",
                "encoding": self.encoding,
                "sample_rate": self.sample_rate,
            },
            "language": self.language,
            "context_id": self._generate_context_id(),
        }
        await ws.send(json.dumps(payload))

    async def receive_events(self) -> AsyncIterator[TTSChunkEvent]:
        """Yield audio chunks as they arrive from Cartesia."""
        async for raw_message in self._ws:
            message = json.loads(raw_message)

            # Decode and yield audio chunks
            if "data" in message and message["data"]:
                audio_chunk = base64.b64decode(message["data"])
                if audio_chunk:
                    yield TTSChunkEvent.create(audio_chunk)

    async def _ensure_connection(self) -> WebSocketClientProtocol:
        """Establish WebSocket connection if not already connected."""
        if self._ws is None:
            url = (
                f"wss://api.cartesia.ai/tts/websocket"
                f"?api_key={self.api_key}&cartesia_version={self.cartesia_version}"
            )
            self._ws = await websockets.connect(url)

        return self._ws
```

#### ​Putting It All Together

The complete pipeline chains the three stages together:

Copyfrom langchain_core.runnables import RunnableGenerator

pipeline = (
    RunnableGenerator(stt_stream)      # Audio → STT events
    | RunnableGenerator(agent_stream)  # STT events → Agent events
    | RunnableGenerator(tts_stream)    # Agent events → TTS audio
)

# Use in WebSocket endpoint
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    async def websocket_audio_stream():
        """Yield audio bytes from WebSocket."""
        while True:
            data = await websocket.receive_bytes()
            yield data

    # Transform audio through pipeline
    output_stream = pipeline.atransform(websocket_audio_stream())

    # Send TTS audio back to client
    async for event in output_stream:
        if event.type == "tts_chunk":
            await websocket.send_bytes(event.audio)

We use RunnableGenerators to compose each step of the pipeline. This is an abstraction LangChain uses internally to manage streaming across components.

Each stage processes events independently and concurrently: audio transcription begins as soon as audio arrives, the agent starts reasoning as soon as a transcript is available, and speech synthesis begins as soon as agent text is generated. This architecture can achieve sub-700ms latency to support natural conversation.

For more on building agents with LangChain, see the Agents guide.

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```


---

## Build a SQL agent - Docs by LangChain {#doc-14}

**Source:** [https://docs.langchain.com/oss/python/langchain/sql-agent](https://docs.langchain.com/oss/python/langchain/sql-agent)

### Build a SQL agent

Copy page

#### ​Overview

In this tutorial, you will learn how to build an agent that can answer questions about a SQL database using LangChain agents.

At a high level, the agent will:

1Fetch the available tables and schemas from the database2Decide which tables are relevant to the question3Fetch the schemas for the relevant tables4Generate a query based on the question and information from the schemas5Double-check the query for common mistakes using an LLM6Execute the query and return the results7Correct mistakes surfaced by the database engine until the query is successful8Formulate a response based on the results

Building Q&A systems of SQL databases requires executing model-generated SQL queries. There are inherent risks in doing this. Make sure that your database connection permissions are always scoped as narrowly as possible for your agent’s needs. This will mitigate, though not eliminate, the risks of building a model-driven system.

##### ​Concepts

We will cover the following concepts:

- Tools for reading from SQL databases
- LangChain agents
- Human-in-the-loop processes

#### ​Setup

##### ​Installation

pipCopypip install langchain  langgraph  langchain-community

##### ​LangSmith

Set up LangSmith to inspect what is happening inside your chain or agent. Then set the following environment variables:

Copyexport LANGSMITH_TRACING="true"
export LANGSMITH_API_KEY="..."

#### ​1. Select an LLM

Select a model that supports tool-calling:

OpenAI Anthropic Azure Google Gemini AWS Bedrock HuggingFace👉 Read the OpenAI chat model integration docsCopypip install -U "langchain[openai]"
init_chat_modelModel ClassCopyimport os
```python
from langchain.chat_models import init_chat_model

os.environ["OPENAI_API_KEY"] = "sk-..."

model = init_chat_model("gpt-4.1")
👉 Read the Anthropic chat model integration docsCopypip install -U "langchain[anthropic]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["ANTHROPIC_API_KEY"] = "sk-..."

model = init_chat_model("claude-sonnet-4-5-20250929")
👉 Read the Azure chat model integration docsCopypip install -U "langchain[openai]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["AZURE_OPENAI_API_KEY"] = "..."
os.environ["AZURE_OPENAI_ENDPOINT"] = "..."
os.environ["OPENAI_API_VERSION"] = "2025-03-01-preview"

model = init_chat_model(
    "azure_openai:gpt-4.1",
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
)
👉 Read the Google GenAI chat model integration docsCopypip install -U "langchain[google-genai]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["GOOGLE_API_KEY"] = "..."

model = init_chat_model("google_genai:gemini-2.5-flash-lite")
👉 Read the AWS Bedrock chat model integration docsCopypip install -U "langchain[aws]"
init_chat_modelModel ClassCopyfrom langchain.chat_models import init_chat_model

# Follow the steps here to configure your credentials:
# https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html

model = init_chat_model(
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
    model_provider="bedrock_converse",
)
👉 Read the HuggingFace chat model integration docsCopypip install -U "langchain[huggingface]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["HUGGINGFACEHUB_API_TOKEN"] = "hf_..."

model = init_chat_model(
    "microsoft/Phi-3-mini-4k-instruct",
    model_provider="huggingface",
    temperature=0.7,
    max_tokens=1024,
)

The output shown in the examples below used OpenAI.
```

#### ​2. Configure the database

You will be creating a SQLite database for this tutorial. SQLite is a lightweight database that is easy to set up and use. We will be loading the chinook database, which is a sample database that represents a digital media store.

For convenience, we have hosted the database (Chinook.db) on a public GCS bucket.

Copyimport requests, pathlib

url = "https://storage.googleapis.com/benchmarks-artifacts/chinook/Chinook.db"
local_path = pathlib.Path("Chinook.db")

if local_path.exists():
    print(f"{local_path} already exists, skipping download.")
else:
    response = requests.get(url)
    if response.status_code == 200:
        local_path.write_bytes(response.content)
        print(f"File downloaded and saved as {local_path}")
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")

We will use a handy SQL database wrapper available in the langchain_community package to interact with the database. The wrapper provides a simple interface to execute SQL queries and fetch results:

Copyfrom langchain_community.utilities import SQLDatabase

db = SQLDatabase.from_uri("sqlite:///Chinook.db")

print(f"Dialect: {db.dialect}")
print(f"Available tables: {db.get_usable_table_names()}")
print(f'Sample output: {db.run("SELECT * FROM Artist LIMIT 5;")}')

CopyDialect: sqlite
Available tables: ['Album', 'Artist', 'Customer', 'Employee', 'Genre', 'Invoice', 'InvoiceLine', 'MediaType', 'Playlist', 'PlaylistTrack', 'Track']
Sample output: [(1, 'AC/DC'), (2, 'Accept'), (3, 'Aerosmith'), (4, 'Alanis Morissette'), (5, 'Alice In Chains')]

#### ​3. Add tools for database interactions

Use the SQLDatabase wrapper available in the langchain_community package to interact with the database. The wrapper provides a simple interface to execute SQL queries and fetch results:

Copyfrom langchain_community.agent_toolkits import SQLDatabaseToolkit

toolkit = SQLDatabaseToolkit(db=db, llm=model)

tools = toolkit.get_tools()

for tool in tools:
    print(f"{tool.name}: {tool.description}\n")

Copysql_db_query: Input to this tool is a detailed and correct SQL query, output is a result from the database. If the query is not correct, an error message will be returned. If an error is returned, rewrite the query, check the query, and try again. If you encounter an issue with Unknown column 'xxxx' in 'field list', use sql_db_schema to query the correct table fields.

sql_db_schema: Input to this tool is a comma-separated list of tables, output is the schema and sample rows for those tables. Be sure that the tables actually exist by calling sql_db_list_tables first! Example Input: table1, table2, table3

sql_db_list_tables: Input is an empty string, output is a comma-separated list of tables in the database.

sql_db_query_checker: Use this tool to double check if your query is correct before executing it. Always use this tool before executing a query with sql_db_query!

#### ​4. Use create_agent

Use create_agent to build a ReAct agent with minimal code. The agent will interpret the request and generate a SQL command, which the tools will execute. If the command has an error, the error message is returned to the model. The model can then examine the original request and the new error message and generate a new command. This can continue until the LLM generates the command successfully or reaches an end count. This pattern of providing a model with feedback - error messages in this case - is very powerful.

Initialize the agent with a descriptive system prompt to customize its behavior:

Copysystem_prompt = """
You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query to run,
then look at the results of the query and return the answer. Unless the user
specifies a specific number of examples they wish to obtain, always limit your
query to at most {top_k} results.

You can order the results by a relevant column to return the most interesting
examples in the database. Never query for all the columns from a specific table,
only ask for the relevant columns given the question.

You MUST double check your query before executing it. If you get an error while
executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
database.

To start you should ALWAYS look at the tables in the database to see what you
can query. Do NOT skip this step.

Then you should query the schema of the most relevant tables.
""".format(
    dialect=db.dialect,
    top_k=5,
)

Now, create an agent with the model, tools, and prompt:

Copyfrom langchain.agents import create_agent

agent = create_agent(
    model,
    tools,
    system_prompt=system_prompt,
)

#### ​5. Run the agent

Run the agent on a sample query and observe its behavior:

Copyquestion = "Which genre on average has the longest tracks?"

for step in agent.stream(
    {"messages": [{"role": "user", "content": question}]},
    stream_mode="values",
):
    step["messages"][-1].pretty_print()

Copy================================ Human Message =================================

Which genre on average has the longest tracks?
================================== Ai Message ==================================
Tool Calls:
  sql_db_list_tables (call_BQsWg8P65apHc8BTJ1NPDvnM)
 Call ID: call_BQsWg8P65apHc8BTJ1NPDvnM
  Args:
================================= Tool Message =================================
Name: sql_db_list_tables

Album, Artist, Customer, Employee, Genre, Invoice, InvoiceLine, MediaType, Playlist, PlaylistTrack, Track
================================== Ai Message ==================================
Tool Calls:
  sql_db_schema (call_i89tjKECFSeERbuACYm4w0cU)
 Call ID: call_i89tjKECFSeERbuACYm4w0cU
  Args:
    table_names: Track, Genre
================================= Tool Message =================================
Name: sql_db_schema

CREATE TABLE "Genre" (
	"GenreId" INTEGER NOT NULL,
	"Name" NVARCHAR(120),
	PRIMARY KEY ("GenreId")
)

/*
3 rows from Genre table:
GenreId	Name
1	Rock
2	Jazz
3	Metal
*/

CREATE TABLE "Track" (
	"TrackId" INTEGER NOT NULL,
	"Name" NVARCHAR(200) NOT NULL,
	"AlbumId" INTEGER,
	"MediaTypeId" INTEGER NOT NULL,
	"GenreId" INTEGER,
	"Composer" NVARCHAR(220),
	"Milliseconds" INTEGER NOT NULL,
	"Bytes" INTEGER,
	"UnitPrice" NUMERIC(10, 2) NOT NULL,
	PRIMARY KEY ("TrackId"),
	FOREIGN KEY("MediaTypeId") REFERENCES "MediaType" ("MediaTypeId"),
	FOREIGN KEY("GenreId") REFERENCES "Genre" ("GenreId"),
	FOREIGN KEY("AlbumId") REFERENCES "Album" ("AlbumId")
)

/*
3 rows from Track table:
TrackId	Name	AlbumId	MediaTypeId	GenreId	Composer	Milliseconds	Bytes	UnitPrice
1	For Those About To Rock (We Salute You)	1	1	1	Angus Young, Malcolm Young, Brian Johnson	343719	11170334	0.99
2	Balls to the Wall	2	2	1	U. Dirkschneider, W. Hoffmann, H. Frank, P. Baltes, S. Kaufmann, G. Hoffmann	342562	5510424	0.99
3	Fast As a Shark	3	2	1	F. Baltes, S. Kaufman, U. Dirkscneider & W. Hoffman	230619	3990994	0.99
*/
================================== Ai Message ==================================
Tool Calls:
  sql_db_query_checker (call_G64yYm6R6UauiVPCXJZMA49b)
 Call ID: call_G64yYm6R6UauiVPCXJZMA49b
  Args:
    query: SELECT Genre.Name, AVG(Track.Milliseconds) AS AverageLength FROM Track INNER JOIN Genre ON Track.GenreId = Genre.GenreId GROUP BY Genre.Name ORDER BY AverageLength DESC LIMIT 5;
================================= Tool Message =================================
Name: sql_db_query_checker

SELECT Genre.Name, AVG(Track.Milliseconds) AS AverageLength FROM Track INNER JOIN Genre ON Track.GenreId = Genre.GenreId GROUP BY Genre.Name ORDER BY AverageLength DESC LIMIT 5;
================================== Ai Message ==================================
Tool Calls:
  sql_db_query (call_AnO3SrhD0ODJBxh6dHMwvHwZ)
 Call ID: call_AnO3SrhD0ODJBxh6dHMwvHwZ
  Args:
    query: SELECT Genre.Name, AVG(Track.Milliseconds) AS AverageLength FROM Track INNER JOIN Genre ON Track.GenreId = Genre.GenreId GROUP BY Genre.Name ORDER BY AverageLength DESC LIMIT 5;
================================= Tool Message =================================
Name: sql_db_query

[('Sci Fi & Fantasy', 2911783.0384615385), ('Science Fiction', 2625549.076923077), ('Drama', 2575283.78125), ('TV Shows', 2145041.0215053763), ('Comedy', 1585263.705882353)]
================================== Ai Message ==================================

On average, the genre with the longest tracks is "Sci Fi & Fantasy" with an average track length of approximately 2,911,783 milliseconds. This is followed by "Science Fiction," "Drama," "TV Shows," and "Comedy."

The agent correctly wrote a query, checked the query, and ran it to inform its final response.

You can inspect all aspects of the above run, including steps taken, tools invoked, what prompts were seen by the LLM, and more in the LangSmith trace.

##### ​(Optional) Use Studio

Studio provides a “client side” loop as well as memory so you can run this as a chat interface and query the database. You can ask questions like “Tell me the scheme of the database” or “Show me the invoices for the 5 top customers”. You will see the SQL command that is generated and the resulting output. The details of how to get that started are below.

Run your agent in StudioIn addition to the previously mentioned packages, you will need to:Copypip install -U langgraph-cli[inmem]>=0.4.0
```
In directory you will run in, you will need a langgraph.json file with the following contents:Copy{
  "dependencies": ["."],
  "graphs": {
      "agent": "./sql_agent.py:agent",
      "graph": "./sql_agent_langgraph.py:graph"
  },
  "env": ".env"
}
Create a file sql_agent.py and insert this:Copy#sql_agent.py for studio
import pathlib

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
import requests

# Initialize an LLM
model = init_chat_model("gpt-4.1")

# Get the database, store it locally
url = "https://storage.googleapis.com/benchmarks-artifacts/chinook/Chinook.db"
local_path = pathlib.Path("Chinook.db")

if local_path.exists():
    print(f"{local_path} already exists, skipping download.")
else:
    response = requests.get(url)
    if response.status_code == 200:
        local_path.write_bytes(response.content)
        print(f"File downloaded and saved as {local_path}")
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")

db = SQLDatabase.from_uri("sqlite:///Chinook.db")

# Create the tools
toolkit = SQLDatabaseToolkit(db=db, llm=model)

tools = toolkit.get_tools()

for tool in tools:
    print(f"{tool.name}: {tool.description}\n")

# Use create_agent
system_prompt = """
You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query to run,
then look at the results of the query and return the answer. Unless the user
specifies a specific number of examples they wish to obtain, always limit your
query to at most {top_k} results.

You can order the results by a relevant column to return the most interesting
examples in the database. Never query for all the columns from a specific table,
only ask for the relevant columns given the question.

You MUST double check your query before executing it. If you get an error while
executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
database.

To start you should ALWAYS look at the tables in the database to see what you
can query. Do NOT skip this step.

Then you should query the schema of the most relevant tables.
""".format(
    dialect=db.dialect,
    top_k=5,
)

agent = create_agent(
    model,
    tools,
    system_prompt=system_prompt,
)
```

#### ​6. Implement human-in-the-loop review

It can be prudent to check the agent’s SQL queries before they are executed for any unintended actions or inefficiencies.

LangChain agents feature support for built-in human-in-the-loop middleware to add oversight to agent tool calls. Let’s configure the agent to pause for human review on calling the sql_db_query tool:

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model,
    tools,
    system_prompt=system_prompt,
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={"sql_db_query": True},
            description_prefix="Tool execution pending approval",
        ),
    ],
    checkpointer=InMemorySaver(),
)

We’ve added a checkpointer to our agent to allow execution to be paused and resumed. See the human-in-the-loop guide for details on this as well as available middleware configurations.

On running the agent, it will now pause for review before executing the sql_db_query tool:

Copyquestion = "Which genre on average has the longest tracks?"
config = {"configurable": {"thread_id": "1"}}

for step in agent.stream(
    {"messages": [{"role": "user", "content": question}]},
    config,
    stream_mode="values",
):
    if "__interrupt__" in step:
        print("INTERRUPTED:")
        interrupt = step["__interrupt__"][0]
        for request in interrupt.value["action_requests"]:
            print(request["description"])
    elif "messages" in step:
        step["messages"][-1].pretty_print()
    else:
        pass

Copy...

INTERRUPTED:
Tool execution pending approval

Tool: sql_db_query
Args: {'query': 'SELECT g.Name AS Genre, AVG(t.Milliseconds) AS AvgTrackLength FROM Track t JOIN Genre g ON t.GenreId = g.GenreId GROUP BY g.Name ORDER BY AvgTrackLength DESC LIMIT 1;'}

We can resume execution, in this case accepting the query, using Command:

Copyfrom langgraph.types import Command

for step in agent.stream(
    Command(resume={"decisions": [{"type": "approve"}]}),
    config,
    stream_mode="values",
):
    if "messages" in step:
        step["messages"][-1].pretty_print()
    elif "__interrupt__" in step:
        print("INTERRUPTED:")
        interrupt = step["__interrupt__"][0]
        for request in interrupt.value["action_requests"]:
            print(request["description"])
    else:
        pass

Copy================================== Ai Message ==================================
Tool Calls:
  sql_db_query (call_7oz86Epg7lYRqi9rQHbZPS1U)
 Call ID: call_7oz86Epg7lYRqi9rQHbZPS1U
  Args:
    query: SELECT Genre.Name, AVG(Track.Milliseconds) AS AvgDuration FROM Track JOIN Genre ON Track.GenreId = Genre.GenreId GROUP BY Genre.Name ORDER BY AvgDuration DESC LIMIT 5;
================================= Tool Message =================================
Name: sql_db_query

[('Sci Fi & Fantasy', 2911783.0384615385), ('Science Fiction', 2625549.076923077), ('Drama', 2575283.78125), ('TV Shows', 2145041.0215053763), ('Comedy', 1585263.705882353)]
================================== Ai Message ==================================

The genre with the longest average track length is "Sci Fi & Fantasy" with an average duration of about 2,911,783 milliseconds, followed by "Science Fiction" and "Drama."

Refer to the human-in-the-loop guide for details.
```

#### ​Next steps

For deeper customization, check out this tutorial for implementing a SQL agent directly using LangGraph primitives.

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Custom workflow - Docs by LangChain {#doc-15}

**Source:** [https://docs.langchain.com/oss/python/langchain/multi-agent/custom-workflow](https://docs.langchain.com/oss/python/langchain/multi-agent/custom-workflow)

### Custom workflow

Copy page

#### ​Key characteristics

- Complete control over graph structure
- Mix deterministic logic with agentic behavior
- Support for sequential steps, conditional branches, loops, and parallel execution
- Embed other patterns as nodes in your workflow

#### ​When to use

Use custom workflows when standard patterns (subagents, skills, etc.) don’t fit your requirements, you need to mix deterministic logic with agentic behavior, or your use case requires complex routing or multi-stage processing.

Each node in your workflow can be a simple function, an LLM call, or an entire agent with tools. You can also compose other architectures within a custom workflow—for example, embedding a multi-agent system as a single node.

For a complete example of a custom workflow, see the tutorial below.

Tutorial: Build a multi-source knowledge base with routingThe router pattern is an example of a custom workflow. This tutorial walks through building a router that queries GitHub, Notion, and Slack in parallel, then synthesizes results.
Learn more

​Basic implementation

The core insight is that you can call a LangChain agent directly inside any LangGraph node, combining the flexibility of custom workflows with the convenience of pre-built agents:

Copyfrom langchain.agents import create_agent
```python
from langgraph.graph import StateGraph, START, END

agent = create_agent(model="openai:gpt-4o", tools=[...])

def agent_node(state: State) -> dict:
    """A LangGraph node that invokes a LangChain agent."""
    result = agent.invoke({
        "messages": [{"role": "user", "content": state["query"]}]
    })
    return {"answer": result["messages"][-1].content}

# Build a simple workflow
workflow = (
    StateGraph(State)
    .add_node("agent", agent_node)
    .add_edge(START, "agent")
    .add_edge("agent", END)
    .compile()
)

​Example: RAG pipeline

A common use case is combining retrieval with an agent. This example builds a WNBA stats assistant that retrieves from a knowledge base and can fetch live news.

Custom RAG workflowThe workflow demonstrates three types of nodes:
Model node (Rewrite): Rewrites the user query for better retrieval using structured output.
Deterministic node (Retrieve): Performs vector similarity search — no LLM involved.
Agent node (Agent): Reasons over retrieved context and can fetch additional information via tools.
You can use LangGraph state to pass information between workflow steps. This allows each part of your workflow to read and update structured fields, making it easy to share data and context across nodes.Copyfrom typing import TypedDict
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore

class State(TypedDict):
    question: str
    rewritten_query: str
    documents: list[str]
    answer: str

# WNBA knowledge base with rosters, game results, and player stats
embeddings = OpenAIEmbeddings()
vector_store = InMemoryVectorStore(embeddings)
vector_store.add_texts([
    # Rosters
    "New York Liberty 2024 roster: Breanna Stewart, Sabrina Ionescu, Jonquel Jones, Courtney Vandersloot.",
    "Las Vegas Aces 2024 roster: A'ja Wilson, Kelsey Plum, Jackie Young, Chelsea Gray.",
    "Indiana Fever 2024 roster: Caitlin Clark, Aliyah Boston, Kelsey Mitchell, NaLyssa Smith.",
    # Game results
    "2024 WNBA Finals: New York Liberty defeated Minnesota Lynx 3-2 to win the championship.",
    "June 15, 2024: Indiana Fever 85, Chicago Sky 79. Caitlin Clark had 23 points and 8 assists.",
    "August 20, 2024: Las Vegas Aces 92, Phoenix Mercury 84. A'ja Wilson scored 35 points.",
    # Player stats
    "A'ja Wilson 2024 season stats: 26.9 PPG, 11.9 RPG, 2.6 BPG. Won MVP award.",
    "Caitlin Clark 2024 rookie stats: 19.2 PPG, 8.4 APG, 5.7 RPG. Won Rookie of the Year.",
    "Breanna Stewart 2024 stats: 20.4 PPG, 8.5 RPG, 3.5 APG.",
])
retriever = vector_store.as_retriever(search_kwargs={"k": 5})

@tool
def get_latest_news(query: str) -> str:
    """Get the latest WNBA news and updates."""
    # Your news API here
    return "Latest: The WNBA announced expanded playoff format for 2025..."

agent = create_agent(
    model="openai:gpt-4o",
    tools=[get_latest_news],
)

model = ChatOpenAI(model="gpt-4o")

class RewrittenQuery(BaseModel):
    query: str

def rewrite_query(state: State) -> dict:
    """Rewrite the user query for better retrieval."""
    system_prompt = """Rewrite this query to retrieve relevant WNBA information.
The knowledge base contains: team rosters, game results with scores, and player statistics (PPG, RPG, APG).
Focus on specific player names, team names, or stat categories mentioned."""
    response = model.with_structured_output(RewrittenQuery).invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": state["question"]}
    ])
    return {"rewritten_query": response.query}

def retrieve(state: State) -> dict:
    """Retrieve documents based on the rewritten query."""
    docs = retriever.invoke(state["rewritten_query"])
    return {"documents": [doc.page_content for doc in docs]}

def call_agent(state: State) -> dict:
    """Generate answer using retrieved context."""
    context = "\n\n".join(state["documents"])
    prompt = f"Context:\n{context}\n\nQuestion: {state['question']}"
    response = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
    return {"answer": response["messages"][-1].content_blocks}

workflow = (
    StateGraph(State)
    .add_node("rewrite", rewrite_query)
    .add_node("retrieve", retrieve)
    .add_node("agent", call_agent)
    .add_edge(START, "rewrite")
    .add_edge("rewrite", "retrieve")
    .add_edge("retrieve", "agent")
    .add_edge("agent", END)
    .compile()
)

result = workflow.invoke({"question": "Who won the 2024 WNBA Championship?"})
print(result["answer"])

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```

#### Tutorial: Build a multi-source knowledge base with routing

#### ​Basic implementation

The core insight is that you can call a LangChain agent directly inside any LangGraph node, combining the flexibility of custom workflows with the convenience of pre-built agents:

Copyfrom langchain.agents import create_agent
```python
from langgraph.graph import StateGraph, START, END

agent = create_agent(model="openai:gpt-4o", tools=[...])

def agent_node(state: State) -> dict:
    """A LangGraph node that invokes a LangChain agent."""
    result = agent.invoke({
        "messages": [{"role": "user", "content": state["query"]}]
    })
    return {"answer": result["messages"][-1].content}

# Build a simple workflow
workflow = (
    StateGraph(State)
    .add_node("agent", agent_node)
    .add_edge(START, "agent")
    .add_edge("agent", END)
    .compile()
)
```

#### ​Example: RAG pipeline

A common use case is combining retrieval with an agent. This example builds a WNBA stats assistant that retrieves from a knowledge base and can fetch live news.

Custom RAG workflowThe workflow demonstrates three types of nodes:
Model node (Rewrite): Rewrites the user query for better retrieval using structured output.
Deterministic node (Retrieve): Performs vector similarity search — no LLM involved.
Agent node (Agent): Reasons over retrieved context and can fetch additional information via tools.
You can use LangGraph state to pass information between workflow steps. This allows each part of your workflow to read and update structured fields, making it easy to share data and context across nodes.Copyfrom typing import TypedDict
```python
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore

class State(TypedDict):
    question: str
    rewritten_query: str
    documents: list[str]
    answer: str

# WNBA knowledge base with rosters, game results, and player stats
embeddings = OpenAIEmbeddings()
vector_store = InMemoryVectorStore(embeddings)
vector_store.add_texts([
    # Rosters
    "New York Liberty 2024 roster: Breanna Stewart, Sabrina Ionescu, Jonquel Jones, Courtney Vandersloot.",
    "Las Vegas Aces 2024 roster: A'ja Wilson, Kelsey Plum, Jackie Young, Chelsea Gray.",
    "Indiana Fever 2024 roster: Caitlin Clark, Aliyah Boston, Kelsey Mitchell, NaLyssa Smith.",
    # Game results
    "2024 WNBA Finals: New York Liberty defeated Minnesota Lynx 3-2 to win the championship.",
    "June 15, 2024: Indiana Fever 85, Chicago Sky 79. Caitlin Clark had 23 points and 8 assists.",
    "August 20, 2024: Las Vegas Aces 92, Phoenix Mercury 84. A'ja Wilson scored 35 points.",
    # Player stats
    "A'ja Wilson 2024 season stats: 26.9 PPG, 11.9 RPG, 2.6 BPG. Won MVP award.",
    "Caitlin Clark 2024 rookie stats: 19.2 PPG, 8.4 APG, 5.7 RPG. Won Rookie of the Year.",
    "Breanna Stewart 2024 stats: 20.4 PPG, 8.5 RPG, 3.5 APG.",
])
retriever = vector_store.as_retriever(search_kwargs={"k": 5})

@tool
def get_latest_news(query: str) -> str:
    """Get the latest WNBA news and updates."""
    # Your news API here
    return "Latest: The WNBA announced expanded playoff format for 2025..."

agent = create_agent(
    model="openai:gpt-4o",
    tools=[get_latest_news],
)

model = ChatOpenAI(model="gpt-4o")

class RewrittenQuery(BaseModel):
    query: str

def rewrite_query(state: State) -> dict:
    """Rewrite the user query for better retrieval."""
    system_prompt = """Rewrite this query to retrieve relevant WNBA information.
The knowledge base contains: team rosters, game results with scores, and player statistics (PPG, RPG, APG).
Focus on specific player names, team names, or stat categories mentioned."""
    response = model.with_structured_output(RewrittenQuery).invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": state["question"]}
    ])
    return {"rewritten_query": response.query}

def retrieve(state: State) -> dict:
    """Retrieve documents based on the rewritten query."""
    docs = retriever.invoke(state["rewritten_query"])
    return {"documents": [doc.page_content for doc in docs]}

def call_agent(state: State) -> dict:
    """Generate answer using retrieved context."""
    context = "\n\n".join(state["documents"])
    prompt = f"Context:\n{context}\n\nQuestion: {state['question']}"
    response = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
    return {"answer": response["messages"][-1].content_blocks}

workflow = (
    StateGraph(State)
    .add_node("rewrite", rewrite_query)
    .add_node("retrieve", retrieve)
    .add_node("agent", call_agent)
    .add_edge(START, "rewrite")
    .add_edge("rewrite", "retrieve")
    .add_edge("retrieve", "agent")
    .add_edge("agent", END)
    .compile()
)

result = workflow.invoke({"question": "Who won the 2024 WNBA Championship?"})
print(result["answer"])

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```


---

## Build a semantic search engine with LangChain - Docs by LangChain {#doc-16}

**Source:** [https://docs.langchain.com/oss/python/langchain/knowledge-base](https://docs.langchain.com/oss/python/langchain/knowledge-base)

### Build a semantic search engine with LangChain

Copy page

#### ​Overview

This tutorial will familiarize you with LangChain’s document loader, embedding, and vector store abstractions. These abstractions are designed to support retrieval of data—  from (vector) databases and other sources — for integration with LLM workflows. They are important for applications that fetch data to be reasoned over as part of model inference, as in the case of retrieval-augmented generation, or RAG.

Here we will build a search engine over a PDF document. This will allow us to retrieve passages in the PDF that are similar to an input query. The guide also includes a minimal RAG implementation on top of the search engine.

##### ​Concepts

This guide focuses on retrieval of text data. We will cover the following concepts:

- Documents and document loaders;
- Text splitters;
- Embeddings;
- Vector stores and retrievers.

#### ​Setup

##### ​Installation

This tutorial requires the langchain-community and pypdf packages:

pipcondaCopypip install langchain-community pypdf

For more details, see our Installation guide.

##### ​LangSmith

Many of the applications you build with LangChain will contain multiple steps with multiple invocations of LLM calls.
As these applications get more and more complex, it becomes crucial to be able to inspect what exactly is going on inside your chain or agent.
The best way to do this is with LangSmith.

After you sign up at the link above, make sure to set your environment variables to start logging traces:

Copyexport LANGSMITH_TRACING="true"
export LANGSMITH_API_KEY="..."

Or, if in a notebook, you can set them with:

Copyimport getpass
```python
import os

os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = getpass.getpass()
```

#### ​1. Documents and Document Loaders

LangChain implements a Document abstraction, which is intended to represent a unit of text and associated metadata. It has three attributes:

- page_content: a string representing the content;
- metadata: a dict containing arbitrary metadata;
- id: (optional) a string identifier for the document.
The metadata attribute can capture information about the source of the document, its relationship to other documents, and other information. Note that an individual Document object often represents a chunk of a larger document.

We can generate sample documents when desired:

Copyfrom langchain_core.documents import Document

documents = [
    Document(
        page_content="Dogs are great companions, known for their loyalty and friendliness.",
        metadata={"source": "mammal-pets-doc"},
    ),
    Document(
        page_content="Cats are independent pets that often enjoy their own space.",
        metadata={"source": "mammal-pets-doc"},
    ),
]

However, the LangChain ecosystem implements document loaders that integrate with hundreds of common sources. This makes it easy to incorporate data from these sources into your AI application.

##### ​Loading documents

Let’s load a PDF into a sequence of Document objects. Here is a sample PDF — a 10-k filing for Nike from 2023. We can consult the LangChain documentation for available PDF document loaders.

Copyfrom langchain_community.document_loaders import PyPDFLoader

file_path = "../example_data/nke-10k-2023.pdf"
loader = PyPDFLoader(file_path)

docs = loader.load()

print(len(docs))

Copy107

PyPDFLoader loads one Document object per PDF page. For each, we can easily access:

- The string content of the page;
- Metadata containing the file name and page number.
Copyprint(f"{docs[0].page_content[:200]}\n")
print(docs[0].metadata)

CopyTable of Contents
UNITED STATES
SECURITIES AND EXCHANGE COMMISSION
Washington, D.C. 20549
FORM 10-K
(Mark One)
☑ ANNUAL REPORT PURSUANT TO SECTION 13 OR 15(D) OF THE SECURITIES EXCHANGE ACT OF 1934
FO

{'source': '../example_data/nke-10k-2023.pdf', 'page': 0}

##### ​Splitting

For both information retrieval and downstream question-answering purposes, a page may be too coarse a representation. Our goal in the end will be to retrieve Document objects that answer an input query, and further splitting our PDF will help ensure that the meanings of relevant portions of the document are not “washed out” by surrounding text.

We can use text splitters for this purpose. Here we will use a simple text splitter that partitions based on characters. We will split our documents into chunks of 1000 characters
with 200 characters of overlap between chunks. The overlap helps
mitigate the possibility of separating a statement from important
context related to it. We use the
RecursiveCharacterTextSplitter,
which will recursively split the document using common separators like
new lines until each chunk is the appropriate size. This is the
recommended text splitter for generic text use cases.

We set add_start_index=True so that the character index where each
split Document starts within the initial Document is preserved as
metadata attribute “start_index”.

Copyfrom langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=200, add_start_index=True
)
all_splits = text_splitter.split_documents(docs)

print(len(all_splits))

Copy514

#### ​2. Embeddings

Vector search is a common way to store and search over unstructured data (such as unstructured text). The idea is to store numeric vectors that are associated with the text. Given a query, we can embed it as a vector of the same dimension and use vector similarity metrics (such as cosine similarity) to identify related text.

LangChain supports embeddings from dozens of providers. These models specify how text should be converted into a numeric vector. Let’s select a model:

OpenAI Azure Google Gemini Google Vertex AWS HuggingFace Ollama Cohere MistralAI Nomic NVIDIA Voyage AI IBM watsonx Fake IsaacusCopypip install -U "langchain-openai"
Copyimport getpass
```python
import os

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
Copypip install -U "langchain-openai"
Copyimport getpass
import os

if not os.environ.get("AZURE_OPENAI_API_KEY"):
    os.environ["AZURE_OPENAI_API_KEY"] = getpass.getpass("Enter API key for Azure: ")

from langchain_openai import AzureOpenAIEmbeddings

embeddings = AzureOpenAIEmbeddings(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
)
Copypip install -qU langchain-google-genai
Copyimport getpass
import os

if not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter API key for Google Gemini: ")

from langchain_google_genai import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
Copypip install -qU langchain-google-vertexai
Copyfrom langchain_google_vertexai import VertexAIEmbeddings

embeddings = VertexAIEmbeddings(model="text-embedding-005")
Copypip install -qU langchain-aws
Copyfrom langchain_aws import BedrockEmbeddings

embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0")
Copypip install -qU langchain-huggingface
Copyfrom langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
Copypip install -qU langchain-ollama
Copyfrom langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="llama3")
Copypip install -qU langchain-cohere
Copyimport getpass
import os

if not os.environ.get("COHERE_API_KEY"):
    os.environ["COHERE_API_KEY"] = getpass.getpass("Enter API key for Cohere: ")

from langchain_cohere import CohereEmbeddings

embeddings = CohereEmbeddings(model="embed-english-v3.0")
Copypip install -qU langchain-mistralai
Copyimport getpass
import os

if not os.environ.get("MISTRALAI_API_KEY"):
    os.environ["MISTRALAI_API_KEY"] = getpass.getpass("Enter API key for MistralAI: ")

from langchain_mistralai import MistralAIEmbeddings

embeddings = MistralAIEmbeddings(model="mistral-embed")
Copypip install -qU langchain-nomic
Copyimport getpass
import os

if not os.environ.get("NOMIC_API_KEY"):
    os.environ["NOMIC_API_KEY"] = getpass.getpass("Enter API key for Nomic: ")

from langchain_nomic import NomicEmbeddings

embeddings = NomicEmbeddings(model="nomic-embed-text-v1.5")
Copypip install -qU langchain-nvidia-ai-endpoints
Copyimport getpass
import os

if not os.environ.get("NVIDIA_API_KEY"):
    os.environ["NVIDIA_API_KEY"] = getpass.getpass("Enter API key for NVIDIA: ")

from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

embeddings = NVIDIAEmbeddings(model="NV-Embed-QA")
Copypip install -qU langchain-voyageai
Copyimport getpass
import os

if not os.environ.get("VOYAGE_API_KEY"):
    os.environ["VOYAGE_API_KEY"] = getpass.getpass("Enter API key for Voyage AI: ")

from langchain-voyageai import VoyageAIEmbeddings

embeddings = VoyageAIEmbeddings(model="voyage-3")
Copypip install -qU langchain-ibm
Copyimport getpass
import os

if not os.environ.get("WATSONX_APIKEY"):
    os.environ["WATSONX_APIKEY"] = getpass.getpass("Enter API key for IBM watsonx: ")

from langchain_ibm import WatsonxEmbeddings

embeddings = WatsonxEmbeddings(
    model_id="ibm/slate-125m-english-rtrvr",
    url="https://us-south.ml.cloud.ibm.com",
    project_id="<WATSONX PROJECT_ID>",
)
Copypip install -qU langchain-core
Copyfrom langchain_core.embeddings import DeterministicFakeEmbedding

embeddings = DeterministicFakeEmbedding(size=4096)
Copypip install -qU langchain-isaacus
Copyimport getpass
import os

if not os.environ.get("ISAACUS_API_KEY"):
os.environ["ISAACUS_API_KEY"] = getpass.getpass("Enter API key for Isaacus: ")

from langchain_isaacus import IsaacusEmbeddings

embeddings = IsaacusEmbeddings(model="kanon-2-embedder")

Copyvector_1 = embeddings.embed_query(all_splits[0].page_content)
vector_2 = embeddings.embed_query(all_splits[1].page_content)

assert len(vector_1) == len(vector_2)
print(f"Generated vectors of length {len(vector_1)}\n")
print(vector_1[:10])

CopyGenerated vectors of length 1536

[-0.008586574345827103, -0.03341241180896759, -0.008936782367527485, -0.0036674530711025, 0.010564599186182022, 0.009598285891115665, -0.028587326407432556, -0.015824200585484505, 0.0030416189692914486, -0.012899317778646946]

Armed with a model for generating text embeddings, we can next store them in a special data structure that supports efficient similarity search.
```

#### ​3. Vector stores

LangChain VectorStore objects contain methods for adding text and Document objects to the store, and querying them using various similarity metrics. They are often initialized with embedding models, which determine how text data is translated to numeric vectors.

LangChain includes a suite of integrations with different vector store technologies. Some vector stores are hosted by a provider (e.g., various cloud providers) and require specific credentials to use; some (such as Postgres) run in separate infrastructure that can be run locally or via a third-party; others can run in-memory for lightweight workloads. Let’s select a vector store:

In-memory Amazon OpenSearch AstraDB Chroma FAISS Milvus MongoDB PGVector PGVectorStore Pinecone QdrantCopypip install -U "langchain-core"
Copyfrom langchain_core.vectorstores import InMemoryVectorStore

vector_store = InMemoryVectorStore(embeddings)
Copypip install -qU  boto3
Copyfrom opensearchpy import RequestsHttpConnection

service = "es"  # must set the service as 'es'
region = "us-east-2"
credentials = boto3.Session(
    aws_access_key_id="xxxxxx", aws_secret_access_key="xxxxx"
).get_credentials()
awsauth = AWS4Auth("xxxxx", "xxxxxx", region, service, session_token=credentials.token)

vector_store = OpenSearchVectorSearch.from_documents(
    docs,
    embeddings,
    opensearch_url="host url",
    http_auth=awsauth,
    timeout=300,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    index_name="test-index",
)
Copypip install -U "langchain-astradb"
Copyfrom langchain_astradb import AstraDBVectorStore

vector_store = AstraDBVectorStore(
    embedding=embeddings,
    api_endpoint=ASTRA_DB_API_ENDPOINT,
    collection_name="astra_vector_langchain",
    token=ASTRA_DB_APPLICATION_TOKEN,
    namespace=ASTRA_DB_NAMESPACE,
)
Copypip install -qU langchain-chroma
Copyfrom langchain_chroma import Chroma

vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
)
Copypip install -qU langchain-community faiss-cpu
Copyimport faiss
```python
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS

embedding_dim = len(embeddings.embed_query("hello world"))
index = faiss.IndexFlatL2(embedding_dim)

vector_store = FAISS(
    embedding_function=embeddings,
    index=index,
    docstore=InMemoryDocstore(),
    index_to_docstore_id={},
)
Copypip install -qU langchain-milvus
Copyfrom langchain_milvus import Milvus

URI = "./milvus_example.db"

vector_store = Milvus(
    embedding_function=embeddings,
    connection_args={"uri": URI},
    index_params={"index_type": "FLAT", "metric_type": "L2"},
)
Copypip install -qU langchain-mongodb
Copyfrom langchain_mongodb import MongoDBAtlasVectorSearch

vector_store = MongoDBAtlasVectorSearch(
    embedding=embeddings,
    collection=MONGODB_COLLECTION,
    index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
    relevance_score_fn="cosine",
)
Copypip install -qU langchain-postgres
Copyfrom langchain_postgres import PGVector

vector_store = PGVector(
    embeddings=embeddings,
    collection_name="my_docs",
    connection="postgresql+psycopg://...",
)
Copypip install -qU langchain-postgres
Copyfrom langchain_postgres import PGEngine, PGVectorStore

pg_engine = PGEngine.from_connection_string(
    url="postgresql+psycopg://..."
)

vector_store = PGVectorStore.create_sync(
    engine=pg_engine,
    table_name='test_table',
    embedding_service=embedding
)
Copypip install -qU langchain-pinecone
Copyfrom langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

pc = Pinecone(api_key=...)
index = pc.Index(index_name)

vector_store = PineconeVectorStore(embedding=embeddings, index=index)
Copypip install -qU langchain-qdrant
Copyfrom qdrant_client.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

client = QdrantClient(":memory:")

vector_size = len(embeddings.embed_query("sample text"))

if not client.collection_exists("test"):
    client.create_collection(
        collection_name="test",
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
    )
vector_store = QdrantVectorStore(
    client=client,
    collection_name="test",
    embedding=embeddings,
)

Having instantiated our vector store, we can now index the documents.

Copyids = vector_store.add_documents(documents=all_splits)

Note that most vector store implementations will allow you to connect to an existing vector store—  e.g., by providing a client, index name, or other information. See the documentation for a specific integration for more detail.

Once we’ve instantiated a VectorStore that contains documents, we can query it. VectorStore includes methods for querying:

- Synchronously and asynchronously;
- By string query and by vector;
- With and without returning similarity scores;
- By similarity and maximum marginal relevance (to balance similarity with query to diversity in retrieved results).
The methods will generally include a list of Document objects in their outputs.

Usage

Embeddings typically represent text as a “dense” vector such that texts with similar meanings are geometrically close. This lets us retrieve relevant information just by passing in a question, without knowledge of any specific key-terms used in the document.

Return documents based on similarity to a string query:

Copyresults = vector_store.similarity_search(
    "How many distribution centers does Nike have in the US?"
)

print(results[0])

Copypage_content='direct to consumer operations sell products through the following number of retail stores in the United States:
U.S. RETAIL STORES NUMBER
NIKE Brand factory stores 213
NIKE Brand in-line stores (including employee-only stores) 74
Converse stores (including factory stores) 82
TOTAL 369
In the United States, NIKE has eight significant distribution centers. Refer to Item 2. Properties for further information.
2023 FORM 10-K 2' metadata={'page': 4, 'source': '../example_data/nke-10k-2023.pdf', 'start_index': 3125}

Async query:

Copyresults = await vector_store.asimilarity_search("When was Nike incorporated?")

print(results[0])

Copypage_content='Table of Contents
PART I
ITEM 1. BUSINESS
GENERAL
NIKE, Inc. was incorporated in 1967 under the laws of the State of Oregon. As used in this Annual Report on Form 10-K (this "Annual Report"), the terms "we," "us," "our,"
"NIKE" and the "Company" refer to NIKE, Inc. and its predecessors, subsidiaries and affiliates, collectively, unless the context indicates otherwise.
Our principal business activity is the design, development and worldwide marketing and selling of athletic footwear, apparel, equipment, accessories and services. NIKE is
the largest seller of athletic footwear and apparel in the world. We sell our products through NIKE Direct operations, which are comprised of both NIKE-owned retail stores
and sales through our digital platforms (also referred to as "NIKE Brand Digital"), to retail accounts and to a mix of independent distributors, licensees and sales' metadata={'page': 3, 'source': '../example_data/nke-10k-2023.pdf', 'start_index': 0}

Return scores:

Copy# Note that providers implement different scores; the score here
# is a distance metric that varies inversely with similarity.

results = vector_store.similarity_search_with_score("What was Nike's revenue in 2023?")
doc, score = results[0]
print(f"Score: {score}\n")
print(doc)

CopyScore: 0.23699893057346344

page_content='Table of Contents
FISCAL 2023 NIKE BRAND REVENUE HIGHLIGHTS
The following tables present NIKE Brand revenues disaggregated by reportable operating segment, distribution channel and major product line:
FISCAL 2023 COMPARED TO FISCAL 2022
•NIKE, Inc. Revenues were $51.2 billion in fiscal 2023, which increased 10% and 16% compared to fiscal 2022 on a reported and currency-neutral basis, respectively.
The increase was due to higher revenues in North America, Europe, Middle East & Africa ("EMEA"), APLA and Greater China, which contributed approximately 7, 6,
2 and 1 percentage points to NIKE, Inc. Revenues, respectively.
•NIKE Brand revenues, which represented over 90% of NIKE, Inc. Revenues, increased 10% and 16% on a reported and currency-neutral basis, respectively. This
increase was primarily due to higher revenues in Men's, the Jordan Brand, Women's and Kids' which grew 17%, 35%,11% and 10%, respectively, on a wholesale
equivalent basis.' metadata={'page': 35, 'source': '../example_data/nke-10k-2023.pdf', 'start_index': 0}

Return documents based on similarity to an embedded query:

Copyembedding = embeddings.embed_query("How were Nike's margins impacted in 2023?")

results = vector_store.similarity_search_by_vector(embedding)
print(results[0])

Copypage_content='Table of Contents
GROSS MARGIN
FISCAL 2023 COMPARED TO FISCAL 2022
For fiscal 2023, our consolidated gross profit increased 4% to $22,292 million compared to $21,479 million for fiscal 2022. Gross margin decreased 250 basis points to
43.5% for fiscal 2023 compared to 46.0% for fiscal 2022 due to the following:
*Wholesale equivalent
The decrease in gross margin for fiscal 2023 was primarily due to:
•Higher NIKE Brand product costs, on a wholesale equivalent basis, primarily due to higher input costs and elevated inbound freight and logistics costs as well as
product mix;
•Lower margin in our NIKE Direct business, driven by higher promotional activity to liquidate inventory in the current period compared to lower promotional activity in
the prior period resulting from lower available inventory supply;
•Unfavorable changes in net foreign currency exchange rates, including hedges; and
•Lower off-price margin, on a wholesale equivalent basis.
This was partially offset by:' metadata={'page': 36, 'source': '../example_data/nke-10k-2023.pdf', 'start_index': 0}

Learn more:

- API Reference
- Integration-specific docs
```

#### ​4. Retrievers

LangChain VectorStore objects do not subclass Runnable. LangChain Retrievers are Runnables, so they implement a standard set of methods (e.g., synchronous and asynchronous invoke and batch operations). Although we can construct retrievers from vector stores, retrievers can interface with non-vector store sources of data, as well (such as external APIs).

We can create a simple version of this ourselves, without subclassing Retriever. If we choose what method we wish to use to retrieve documents, we can create a runnable easily. Below we will build one around the similarity_search method:

Copyfrom typing import List

```python
from langchain_core.documents import Document
from langchain_core.runnables import chain

@chain
def retriever(query: str) -> List[Document]:
    return vector_store.similarity_search(query, k=1)

retriever.batch(
    [
        "How many distribution centers does Nike have in the US?",
        "When was Nike incorporated?",
    ],
)

Copy[[Document(metadata={'page': 4, 'source': '../example_data/nke-10k-2023.pdf', 'start_index': 3125}, page_content='direct to consumer operations sell products through the following number of retail stores in the United States:\nU.S. RETAIL STORES NUMBER\nNIKE Brand factory stores 213 \nNIKE Brand in-line stores (including employee-only stores) 74 \nConverse stores (including factory stores) 82 \nTOTAL 369 \nIn the United States, NIKE has eight significant distribution centers. Refer to Item 2. Properties for further information.\n2023 FORM 10-K 2')],
 [Document(metadata={'page': 3, 'source': '../example_data/nke-10k-2023.pdf', 'start_index': 0}, page_content='Table of Contents\nPART I\nITEM 1. BUSINESS\nGENERAL\nNIKE, Inc. was incorporated in 1967 under the laws of the State of Oregon. As used in this Annual Report on Form 10-K (this "Annual Report"), the terms "we," "us," "our,"\n"NIKE" and the "Company" refer to NIKE, Inc. and its predecessors, subsidiaries and affiliates, collectively, unless the context indicates otherwise.\nOur principal business activity is the design, development and worldwide marketing and selling of athletic footwear, apparel, equipment, accessories and services. NIKE is\nthe largest seller of athletic footwear and apparel in the world. We sell our products through NIKE Direct operations, which are comprised of both NIKE-owned retail stores\nand sales through our digital platforms (also referred to as "NIKE Brand Digital"), to retail accounts and to a mix of independent distributors, licensees and sales')]]

Vectorstores implement an as_retriever method that will generate a Retriever, specifically a VectorStoreRetriever. These retrievers include specific search_type and search_kwargs attributes that identify what methods of the underlying vector store to call, and how to parameterize them. For instance, we can replicate the above with the following:

Copyretriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 1},
)

retriever.batch(
    [
        "How many distribution centers does Nike have in the US?",
        "When was Nike incorporated?",
    ],
)

Copy[[Document(metadata={'page': 4, 'source': '../example_data/nke-10k-2023.pdf', 'start_index': 3125}, page_content='direct to consumer operations sell products through the following number of retail stores in the United States:\nU.S. RETAIL STORES NUMBER\nNIKE Brand factory stores 213 \nNIKE Brand in-line stores (including employee-only stores) 74 \nConverse stores (including factory stores) 82 \nTOTAL 369 \nIn the United States, NIKE has eight significant distribution centers. Refer to Item 2. Properties for further information.\n2023 FORM 10-K 2')],
 [Document(metadata={'page': 3, 'source': '../example_data/nke-10k-2023.pdf', 'start_index': 0}, page_content='Table of Contents\nPART I\nITEM 1. BUSINESS\nGENERAL\nNIKE, Inc. was incorporated in 1967 under the laws of the State of Oregon. As used in this Annual Report on Form 10-K (this "Annual Report"), the terms "we," "us," "our,"\n"NIKE" and the "Company" refer to NIKE, Inc. and its predecessors, subsidiaries and affiliates, collectively, unless the context indicates otherwise.\nOur principal business activity is the design, development and worldwide marketing and selling of athletic footwear, apparel, equipment, accessories and services. NIKE is\nthe largest seller of athletic footwear and apparel in the world. We sell our products through NIKE Direct operations, which are comprised of both NIKE-owned retail stores\nand sales through our digital platforms (also referred to as "NIKE Brand Digital"), to retail accounts and to a mix of independent distributors, licensees and sales')]]

VectorStoreRetriever supports search types of "similarity" (default), "mmr" (maximum marginal relevance, described above), and "similarity_score_threshold". We can use the latter to threshold documents output by the retriever by similarity score.

Retrievers can easily be incorporated into more complex applications, such as retrieval-augmented generation (RAG) applications that combine a given question with retrieved context into a prompt for a LLM. To learn more about building such an application, check out the RAG tutorial tutorial.
```

#### ​Next steps

You’ve now seen how to build a semantic search engine over a PDF document.

For more on document loaders:

- Overview
- Available integrations
For more on embeddings:

- Overview
- Available integrations
For more on vector stores:

- Overview
- Available integrations
For more on RAG, see:

- Build a Retrieval Augmented Generation (RAG) App
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Multi-agent - Docs by LangChain {#doc-17}

**Source:** [https://docs.langchain.com/oss/python/langchain/multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

### Multi-agent

Copy page

#### ​Why multi-agent?

When developers say they need “multi-agent,” they’re usually looking for one or more of these capabilities:

- Context management: Provide specialized knowledge without overwhelming the model’s context window. If context were infinite and latency zero, you could dump all knowledge into a single prompt — but since it’s not, you need patterns to selectively surface relevant information.
- Distributed development: Allow different teams to develop and maintain capabilities independently, composing them into a larger system with clear boundaries.
- Parallelization: Spawn specialized workers for subtasks and execute them concurrently for faster results.
Multi-agent patterns are particularly valuable when a single agent has too many tools and makes poor decisions about which to use, when tasks require specialized knowledge with extensive context (long prompts and domain-specific tools), or when you need to enforce sequential constraints that unlock capabilities only after certain conditions are met.

At the center of multi-agent design is context engineering—deciding what information each agent sees. The quality of your system depends on ensuring each agent has access to the right data for its task.

#### ​Patterns

Here are the main patterns for building multi-agent systems, each suited to different use cases:

PatternHow it worksSubagentsA main agent coordinates subagents as tools. All routing passes through the main agent, which decides when and how to invoke each subagent.HandoffsBehavior changes dynamically based on state. Tool calls update a state variable that triggers routing or configuration changes, switching agents or adjusting the current agent’s tools and prompt.SkillsSpecialized prompts and knowledge loaded on-demand. A single agent stays in control while loading context from skills as needed.RouterA routing step classifies input and directs it to one or more specialized agents. Results are synthesized into a combined response.Custom workflowBuild bespoke execution flows with LangGraph, mixing deterministic logic and agentic behavior. Embed other patterns as nodes in your workflow.

##### ​Choosing a pattern

Use this table to match your requirements to the right pattern:

PatternDistributed developmentParallelizationMulti-hopDirect user interactionSubagents⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐Handoffs——⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐Skills⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐Router⭐⭐⭐⭐⭐⭐⭐⭐—⭐⭐⭐

- Distributed development: Can different teams maintain components independently?
- Parallelization: Can multiple agents execute concurrently?
- Multi-hop: Does the pattern support calling multiple subagents in series?
- Direct user interaction: Can subagents converse directly with the user?
You can mix patterns! For example, a subagents architecture can invoke tools that invoke custom workflows or router agents. Subagents can even use the skills pattern to load context on-demand. The possibilities are endless!

##### ​Visual overview

Subagents Handoffs Skills RouterA main agent coordinates subagents as tools. All routing passes through the main agent.Agents transfer control to each other via tool calls. Each agent can hand off to others or respond directly to the user.A single agent loads specialized prompts and knowledge on-demand while staying in control.A routing step classifies input and directs it to specialized agents. Results are synthesized.

#### ​Performance comparison

Different patterns have different performance characteristics. Understanding these tradeoffs helps you choose the right pattern for your latency and cost requirements.

Key metrics:

- Model calls: Number of LLM invocations. More calls = higher latency (especially if sequential) and higher per-request API costs.
- Tokens processed: Total context window usage across all calls. More tokens = higher processing costs and potential context limits.

##### ​One-shot request

User: “Buy coffee”

A specialized coffee agent/skill can call a buy_coffee tool.

PatternModel callsBest fitSubagents4Handoffs3✅Skills3✅Router3✅

Subagents Handoffs Skills Router4 model calls:3 model calls:3 model calls:3 model calls:

Key insight: Handoffs, Skills, and Router are most efficient for single tasks (3 calls each). Subagents adds one extra call because results flow back through the main agent—this overhead provides centralized control.

##### ​Repeat request

Turn 1: “Buy coffee”
Turn 2: “Buy coffee again”

The user repeats the same request in the same conversation.

PatternTurn 2 callsTotal (both turns)Best fitSubagents48Handoffs25✅Skills25✅Router36

Subagents Handoffs Skills Router4 calls again → 8 total
Subagents are stateless by design—each invocation follows the same flow
The main agent maintains conversation context, but subagents start fresh each time
This provides strong context isolation but repeats the full flow
2 calls → 5 total
The coffee agent is still active from turn 1 (state persists)
No handoff needed—agent directly calls buy_coffee tool (call 1)
Agent responds to user (call 2)
Saves 1 call by skipping the handoff
2 calls → 5 total
The skill context is already loaded in conversation history
No need to reload—agent directly calls buy_coffee tool (call 1)
Agent responds to user (call 2)
Saves 1 call by reusing loaded skill
3 calls again → 6 total
Routers are stateless—each request requires an LLM routing call
Turn 2: Router LLM call (1) → Milk agent calls buy_coffee (2) → Milk agent responds (3)
Can be optimized by wrapping as a tool in a stateful agent

Key insight: Stateful patterns (Handoffs, Skills) save 40-50% of calls on repeat requests. Subagents maintain consistent cost per request—this stateless design provides strong context isolation but at the cost of repeated model calls.

##### ​Multi-domain

User: “Compare Python, JavaScript, and Rust for web development”

Each language agent/skill contains ~2000 tokens of documentation. All patterns can make parallel tool calls.

PatternModel callsTotal tokensBest fitSubagents5~9K✅Handoffs7+~14K+Skills3~15KRouter5~9K✅

Subagents Handoffs Skills Router5 calls, ~9K tokensEach subagent works in isolation with only its relevant context. Total: 9K tokens.7+ calls, ~14K+ tokensHandoffs executes sequentially—can’t research all three languages in parallel. Growing conversation history adds overhead. Total: ~14K+ tokens.3 calls, ~15K tokensAfter loading, every subsequent call processes all 6K tokens of skill documentation. Subagents processes 67% fewer tokens overall due to context isolation. Total: 15K tokens.5 calls, ~9K tokensRouter uses an LLM for routing, then invokes agents in parallel. Similar to Subagents but with explicit routing step. Total: 9K tokens.

Key insight: For multi-domain tasks, patterns with parallel execution (Subagents, Router) are most efficient. Skills has fewer calls but high token usage due to context accumulation. Handoffs is inefficient here—it must execute sequentially and can’t leverage parallel tool calling for consulting multiple domains simultaneously.

##### ​Summary

Here’s how patterns compare across all three scenarios:

PatternOne-shotRepeat requestMulti-domainSubagents4 calls8 calls (4+4)5 calls, 9K tokensHandoffs3 calls5 calls (3+2)7+ calls, 14K+ tokensSkills3 calls5 calls (3+2)3 calls, 15K tokensRouter3 calls6 calls (3+3)5 calls, 9K tokens

Choosing a pattern:

Optimize forSubagentsHandoffsSkillsRouterSingle requests✅✅✅Repeat requests✅✅Parallel execution✅✅Large-context domains✅✅Simple, focused tasks✅

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Build a RAG agent with LangChain - Docs by LangChain {#doc-18}

**Source:** [https://docs.langchain.com/oss/python/langchain/rag](https://docs.langchain.com/oss/python/langchain/rag)

### Build a RAG agent with LangChain

Copy page

#### ​Overview

One of the most powerful applications enabled by LLMs is sophisticated question-answering (Q&A) chatbots. These are applications that can answer questions about specific source information. These applications use a technique known as Retrieval Augmented Generation, or RAG.

This tutorial will show how to build a simple Q&A application over an unstructured text data source. We will demonstrate:

- A RAG agent that executes searches with a simple tool. This is a good general-purpose implementation.
- A two-step RAG chain that uses just a single LLM call per query. This is a fast and effective method for simple queries.

##### ​Concepts

We will cover the following concepts:

- Indexing: a pipeline for ingesting data from a source and indexing it. This usually happens in a separate process.
- Retrieval and generation: the actual RAG process, which takes the user query at run time and retrieves the relevant data from the index, then passes that to the model.
Once we’ve indexed our data, we will use an agent as our orchestration framework to implement the retrieval and generation steps.

The indexing portion of this tutorial will largely follow the semantic search tutorial.If your data is already available for search (i.e., you have a function to execute a search), or you’re comfortable with the content from that tutorial, feel free to skip to the section on retrieval and generation

##### ​Preview

In this guide we’ll build an app that answers questions about the website’s content. The specific website we will use is the LLM Powered Autonomous Agents blog post by Lilian Weng, which allows us to ask questions about the contents of the post.

We can create a simple indexing pipeline and RAG chain to do this in ~40 lines of code. See below for the full code snippet:

Expand for full code snippetCopyimport bs4
```python
from langchain.agents import AgentState, create_agent
from langchain_community.document_loaders import WebBaseLoader
from langchain.messages import MessageLikeRepresentation
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load and chunk contents of the blog
loader = WebBaseLoader(
    web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
    bs_kwargs=dict(
        parse_only=bs4.SoupStrainer(
            class_=("post-content", "post-title", "post-header")
        )
    ),
)
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
all_splits = text_splitter.split_documents(docs)

# Index chunks
_ = vector_store.add_documents(documents=all_splits)

# Construct a tool for retrieving context
@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve information to help answer a query."""
    retrieved_docs = vector_store.similarity_search(query, k=2)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs

tools = [retrieve_context]
# If desired, specify custom instructions
prompt = (
    "You have access to a tool that retrieves context from a blog post. "
    "Use the tool to help answer user queries."
)
agent = create_agent(model, tools, system_prompt=prompt)
Copyquery = "What is task decomposition?"
for step in agent.stream(
    {"messages": [{"role": "user", "content": query}]},
    stream_mode="values",
):
    step["messages"][-1].pretty_print()
Copy================================ Human Message =================================

What is task decomposition?
================================== Ai Message ==================================
Tool Calls:
  retrieve_context (call_xTkJr8njRY0geNz43ZvGkX0R)
 Call ID: call_xTkJr8njRY0geNz43ZvGkX0R
  Args:
    query: task decomposition
================================= Tool Message =================================
Name: retrieve_context

Source: {'source': 'https://lilianweng.github.io/posts/2023-06-23-agent/'}
Content: Task decomposition can be done by...

Source: {'source': 'https://lilianweng.github.io/posts/2023-06-23-agent/'}
Content: Component One: Planning...
================================== Ai Message ==================================

Task decomposition refers to...
Check out the LangSmith trace.
```

#### ​Setup

##### ​Installation

This tutorial requires these langchain dependencies:

pipuvCopypip install langchain langchain-text-splitters langchain-community bs4

For more details, see our Installation guide.

##### ​LangSmith

Many of the applications you build with LangChain will contain multiple steps with multiple invocations of LLM calls. As these applications get more complex, it becomes crucial to be able to inspect what exactly is going on inside your chain or agent. The best way to do this is with LangSmith.

After you sign up at the link above, make sure to set your environment variables to start logging traces:

Copyexport LANGSMITH_TRACING="true"
export LANGSMITH_API_KEY="..."

Or, set them in Python:

Copyimport getpass
```python
import os

os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = getpass.getpass()
```

##### ​Components

We will need to select three components from LangChain’s suite of integrations.

Select a chat model:

OpenAI Anthropic Azure Google Gemini AWS Bedrock HuggingFace👉 Read the OpenAI chat model integration docsCopypip install -U "langchain[openai]"
init_chat_modelModel ClassCopyimport os
```python
from langchain.chat_models import init_chat_model

os.environ["OPENAI_API_KEY"] = "sk-..."

model = init_chat_model("gpt-4.1")
👉 Read the Anthropic chat model integration docsCopypip install -U "langchain[anthropic]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["ANTHROPIC_API_KEY"] = "sk-..."

model = init_chat_model("claude-sonnet-4-5-20250929")
👉 Read the Azure chat model integration docsCopypip install -U "langchain[openai]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["AZURE_OPENAI_API_KEY"] = "..."
os.environ["AZURE_OPENAI_ENDPOINT"] = "..."
os.environ["OPENAI_API_VERSION"] = "2025-03-01-preview"

model = init_chat_model(
    "azure_openai:gpt-4.1",
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
)
👉 Read the Google GenAI chat model integration docsCopypip install -U "langchain[google-genai]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["GOOGLE_API_KEY"] = "..."

model = init_chat_model("google_genai:gemini-2.5-flash-lite")
👉 Read the AWS Bedrock chat model integration docsCopypip install -U "langchain[aws]"
init_chat_modelModel ClassCopyfrom langchain.chat_models import init_chat_model

# Follow the steps here to configure your credentials:
# https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html

model = init_chat_model(
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
    model_provider="bedrock_converse",
)
👉 Read the HuggingFace chat model integration docsCopypip install -U "langchain[huggingface]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["HUGGINGFACEHUB_API_TOKEN"] = "hf_..."

model = init_chat_model(
    "microsoft/Phi-3-mini-4k-instruct",
    model_provider="huggingface",
    temperature=0.7,
    max_tokens=1024,
)

Select an embeddings model:

OpenAI Azure Google Gemini Google Vertex AWS HuggingFace Ollama Cohere MistralAI Nomic NVIDIA Voyage AI IBM watsonx Fake IsaacusCopypip install -U "langchain-openai"
Copyimport getpass
import os

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
Copypip install -U "langchain-openai"
Copyimport getpass
import os

if not os.environ.get("AZURE_OPENAI_API_KEY"):
    os.environ["AZURE_OPENAI_API_KEY"] = getpass.getpass("Enter API key for Azure: ")

from langchain_openai import AzureOpenAIEmbeddings

embeddings = AzureOpenAIEmbeddings(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
)
Copypip install -qU langchain-google-genai
Copyimport getpass
import os

if not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter API key for Google Gemini: ")

from langchain_google_genai import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
Copypip install -qU langchain-google-vertexai
Copyfrom langchain_google_vertexai import VertexAIEmbeddings

embeddings = VertexAIEmbeddings(model="text-embedding-005")
Copypip install -qU langchain-aws
Copyfrom langchain_aws import BedrockEmbeddings

embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0")
Copypip install -qU langchain-huggingface
Copyfrom langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
Copypip install -qU langchain-ollama
Copyfrom langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="llama3")
Copypip install -qU langchain-cohere
Copyimport getpass
import os

if not os.environ.get("COHERE_API_KEY"):
    os.environ["COHERE_API_KEY"] = getpass.getpass("Enter API key for Cohere: ")

from langchain_cohere import CohereEmbeddings

embeddings = CohereEmbeddings(model="embed-english-v3.0")
Copypip install -qU langchain-mistralai
Copyimport getpass
import os

if not os.environ.get("MISTRALAI_API_KEY"):
    os.environ["MISTRALAI_API_KEY"] = getpass.getpass("Enter API key for MistralAI: ")

from langchain_mistralai import MistralAIEmbeddings

embeddings = MistralAIEmbeddings(model="mistral-embed")
Copypip install -qU langchain-nomic
Copyimport getpass
import os

if not os.environ.get("NOMIC_API_KEY"):
    os.environ["NOMIC_API_KEY"] = getpass.getpass("Enter API key for Nomic: ")

from langchain_nomic import NomicEmbeddings

embeddings = NomicEmbeddings(model="nomic-embed-text-v1.5")
Copypip install -qU langchain-nvidia-ai-endpoints
Copyimport getpass
import os

if not os.environ.get("NVIDIA_API_KEY"):
    os.environ["NVIDIA_API_KEY"] = getpass.getpass("Enter API key for NVIDIA: ")

from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

embeddings = NVIDIAEmbeddings(model="NV-Embed-QA")
Copypip install -qU langchain-voyageai
Copyimport getpass
import os

if not os.environ.get("VOYAGE_API_KEY"):
    os.environ["VOYAGE_API_KEY"] = getpass.getpass("Enter API key for Voyage AI: ")

from langchain-voyageai import VoyageAIEmbeddings

embeddings = VoyageAIEmbeddings(model="voyage-3")
Copypip install -qU langchain-ibm
Copyimport getpass
import os

if not os.environ.get("WATSONX_APIKEY"):
    os.environ["WATSONX_APIKEY"] = getpass.getpass("Enter API key for IBM watsonx: ")

from langchain_ibm import WatsonxEmbeddings

embeddings = WatsonxEmbeddings(
    model_id="ibm/slate-125m-english-rtrvr",
    url="https://us-south.ml.cloud.ibm.com",
    project_id="<WATSONX PROJECT_ID>",
)
Copypip install -qU langchain-core
Copyfrom langchain_core.embeddings import DeterministicFakeEmbedding

embeddings = DeterministicFakeEmbedding(size=4096)
Copypip install -qU langchain-isaacus
Copyimport getpass
import os

if not os.environ.get("ISAACUS_API_KEY"):
os.environ["ISAACUS_API_KEY"] = getpass.getpass("Enter API key for Isaacus: ")

from langchain_isaacus import IsaacusEmbeddings

embeddings = IsaacusEmbeddings(model="kanon-2-embedder")

Select a vector store:

In-memory Amazon OpenSearch AstraDB Chroma FAISS Milvus MongoDB PGVector PGVectorStore Pinecone QdrantCopypip install -U "langchain-core"
Copyfrom langchain_core.vectorstores import InMemoryVectorStore

vector_store = InMemoryVectorStore(embeddings)
Copypip install -qU  boto3
Copyfrom opensearchpy import RequestsHttpConnection

service = "es"  # must set the service as 'es'
region = "us-east-2"
credentials = boto3.Session(
    aws_access_key_id="xxxxxx", aws_secret_access_key="xxxxx"
).get_credentials()
awsauth = AWS4Auth("xxxxx", "xxxxxx", region, service, session_token=credentials.token)

vector_store = OpenSearchVectorSearch.from_documents(
    docs,
    embeddings,
    opensearch_url="host url",
    http_auth=awsauth,
    timeout=300,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    index_name="test-index",
)
Copypip install -U "langchain-astradb"
Copyfrom langchain_astradb import AstraDBVectorStore

vector_store = AstraDBVectorStore(
    embedding=embeddings,
    api_endpoint=ASTRA_DB_API_ENDPOINT,
    collection_name="astra_vector_langchain",
    token=ASTRA_DB_APPLICATION_TOKEN,
    namespace=ASTRA_DB_NAMESPACE,
)
Copypip install -qU langchain-chroma
Copyfrom langchain_chroma import Chroma

vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
)
Copypip install -qU langchain-community faiss-cpu
Copyimport faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS

embedding_dim = len(embeddings.embed_query("hello world"))
index = faiss.IndexFlatL2(embedding_dim)

vector_store = FAISS(
    embedding_function=embeddings,
    index=index,
    docstore=InMemoryDocstore(),
    index_to_docstore_id={},
)
Copypip install -qU langchain-milvus
Copyfrom langchain_milvus import Milvus

URI = "./milvus_example.db"

vector_store = Milvus(
    embedding_function=embeddings,
    connection_args={"uri": URI},
    index_params={"index_type": "FLAT", "metric_type": "L2"},
)
Copypip install -qU langchain-mongodb
Copyfrom langchain_mongodb import MongoDBAtlasVectorSearch

vector_store = MongoDBAtlasVectorSearch(
    embedding=embeddings,
    collection=MONGODB_COLLECTION,
    index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
    relevance_score_fn="cosine",
)
Copypip install -qU langchain-postgres
Copyfrom langchain_postgres import PGVector

vector_store = PGVector(
    embeddings=embeddings,
    collection_name="my_docs",
    connection="postgresql+psycopg://...",
)
Copypip install -qU langchain-postgres
Copyfrom langchain_postgres import PGEngine, PGVectorStore

pg_engine = PGEngine.from_connection_string(
    url="postgresql+psycopg://..."
)

vector_store = PGVectorStore.create_sync(
    engine=pg_engine,
    table_name='test_table',
    embedding_service=embedding
)
Copypip install -qU langchain-pinecone
Copyfrom langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

pc = Pinecone(api_key=...)
index = pc.Index(index_name)

vector_store = PineconeVectorStore(embedding=embeddings, index=index)
Copypip install -qU langchain-qdrant
Copyfrom qdrant_client.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

client = QdrantClient(":memory:")

vector_size = len(embeddings.embed_query("sample text"))

if not client.collection_exists("test"):
    client.create_collection(
        collection_name="test",
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
    )
vector_store = QdrantVectorStore(
    client=client,
    collection_name="test",
    embedding=embeddings,
)
```

#### ​1. Indexing

This section is an abbreviated version of the content in the semantic search tutorial.If your data is already indexed and available for search (i.e., you have a function to execute a search), or if you’re comfortable with document loaders, embeddings, and vector stores, feel free to skip to the next section on retrieval and generation.

Indexing commonly works as follows:

- Load: First we need to load our data. This is done with Document Loaders.
- Split: Text splitters break large Documents into smaller chunks. This is useful both for indexing data and passing it into a model, as large chunks are harder to search over and won’t fit in a model’s finite context window.
- Store: We need somewhere to store and index our splits, so that they can be searched over later. This is often done using a VectorStore and Embeddings model.

##### ​Loading documents

We need to first load the blog post contents. We can use DocumentLoaders for this, which are objects that load in data from a source and return a list of Document objects.

In this case we’ll use the WebBaseLoader, which uses urllib to load HTML from web URLs and BeautifulSoup to parse it to text. We can customize the HTML -> text parsing by passing in parameters into the BeautifulSoup parser via bs_kwargs (see BeautifulSoup docs). In this case only HTML tags with class “post-content”, “post-title”, or “post-header” are relevant, so we’ll remove all others.

Copyimport bs4
```python
from langchain_community.document_loaders import WebBaseLoader

# Only keep post title, headers, and content from the full HTML.
bs4_strainer = bs4.SoupStrainer(class_=("post-title", "post-header", "post-content"))
loader = WebBaseLoader(
    web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
    bs_kwargs={"parse_only": bs4_strainer},
)
docs = loader.load()

assert len(docs) == 1
print(f"Total characters: {len(docs[0].page_content)}")

CopyTotal characters: 43131

Copyprint(docs[0].page_content[:500])

Copy      LLM Powered Autonomous Agents

Date: June 23, 2023  |  Estimated Reading Time: 31 min  |  Author: Lilian Weng

Building agents with LLM (large language model) as its core controller is a cool concept. Several proof-of-concepts demos, such as AutoGPT, GPT-Engineer and BabyAGI, serve as inspiring examples. The potentiality of LLM extends beyond generating well-written copies, stories, essays and programs; it can be framed as a powerful general problem solver.
Agent System Overview#
In

Go deeper

DocumentLoader: Object that loads data from a source as list of Documents.

- Integrations: 160+ integrations to choose from.
- BaseLoader: API reference for the base interface.
```

##### ​Splitting documents

Our loaded document is over 42k characters which is too long to fit into the context window of many models. Even for those models that could fit the full post in their context window, models can struggle to find information in very long inputs.

To handle this we’ll split the Document into chunks for embedding and vector storage. This should help us retrieve only the most relevant parts of the blog post at run time.

As in the semantic search tutorial, we use a RecursiveCharacterTextSplitter, which will recursively split the document using common separators like new lines until each chunk is the appropriate size. This is the recommended text splitter for generic text use cases.

Copyfrom langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,  # chunk size (characters)
    chunk_overlap=200,  # chunk overlap (characters)
    add_start_index=True,  # track index in original document
)
all_splits = text_splitter.split_documents(docs)

print(f"Split blog post into {len(all_splits)} sub-documents.")

CopySplit blog post into 66 sub-documents.

Go deeper

TextSplitter: Object that splits a list of Document objects into smaller
chunks for storage and retrieval.

- Integrations
- Interface: API reference for the base interface.

##### ​Storing documents

Now we need to index our 66 text chunks so that we can search over them at runtime. Following the semantic search tutorial, our approach is to embed the contents of each document split and insert these embeddings into a vector store. Given an input query, we can then use vector search to retrieve relevant documents.

We can embed and store all of our document splits in a single command using the vector store and embeddings model selected at the start of the tutorial.

Copydocument_ids = vector_store.add_documents(documents=all_splits)

print(document_ids[:3])

Copy['07c18af6-ad58-479a-bfb1-d508033f9c64', '9000bf8e-1993-446f-8d4d-f4e507ba4b8f', 'ba3b5d14-bed9-4f5f-88be-44c88aedc2e6']

Go deeper

Embeddings: Wrapper around a text embedding model, used for converting text to embeddings.

- Integrations: 30+ integrations to choose from.
- Interface: API reference for the base interface.
VectorStore: Wrapper around a vector database, used for storing and querying embeddings.

- Integrations: 40+ integrations to choose from.
- Interface: API reference for the base interface.
This completes the Indexing portion of the pipeline. At this point we have a query-able vector store containing the chunked contents of our blog post. Given a user question, we should ideally be able to return the snippets of the blog post that answer the question.

#### ​2. Retrieval and Generation

RAG applications commonly work as follows:

- Retrieve: Given a user input, relevant splits are retrieved from storage using a Retriever.
- Generate: A model produces an answer using a prompt that includes both the question with the retrieved data
Now let’s write the actual application logic. We want to create a simple application that takes a user question, searches for documents relevant to that question, passes the retrieved documents and initial question to a model, and returns an answer.

We will demonstrate:

- A RAG agent that executes searches with a simple tool. This is a good general-purpose implementation.
- A two-step RAG chain that uses just a single LLM call per query. This is a fast and effective method for simple queries.

##### ​RAG agents

One formulation of a RAG application is as a simple agent with a tool that retrieves information. We can assemble a minimal RAG agent by implementing a tool that wraps our vector store:

Copyfrom langchain.tools import tool

```python
@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve information to help answer a query."""
    retrieved_docs = vector_store.similarity_search(query, k=2)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs

Here we use the tool decorator to configure the tool to attach raw documents as artifacts to each ToolMessage. This will let us access document metadata in our application, separate from the stringified representation that is sent to the model.

Retrieval tools are not limited to a single string query argument, as in the above example. You can
force the LLM to specify additional search parameters by adding arguments— for example, a category:Copyfrom typing import Literal

def retrieve_context(query: str, section: Literal["beginning", "middle", "end"]):

Given our tool, we can construct the agent:

Copyfrom langchain.agents import create_agent

tools = [retrieve_context]
# If desired, specify custom instructions
prompt = (
    "You have access to a tool that retrieves context from a blog post. "
    "Use the tool to help answer user queries."
)
agent = create_agent(model, tools, system_prompt=prompt)

Let’s test this out. We construct a question that would typically require an iterative sequence of retrieval steps to answer:

Copyquery = (
    "What is the standard method for Task Decomposition?\n\n"
    "Once you get the answer, look up common extensions of that method."
)

for event in agent.stream(
    {"messages": [{"role": "user", "content": query}]},
    stream_mode="values",
):
    event["messages"][-1].pretty_print()

Copy================================ Human Message =================================

What is the standard method for Task Decomposition?

Once you get the answer, look up common extensions of that method.
================================== Ai Message ==================================
Tool Calls:
  retrieve_context (call_d6AVxICMPQYwAKj9lgH4E337)
 Call ID: call_d6AVxICMPQYwAKj9lgH4E337
  Args:
    query: standard method for Task Decomposition
================================= Tool Message =================================
Name: retrieve_context

Source: {'source': 'https://lilianweng.github.io/posts/2023-06-23-agent/'}
Content: Task decomposition can be done...

Source: {'source': 'https://lilianweng.github.io/posts/2023-06-23-agent/'}
Content: Component One: Planning...
================================== Ai Message ==================================
Tool Calls:
  retrieve_context (call_0dbMOw7266jvETbXWn4JqWpR)
 Call ID: call_0dbMOw7266jvETbXWn4JqWpR
  Args:
    query: common extensions of the standard method for Task Decomposition
================================= Tool Message =================================
Name: retrieve_context

Source: {'source': 'https://lilianweng.github.io/posts/2023-06-23-agent/'}
Content: Task decomposition can be done...

Source: {'source': 'https://lilianweng.github.io/posts/2023-06-23-agent/'}
Content: Component One: Planning...
================================== Ai Message ==================================

The standard method for Task Decomposition often used is the Chain of Thought (CoT)...

Note that the agent:

- Generates a query to search for a standard method for task decomposition;
- Receiving the answer, generates a second query to search for common extensions of it;
- Having received all necessary context, answers the question.
We can see the full sequence of steps, along with latency and other metadata, in the LangSmith trace.

You can add a deeper level of control and customization using the LangGraph framework directly— for example, you can add steps to grade document relevance and rewrite search queries. Check out LangGraph’s Agentic RAG tutorial for more advanced formulations.
```

##### ​RAG chains

In the above agentic RAG formulation we allow the LLM to use its discretion in generating a tool call to help answer user queries. This is a good general-purpose solution, but comes with some trade-offs:

Benefits⚠️ DrawbacksSearch only when needed – The LLM can handle greetings, follow-ups, and simple queries without triggering unnecessary searches.Two inference calls – When a search is performed, it requires one call to generate the query and another to produce the final response.Contextual search queries – By treating search as a tool with a query input, the LLM crafts its own queries that incorporate conversational context.Reduced control – The LLM may skip searches when they are actually needed, or issue extra searches when unnecessary.Multiple searches allowed – The LLM can execute several searches in support of a single user query.

Another common approach is a two-step chain, in which we always run a search (potentially using the raw user query) and incorporate the result as context for a single LLM query. This results in a single inference call per query, buying reduced latency at the expense of flexibility.

In this approach we no longer call the model in a loop, but instead make a single pass.

We can implement this chain by removing tools from the agent and instead incorporating the retrieval step into a custom prompt:

Copyfrom langchain.agents.middleware import dynamic_prompt, ModelRequest

```python
@dynamic_prompt
def prompt_with_context(request: ModelRequest) -> str:
    """Inject context into state messages."""
    last_query = request.state["messages"][-1].text
    retrieved_docs = vector_store.similarity_search(last_query)

    docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)

    system_message = (
        "You are a helpful assistant. Use the following context in your response:"
        f"\n\n{docs_content}"
    )

    return system_message

agent = create_agent(model, tools=[], middleware=[prompt_with_context])

Let’s try this out:

Copyquery = "What is task decomposition?"
for step in agent.stream(
    {"messages": [{"role": "user", "content": query}]},
    stream_mode="values",
):
    step["messages"][-1].pretty_print()

Copy================================ Human Message =================================

What is task decomposition?
================================== Ai Message ==================================

Task decomposition is...

In the LangSmith trace we can see the retrieved context incorporated into the model prompt.

This is a fast and effective method for simple queries in constrained settings, when we typically do want to run user queries through semantic search to pull additional context.

Returning source documentsThe above RAG chain incorporates retrieved context into a single system message for that run.As in the agentic RAG formulation, we sometimes want to include raw source documents in the application state to have access to document metadata. We can do this for the two-step chain case by:
Adding a key to the state to store the retrieved documents
Adding a new node via a pre-model hook to populate that key (as well as inject the context).
Copyfrom typing import Any
from langchain_core.documents import Document
from langchain.agents.middleware import AgentMiddleware, AgentState

class State(AgentState):
    context: list[Document]

class RetrieveDocumentsMiddleware(AgentMiddleware[State]):
    state_schema = State

    def before_model(self, state: AgentState) -> dict[str, Any] | None:
        last_message = state["messages"][-1]
        retrieved_docs = vector_store.similarity_search(last_message.text)

        docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)

        augmented_message_content = (
            f"{last_message.text}\n\n"
            "Use the following context to answer the query:\n"
            f"{docs_content}"
        )
        return {
            "messages": [last_message.model_copy(update={"content": augmented_message_content})],
            "context": retrieved_docs,
        }

agent = create_agent(
    model,
    tools=[],
    middleware=[RetrieveDocumentsMiddleware()],
)
```

#### ​Next steps

Now that we’ve implemented a simple RAG application via create_agent, we can easily incorporate new features and go deeper:

- Stream tokens and other information for responsive user experiences
- Add conversational memory to support multi-turn interactions
- Add long-term memory to support memory across conversational threads
- Add structured responses
- Deploy your application with LangSmith Deployment
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Overview - Docs by LangChain {#doc-19}

**Source:** [https://docs.langchain.com/oss/python/langchain/middleware/overview#dynamic-model](https://docs.langchain.com/oss/python/langchain/middleware/overview#dynamic-model)

### Overview

Copy page

#### ​The agent loop

The core agent loop involves calling a model, letting it choose tools to execute, and then finishing when it calls no more tools:

Middleware exposes hooks before and after each of those steps:

#### ​Additional resources

Built-in middlewareExplore built-in middleware for common use cases.Custom middlewareBuild your own middleware with hooks and decorators.Middleware API referenceComplete API reference for middleware.Testing agentsTest your agents with LangSmith.

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.

#### Built-in middleware

Explore built-in middleware for common use cases.

#### Custom middleware

Build your own middleware with hooks and decorators.

#### Middleware API reference

Complete API reference for middleware.

#### Testing agents

Test your agents with LangSmith.


---

## Changelog - Docs by LangChain {#doc-20}

**Source:** [https://docs.langchain.com/oss/python/releases/changelog](https://docs.langchain.com/oss/python/releases/changelog)

### Changelog

Copy page

#### ​langchain v1.2.0

- create_agent: Simplified support for provider-specific tool parameters and definitions via a new extras attribute on tools. Examples:

Provider-specific configuration such as Anthropic’s programmatic tool calling and tool search.
Built-in tools that are executed client-side, as supported by Anthropic, OpenAI, and other providers.
- Provider-specific configuration such as Anthropic’s programmatic tool calling and tool search.
- Built-in tools that are executed client-side, as supported by Anthropic, OpenAI, and other providers.
- Support for strict schema-adherence in agent response_format (see ProviderStrategy docs).

#### ​langchain-google-genai v4.0.0

We’ve re-written the Google GenAI integration to use Google’s consolidated Generative AI SDK, which provides access to the Gemini API and Vertex AI Platform under the same interface. This includes minimal breaking changes as well as deprecated packages in langchain-google-vertexai.

See the full release notes and migration guide for details.

#### ​langchain v1.1.0

- Model profiles: Chat models now expose supported features and capabilities through a .profile attribute. These data are derived from models.dev, an open source project providing model capability data.
- Summarization middleware: Updated to support flexible trigger points using model profiles for context-aware summarization.
- Structured output: ProviderStrategy support (native structured output) can now be inferred from model profiles.
- SystemMessage for create_agent: Support for passing SystemMessage instances directly to create_agent’s system_prompt parameter, enabling advanced features like cache control and structured content blocks.
- Model retry middleware: New middleware for automatically retrying failed model calls with configurable exponential backoff.
- Content moderation middleware: OpenAI content moderation middleware for detecting and handling unsafe content in agent interactions. Supports checking user input, model output, and tool results.

#### ​v1.0.0

##### ​langchain

- Release notes
- Migration guide

##### ​langgraph

- Release notes
- Migration guide
If you encounter any issues or have feedback, please open an issue so we can improve. To view v0.x documentation, go to the archived content and API reference.


---

## LangSmith Observability - Docs by LangChain {#doc-21}

**Source:** [https://docs.langchain.com/oss/python/langchain/observability](https://docs.langchain.com/oss/python/langchain/observability)

### LangSmith Observability

Copy page

#### ​Prerequisites

Before you begin, ensure you have the following:

- A LangSmith account: Sign up (for free) or log in at smith.langchain.com.
- A LangSmith API key: Follow the Create an API key guide.

#### ​Enable tracing

All LangChain agents automatically support LangSmith tracing. To enable it, set the following environment variables:

Copyexport LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=<your-api-key>

#### ​Quickstart

No extra code is needed to log a trace to LangSmith. Just run your agent code as you normally would:

Copyfrom langchain.agents import create_agent

```python
def send_email(to: str, subject: str, body: str):
    """Send an email to a recipient."""
    # ... email sending logic
    return f"Email sent to {to}"

def search_web(query: str):
    """Search the web for information."""
    # ... web search logic
    return f"Search results for: {query}"

agent = create_agent(
    model="gpt-4o",
    tools=[send_email, search_web],
    system_prompt="You are a helpful assistant that can send emails and search the web."
)

# Run the agent - all steps will be traced automatically
response = agent.invoke({
    "messages": [{"role": "user", "content": "Search for the latest AI news and email a summary to john@example.com"}]
})

By default, the trace will be logged to the project with the name default. To configure a custom project name, see Log to a project.
```

#### ​Trace selectively

You may opt to trace specific invocations or parts of your application using LangSmith’s tracing_context context manager:

Copyimport langsmith as ls

# This WILL be traced
with ls.tracing_context(enabled=True):
    agent.invoke({"messages": [{"role": "user", "content": "Send a test email to alice@example.com"}]})

# This will NOT be traced (if LANGSMITH_TRACING is not set)
agent.invoke({"messages": [{"role": "user", "content": "Send another email"}]})

#### ​Log to a project

StaticallyYou can set a custom project name for your entire application by setting the LANGSMITH_PROJECT environment variable:Copyexport LANGSMITH_PROJECT=my-agent-project

DynamicallyYou can set the project name programmatically for specific operations:Copyimport langsmith as ls

with ls.tracing_context(project_name="email-agent-test", enabled=True):
```
    response = agent.invoke({
        "messages": [{"role": "user", "content": "Send a welcome email"}]
    })
```

#### ​Add metadata to traces

You can annotate your traces with custom metadata and tags:

Copyresponse = agent.invoke(
    {"messages": [{"role": "user", "content": "Send a welcome email"}]},
```
    config={
        "tags": ["production", "email-assistant", "v1.0"],
        "metadata": {
            "user_id": "user_123",
            "session_id": "session_456",
            "environment": "production"
        }
    }
)

tracing_context also accepts tags and metadata for fine-grained control:

Copywith ls.tracing_context(
    project_name="email-agent-test",
    enabled=True,
    tags=["production", "email-assistant", "v1.0"],
    metadata={"user_id": "user_123", "session_id": "session_456", "environment": "production"}):
    response = agent.invoke(
        {"messages": [{"role": "user", "content": "Send a welcome email"}]}
    )

This custom metadata and tags will be attached to the trace in LangSmith.

To learn more about how to use traces to debug, evaluate, and monitor your agents, see the LangSmith documentation.

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```


---

## LangSmith Deployment - Docs by LangChain {#doc-22}

**Source:** [https://docs.langchain.com/oss/python/langchain/deploy](https://docs.langchain.com/oss/python/langchain/deploy)

### LangSmith Deployment

Copy page

#### ​Prerequisites

Before you begin, ensure you have the following:

- A GitHub account
- A LangSmith account (free to sign up)

#### ​Deploy your agent

##### ​1. Create a repository on GitHub

Your application’s code must reside in a GitHub repository to be deployed on LangSmith. Both public and private repositories are supported. For this quickstart, first make sure your app is LangGraph-compatible by following the local server setup guide. Then, push your code to the repository.

##### ​2. Deploy to LangSmith

1Navigate to LangSmith DeploymentLog in to LangSmith. In the left sidebar, select Deployments.2Create new deploymentClick the + New Deployment button. A pane will open where you can fill in the required fields.3Link repositoryIf you are a first time user or adding a private repository that has not been previously connected, click the Add new account button and follow the instructions to connect your GitHub account.4Deploy repositorySelect your application’s repository. Click Submit to deploy. This may take about 15 minutes to complete. You can check the status in the Deployment details view.

##### ​3. Test your application in Studio

Once your application is deployed:

- Select the deployment you just created to view more details.
- Click the Studio button in the top right corner. Studio will open to display your graph.

##### ​4. Get the API URL for your deployment

- In the Deployment details view in LangGraph, click the API URL to copy it to your clipboard.
- Click the URL to copy it to the clipboard.

##### ​5. Test the API

You can now test the API:

Python Rest API
Install LangGraph Python:
Copypip install langgraph-sdk

Send a message to the agent:
Copyfrom langgraph_sdk import get_sync_client # or get_client for async

client = get_sync_client(url="your-deployment-url", api_key="your-langsmith-api-key")

for chunk in client.runs.stream(
    None,    # Threadless run
    "agent", # Name of agent. Defined in langgraph.json.
```
    input={
        "messages": [{
            "role": "human",
            "content": "What is LangGraph?",
        }],
    },
    stream_mode="updates",
):
    print(f"Receiving new event of type: {chunk.event}...")
    print(chunk.data)
    print("\n\n")
Copycurl -s --request POST \
    --url <DEPLOYMENT_URL>/runs/stream \
    --header 'Content-Type: application/json' \
    --header "X-Api-Key: <LANGSMITH API KEY> \
    --data "{
        \"assistant_id\": \"agent\", `# Name of agent. Defined in langgraph.json.`
        \"input\": {
            \"messages\": [
                {
                    \"role\": \"human\",
                    \"content\": \"What is LangGraph?\"
                }
            ]
        },
        \"stream_mode\": \"updates\"
    }"

LangSmith offers additional hosting options, including self-hosted and hybrid. For more information, please see the Platform setup overview.

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```


---

## Agent Chat UI - Docs by LangChain {#doc-23}

**Source:** [https://docs.langchain.com/oss/python/langchain/ui](https://docs.langchain.com/oss/python/langchain/ui)

### Agent Chat UI

Copy page

##### ​Quick start

The fastest way to get started is using the hosted version:

- Visit Agent Chat UI
- Connect your agent by entering your deployment URL or local server address
- Start chatting - the UI will automatically detect and render tool calls and interrupts

##### ​Local development

For customization or local development, you can run Agent Chat UI locally:

Use npxClone repositoryCopy# Create a new Agent Chat UI project
npx create-agent-chat-app --project-name my-chat-ui
cd my-chat-ui

# Install dependencies and start
pnpm install
pnpm dev

##### ​Connect to your agent

Agent Chat UI can connect to both local and deployed agents.

After starting Agent Chat UI, you’ll need to configure it to connect to your agent:

- Graph ID: Enter your graph name (find this under graphs in your langgraph.json file)
- Deployment URL: Your Agent server’s endpoint (e.g., http://localhost:2024 for local development, or your deployed agent’s URL)
- LangSmith API key (optional): Add your LangSmith API key (not required if you’re using a local Agent server)
Once configured, Agent Chat UI will automatically fetch and display any interrupted threads from your agent.

Agent Chat UI has out-of-the-box support for rendering tool calls and tool result messages. To customize what messages are shown, see Hiding Messages in the Chat.

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Test - Docs by LangChain {#doc-24}

**Source:** [https://docs.langchain.com/oss/python/langchain/test](https://docs.langchain.com/oss/python/langchain/test)

### Test

Copy page

#### ​Unit Testing

##### ​Mocking Chat Model

For logic not requiring API calls, you can use an in-memory stub for mocking responses.

LangChain provides GenericFakeChatModel for mocking text responses. It accepts an iterator of responses (AIMessages or strings) and returns one per invocation. It supports both regular and streaming usage.

Copyfrom langchain_core.language_models.fake_chat_models import GenericFakeChatModel

model = GenericFakeChatModel(messages=iter([
    AIMessage(content="", tool_calls=[ToolCall(name="foo", args={"bar": "baz"}, id="call_1")]),
    "bar"
]))

model.invoke("hello")
# AIMessage(content='', ..., tool_calls=[{'name': 'foo', 'args': {'bar': 'baz'}, 'id': 'call_1', 'type': 'tool_call'}])

If we invoke the model again, it will return the next item in the iterator:

Copymodel.invoke("hello, again!")
# AIMessage(content='bar', ...)

##### ​InMemorySaver Checkpointer

To enable persistence during testing, you can use the InMemorySaver checkpointer. This allows you to simulate multiple turns to test state-dependent behavior:

Copyfrom langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model,
    tools=[],
    checkpointer=InMemorySaver()
)

# First invocation
agent.invoke(HumanMessage(content="I live in Sydney, Australia."))

# Second invocation: the first message is persisted (Sydney location), so the model returns GMT+10 time
agent.invoke(HumanMessage(content="What's my local time?"))

#### ​Integration Testing

Many agent behaviors only emerge when using a real LLM, such as which tool the agent decides to call, how it formats responses, or whether a prompt modification affects the entire execution trajectory. LangChain’s agentevals package provides evaluators specifically designed for testing agent trajectories with live models.

AgentEvals lets you easily evaluate the trajectory of your agent (the exact sequence of messages, including tool calls) by performing a trajectory match or by using an LLM judge:

Trajectory matchHard-code a reference trajectory for a given input and validate the run via a step-by-step comparison.Ideal for testing well-defined workflows where you know the expected behavior. Use when you have specific expectations about which tools should be called and in what order. This approach is deterministic, fast, and cost-effective since it doesn’t require additional LLM calls.

LLM-as-judgeUse a LLM to qualitatively validate your agent’s execution trajectory. The “judge” LLM reviews the agent’s decisions against a prompt rubric (which can include a reference trajectory).More flexible and can assess nuanced aspects like efficiency and appropriateness, but requires an LLM call and is less deterministic. Use when you want to evaluate the overall quality and reasonableness of the agent’s trajectory without strict tool call or ordering requirements.

​Installing AgentEvals

Copypip install agentevals

Or, clone the AgentEvals repository directly.

​Trajectory Match Evaluator

AgentEvals offers the create_trajectory_match_evaluator function to match your agent’s trajectory against a reference trajectory. There are four modes to choose from:

ModeDescriptionUse CasestrictExact match of messages and tool calls in the same orderTesting specific sequences (e.g., policy lookup before authorization)unorderedSame tool calls allowed in any orderVerifying information retrieval when order doesn’t mattersubsetAgent calls only tools from reference (no extras)Ensuring agent doesn’t exceed expected scopesupersetAgent calls at least the reference tools (extras allowed)Verifying minimum required actions are taken

Strict matchThe strict mode ensures trajectories contain identical messages in the same order with the same tool calls, though it allows for differences in message content. This is useful when you need to enforce a specific sequence of operations, such as requiring a policy lookup before authorizing an action.Copyfrom langchain.agents import create_agent
```python
from langchain.tools import tool
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from agentevals.trajectory.match import create_trajectory_match_evaluator

@tool
def get_weather(city: str):
    """Get weather information for a city."""
    return f"It's 75 degrees and sunny in {city}."

agent = create_agent("gpt-4o", tools=[get_weather])

evaluator = create_trajectory_match_evaluator(
    trajectory_match_mode="strict",
)

def test_weather_tool_called_strict():
    result = agent.invoke({
        "messages": [HumanMessage(content="What's the weather in San Francisco?")]
    })

    reference_trajectory = [
        HumanMessage(content="What's the weather in San Francisco?"),
        AIMessage(content="", tool_calls=[
            {"id": "call_1", "name": "get_weather", "args": {"city": "San Francisco"}}
        ]),
        ToolMessage(content="It's 75 degrees and sunny in San Francisco.", tool_call_id="call_1"),
        AIMessage(content="The weather in San Francisco is 75 degrees and sunny."),
    ]

    evaluation = evaluator(
        outputs=result["messages"],
        reference_outputs=reference_trajectory
    )
    # {
    #     'key': 'trajectory_strict_match',
    #     'score': True,
    #     'comment': None,
    # }
    assert evaluation["score"] is True

Unordered matchThe unordered mode allows the same tool calls in any order, which is helpful when you want to verify that specific information was retrieved but don’t care about the sequence. For example, an agent might need to check both weather and events for a city, but the order doesn’t matter.Copyfrom langchain.agents import create_agent
from langchain.tools import tool
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from agentevals.trajectory.match import create_trajectory_match_evaluator

@tool
def get_weather(city: str):
    """Get weather information for a city."""
    return f"It's 75 degrees and sunny in {city}."

@tool
def get_events(city: str):
    """Get events happening in a city."""
    return f"Concert at the park in {city} tonight."

agent = create_agent("gpt-4o", tools=[get_weather, get_events])

evaluator = create_trajectory_match_evaluator(
    trajectory_match_mode="unordered",
)

def test_multiple_tools_any_order():
    result = agent.invoke({
        "messages": [HumanMessage(content="What's happening in SF today?")]
    })

    # Reference shows tools called in different order than actual execution
    reference_trajectory = [
        HumanMessage(content="What's happening in SF today?"),
        AIMessage(content="", tool_calls=[
            {"id": "call_1", "name": "get_events", "args": {"city": "SF"}},
            {"id": "call_2", "name": "get_weather", "args": {"city": "SF"}},
        ]),
        ToolMessage(content="Concert at the park in SF tonight.", tool_call_id="call_1"),
        ToolMessage(content="It's 75 degrees and sunny in SF.", tool_call_id="call_2"),
        AIMessage(content="Today in SF: 75 degrees and sunny with a concert at the park tonight."),
    ]

    evaluation = evaluator(
        outputs=result["messages"],
        reference_outputs=reference_trajectory,
    )
    # {
    #     'key': 'trajectory_unordered_match',
    #     'score': True,
    # }
    assert evaluation["score"] is True

Subset and superset matchThe superset and subset modes match partial trajectories. The superset mode verifies that the agent called at least the tools in the reference trajectory, allowing additional tool calls. The subset mode ensures the agent did not call any tools beyond those in the reference.Copyfrom langchain.agents import create_agent
from langchain.tools import tool
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from agentevals.trajectory.match import create_trajectory_match_evaluator

@tool
def get_weather(city: str):
    """Get weather information for a city."""
    return f"It's 75 degrees and sunny in {city}."

@tool
def get_detailed_forecast(city: str):
    """Get detailed weather forecast for a city."""
    return f"Detailed forecast for {city}: sunny all week."

agent = create_agent("gpt-4o", tools=[get_weather, get_detailed_forecast])

evaluator = create_trajectory_match_evaluator(
    trajectory_match_mode="superset",
)

def test_agent_calls_required_tools_plus_extra():
    result = agent.invoke({
        "messages": [HumanMessage(content="What's the weather in Boston?")]
    })

    # Reference only requires get_weather, but agent may call additional tools
    reference_trajectory = [
        HumanMessage(content="What's the weather in Boston?"),
        AIMessage(content="", tool_calls=[
            {"id": "call_1", "name": "get_weather", "args": {"city": "Boston"}},
        ]),
        ToolMessage(content="It's 75 degrees and sunny in Boston.", tool_call_id="call_1"),
        AIMessage(content="The weather in Boston is 75 degrees and sunny."),
    ]

    evaluation = evaluator(
        outputs=result["messages"],
        reference_outputs=reference_trajectory,
    )
    # {
    #     'key': 'trajectory_superset_match',
    #     'score': True,
    #     'comment': None,
    # }
    assert evaluation["score"] is True

You can also set the tool_args_match_mode property and/or tool_args_match_overrides to customize how the evaluator considers equality between tool calls in the actual trajectory vs. the reference. By default, only tool calls with the same arguments to the same tool are considered equal. Visit the repository for more details.

​LLM-as-Judge Evaluator

You can also use an LLM to evaluate the agent’s execution path with the create_trajectory_llm_as_judge function. Unlike the trajectory match evaluators, it doesn’t require a reference trajectory, but one can be provided if available.

Without reference trajectoryCopyfrom langchain.agents import create_agent
from langchain.tools import tool
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from agentevals.trajectory.llm import create_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT

@tool
def get_weather(city: str):
    """Get weather information for a city."""
    return f"It's 75 degrees and sunny in {city}."

agent = create_agent("gpt-4o", tools=[get_weather])

evaluator = create_trajectory_llm_as_judge(
    model="openai:o3-mini",
    prompt=TRAJECTORY_ACCURACY_PROMPT,
)

def test_trajectory_quality():
    result = agent.invoke({
        "messages": [HumanMessage(content="What's the weather in Seattle?")]
    })

    evaluation = evaluator(
        outputs=result["messages"],
    )
    # {
    #     'key': 'trajectory_accuracy',
    #     'score': True,
    #     'comment': 'The provided agent trajectory is reasonable...'
    # }
    assert evaluation["score"] is True

With reference trajectoryIf you have a reference trajectory, you can add an extra variable to your prompt and pass in the reference trajectory. Below, we use the prebuilt TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE prompt and configure the reference_outputs variable:Copyevaluator = create_trajectory_llm_as_judge(
    model="openai:o3-mini",
    prompt=TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE,
)
evaluation = judge_with_reference(
    outputs=result["messages"],
    reference_outputs=reference_trajectory,
)

For more configurability over how the LLM evaluates the trajectory, visit the repository.

​Async Support

All agentevals evaluators support Python asyncio. For evaluators that use factory functions, async versions are available by adding async after create_ in the function name.

Async judge and evaluator exampleCopyfrom agentevals.trajectory.llm import create_async_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT
from agentevals.trajectory.match import create_async_trajectory_match_evaluator

async_judge = create_async_trajectory_llm_as_judge(
    model="openai:o3-mini",
    prompt=TRAJECTORY_ACCURACY_PROMPT,
)

async_evaluator = create_async_trajectory_match_evaluator(
    trajectory_match_mode="strict",
)

async def test_async_evaluation():
    result = await agent.ainvoke({
        "messages": [HumanMessage(content="What's the weather?")]
    })

    evaluation = await async_judge(outputs=result["messages"])
    assert evaluation["score"] is True

​LangSmith Integration

For tracking experiments over time, you can log evaluator results to LangSmith, a platform for building production-grade LLM applications that includes tracing, evaluation, and experimentation tools.

First, set up LangSmith by setting the required environment variables:

Copyexport LANGSMITH_API_KEY="your_langsmith_api_key"
export LANGSMITH_TRACING="true"

LangSmith offers two main approaches for running evaluations: pytest integration and the evaluate function.

Using pytest integrationCopyimport pytest
from langsmith import testing as t
from agentevals.trajectory.llm import create_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT

trajectory_evaluator = create_trajectory_llm_as_judge(
    model="openai:o3-mini",
    prompt=TRAJECTORY_ACCURACY_PROMPT,
)

@pytest.mark.langsmith
def test_trajectory_accuracy():
    result = agent.invoke({
        "messages": [HumanMessage(content="What's the weather in SF?")]
    })

    reference_trajectory = [
        HumanMessage(content="What's the weather in SF?"),
        AIMessage(content="", tool_calls=[
            {"id": "call_1", "name": "get_weather", "args": {"city": "SF"}},
        ]),
        ToolMessage(content="It's 75 degrees and sunny in SF.", tool_call_id="call_1"),
        AIMessage(content="The weather in SF is 75 degrees and sunny."),
    ]

    # Log inputs, outputs, and reference outputs to LangSmith
    t.log_inputs({})
    t.log_outputs({"messages": result["messages"]})
    t.log_reference_outputs({"messages": reference_trajectory})

    trajectory_evaluator(
        outputs=result["messages"],
        reference_outputs=reference_trajectory
    )
Run the evaluation with pytest:Copypytest test_trajectory.py --langsmith-output
Results will be automatically logged to LangSmith.

Using the evaluate functionAlternatively, you can create a dataset in LangSmith and use the evaluate function:Copyfrom langsmith import Client
from agentevals.trajectory.llm import create_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT

client = Client()

trajectory_evaluator = create_trajectory_llm_as_judge(
    model="openai:o3-mini",
    prompt=TRAJECTORY_ACCURACY_PROMPT,
)

def run_agent(inputs):
    """Your agent function that returns trajectory messages."""
    return agent.invoke(inputs)["messages"]

experiment_results = client.evaluate(
    run_agent,
    data="your_dataset_name",
    evaluators=[trajectory_evaluator]
)
Results will be automatically logged to LangSmith.

To learn more about evaluating your agent, see the LangSmith docs.

​Recording & Replaying HTTP Calls

Integration tests that call real LLM APIs can be slow and expensive, especially when run frequently in CI/CD pipelines. We recommend using a library for recording HTTP requests and responses, then replaying them in subsequent runs without making actual network calls.

You can use vcrpy to achieve this. If you’re using pytest, the pytest-recording plugin provides a simple way to enable this with minimal configuration. Request/responses are recorded in cassettes, which are then used to mock the real network calls in subsequent runs.

Set up your conftest.py file to filter out sensitive information from the cassettes:

conftest.pyCopyimport pytest

@pytest.fixture(scope="session")
def vcr_config():
    return {
        "filter_headers": [
            ("authorization", "XXXX"),
            ("x-api-key", "XXXX"),
            # ... other headers you want to mask
        ],
        "filter_query_parameters": [
            ("api_key", "XXXX"),
            ("key", "XXXX"),
        ],
    }

Then configure your project to recognise the vcr marker:

pytest.inipyproject.tomlCopy[pytest]
markers =
    vcr: record/replay HTTP via VCR
addopts = --record-mode=once

The --record-mode=once option records HTTP interactions on the first run and replays them on subsequent runs.

Now, simply decorate your tests with the vcr marker:

Copy@pytest.mark.vcr()
def test_agent_trajectory():
    # ...

The first time you run this test, your agent will make real network calls and pytest will generate a cassette file test_agent_trajectory.yaml in the tests/cassettes directory. Subsequent runs will use that cassette to mock the real network calls, granted the agent’s requests don’t change from the previous run. If they do, the test will fail and you’ll need to delete the cassette and rerun the test to record fresh interactions.

When you modify prompts, add new tools, or change expected trajectories, your saved cassettes will become outdated and your existing tests will fail. You should delete the corresponding cassette files and rerun the tests to record fresh interactions.

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```

#### Trajectory match

Hard-code a reference trajectory for a given input and validate the run via a step-by-step comparison.Ideal for testing well-defined workflows where you know the expected behavior. Use when you have specific expectations about which tools should be called and in what order. This approach is deterministic, fast, and cost-effective since it doesn’t require additional LLM calls.

#### LLM-as-judge

Use a LLM to qualitatively validate your agent’s execution trajectory. The “judge” LLM reviews the agent’s decisions against a prompt rubric (which can include a reference trajectory).More flexible and can assess nuanced aspects like efficiency and appropriateness, but requires an LLM call and is less deterministic. Use when you want to evaluate the overall quality and reasonableness of the agent’s trajectory without strict tool call or ordering requirements.

##### ​Installing AgentEvals

Copypip install agentevals

Or, clone the AgentEvals repository directly.

##### ​Trajectory Match Evaluator

AgentEvals offers the create_trajectory_match_evaluator function to match your agent’s trajectory against a reference trajectory. There are four modes to choose from:

ModeDescriptionUse CasestrictExact match of messages and tool calls in the same orderTesting specific sequences (e.g., policy lookup before authorization)unorderedSame tool calls allowed in any orderVerifying information retrieval when order doesn’t mattersubsetAgent calls only tools from reference (no extras)Ensuring agent doesn’t exceed expected scopesupersetAgent calls at least the reference tools (extras allowed)Verifying minimum required actions are taken

Strict matchThe strict mode ensures trajectories contain identical messages in the same order with the same tool calls, though it allows for differences in message content. This is useful when you need to enforce a specific sequence of operations, such as requiring a policy lookup before authorizing an action.Copyfrom langchain.agents import create_agent
```python
from langchain.tools import tool
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from agentevals.trajectory.match import create_trajectory_match_evaluator

@tool
def get_weather(city: str):
    """Get weather information for a city."""
    return f"It's 75 degrees and sunny in {city}."

agent = create_agent("gpt-4o", tools=[get_weather])

evaluator = create_trajectory_match_evaluator(
    trajectory_match_mode="strict",
)

def test_weather_tool_called_strict():
    result = agent.invoke({
        "messages": [HumanMessage(content="What's the weather in San Francisco?")]
    })

    reference_trajectory = [
        HumanMessage(content="What's the weather in San Francisco?"),
        AIMessage(content="", tool_calls=[
            {"id": "call_1", "name": "get_weather", "args": {"city": "San Francisco"}}
        ]),
        ToolMessage(content="It's 75 degrees and sunny in San Francisco.", tool_call_id="call_1"),
        AIMessage(content="The weather in San Francisco is 75 degrees and sunny."),
    ]

    evaluation = evaluator(
        outputs=result["messages"],
        reference_outputs=reference_trajectory
    )
    # {
    #     'key': 'trajectory_strict_match',
    #     'score': True,
    #     'comment': None,
    # }
    assert evaluation["score"] is True

Unordered matchThe unordered mode allows the same tool calls in any order, which is helpful when you want to verify that specific information was retrieved but don’t care about the sequence. For example, an agent might need to check both weather and events for a city, but the order doesn’t matter.Copyfrom langchain.agents import create_agent
from langchain.tools import tool
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from agentevals.trajectory.match import create_trajectory_match_evaluator

@tool
def get_weather(city: str):
    """Get weather information for a city."""
    return f"It's 75 degrees and sunny in {city}."

@tool
def get_events(city: str):
    """Get events happening in a city."""
    return f"Concert at the park in {city} tonight."

agent = create_agent("gpt-4o", tools=[get_weather, get_events])

evaluator = create_trajectory_match_evaluator(
    trajectory_match_mode="unordered",
)

def test_multiple_tools_any_order():
    result = agent.invoke({
        "messages": [HumanMessage(content="What's happening in SF today?")]
    })

    # Reference shows tools called in different order than actual execution
    reference_trajectory = [
        HumanMessage(content="What's happening in SF today?"),
        AIMessage(content="", tool_calls=[
            {"id": "call_1", "name": "get_events", "args": {"city": "SF"}},
            {"id": "call_2", "name": "get_weather", "args": {"city": "SF"}},
        ]),
        ToolMessage(content="Concert at the park in SF tonight.", tool_call_id="call_1"),
        ToolMessage(content="It's 75 degrees and sunny in SF.", tool_call_id="call_2"),
        AIMessage(content="Today in SF: 75 degrees and sunny with a concert at the park tonight."),
    ]

    evaluation = evaluator(
        outputs=result["messages"],
        reference_outputs=reference_trajectory,
    )
    # {
    #     'key': 'trajectory_unordered_match',
    #     'score': True,
    # }
    assert evaluation["score"] is True

Subset and superset matchThe superset and subset modes match partial trajectories. The superset mode verifies that the agent called at least the tools in the reference trajectory, allowing additional tool calls. The subset mode ensures the agent did not call any tools beyond those in the reference.Copyfrom langchain.agents import create_agent
from langchain.tools import tool
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from agentevals.trajectory.match import create_trajectory_match_evaluator

@tool
def get_weather(city: str):
    """Get weather information for a city."""
    return f"It's 75 degrees and sunny in {city}."

@tool
def get_detailed_forecast(city: str):
    """Get detailed weather forecast for a city."""
    return f"Detailed forecast for {city}: sunny all week."

agent = create_agent("gpt-4o", tools=[get_weather, get_detailed_forecast])

evaluator = create_trajectory_match_evaluator(
    trajectory_match_mode="superset",
)

def test_agent_calls_required_tools_plus_extra():
    result = agent.invoke({
        "messages": [HumanMessage(content="What's the weather in Boston?")]
    })

    # Reference only requires get_weather, but agent may call additional tools
    reference_trajectory = [
        HumanMessage(content="What's the weather in Boston?"),
        AIMessage(content="", tool_calls=[
            {"id": "call_1", "name": "get_weather", "args": {"city": "Boston"}},
        ]),
        ToolMessage(content="It's 75 degrees and sunny in Boston.", tool_call_id="call_1"),
        AIMessage(content="The weather in Boston is 75 degrees and sunny."),
    ]

    evaluation = evaluator(
        outputs=result["messages"],
        reference_outputs=reference_trajectory,
    )
    # {
    #     'key': 'trajectory_superset_match',
    #     'score': True,
    #     'comment': None,
    # }
    assert evaluation["score"] is True

You can also set the tool_args_match_mode property and/or tool_args_match_overrides to customize how the evaluator considers equality between tool calls in the actual trajectory vs. the reference. By default, only tool calls with the same arguments to the same tool are considered equal. Visit the repository for more details.
```

##### ​LLM-as-Judge Evaluator

You can also use an LLM to evaluate the agent’s execution path with the create_trajectory_llm_as_judge function. Unlike the trajectory match evaluators, it doesn’t require a reference trajectory, but one can be provided if available.

Without reference trajectoryCopyfrom langchain.agents import create_agent
```python
from langchain.tools import tool
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from agentevals.trajectory.llm import create_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT

@tool
def get_weather(city: str):
    """Get weather information for a city."""
    return f"It's 75 degrees and sunny in {city}."

agent = create_agent("gpt-4o", tools=[get_weather])

evaluator = create_trajectory_llm_as_judge(
    model="openai:o3-mini",
    prompt=TRAJECTORY_ACCURACY_PROMPT,
)

def test_trajectory_quality():
    result = agent.invoke({
        "messages": [HumanMessage(content="What's the weather in Seattle?")]
    })

    evaluation = evaluator(
        outputs=result["messages"],
    )
    # {
    #     'key': 'trajectory_accuracy',
    #     'score': True,
    #     'comment': 'The provided agent trajectory is reasonable...'
    # }
    assert evaluation["score"] is True

With reference trajectoryIf you have a reference trajectory, you can add an extra variable to your prompt and pass in the reference trajectory. Below, we use the prebuilt TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE prompt and configure the reference_outputs variable:Copyevaluator = create_trajectory_llm_as_judge(
    model="openai:o3-mini",
    prompt=TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE,
)
evaluation = judge_with_reference(
    outputs=result["messages"],
    reference_outputs=reference_trajectory,
)

For more configurability over how the LLM evaluates the trajectory, visit the repository.
```

##### ​Async Support

All agentevals evaluators support Python asyncio. For evaluators that use factory functions, async versions are available by adding async after create_ in the function name.

Async judge and evaluator exampleCopyfrom agentevals.trajectory.llm import create_async_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT
```python
from agentevals.trajectory.match import create_async_trajectory_match_evaluator

async_judge = create_async_trajectory_llm_as_judge(
    model="openai:o3-mini",
    prompt=TRAJECTORY_ACCURACY_PROMPT,
)

async_evaluator = create_async_trajectory_match_evaluator(
    trajectory_match_mode="strict",
)

async def test_async_evaluation():
    result = await agent.ainvoke({
        "messages": [HumanMessage(content="What's the weather?")]
    })

    evaluation = await async_judge(outputs=result["messages"])
    assert evaluation["score"] is True
```

#### ​LangSmith Integration

For tracking experiments over time, you can log evaluator results to LangSmith, a platform for building production-grade LLM applications that includes tracing, evaluation, and experimentation tools.

First, set up LangSmith by setting the required environment variables:

Copyexport LANGSMITH_API_KEY="your_langsmith_api_key"
export LANGSMITH_TRACING="true"

LangSmith offers two main approaches for running evaluations: pytest integration and the evaluate function.

Using pytest integrationCopyimport pytest
```python
from langsmith import testing as t
from agentevals.trajectory.llm import create_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT

trajectory_evaluator = create_trajectory_llm_as_judge(
    model="openai:o3-mini",
    prompt=TRAJECTORY_ACCURACY_PROMPT,
)

@pytest.mark.langsmith
def test_trajectory_accuracy():
    result = agent.invoke({
        "messages": [HumanMessage(content="What's the weather in SF?")]
    })

    reference_trajectory = [
        HumanMessage(content="What's the weather in SF?"),
        AIMessage(content="", tool_calls=[
            {"id": "call_1", "name": "get_weather", "args": {"city": "SF"}},
        ]),
        ToolMessage(content="It's 75 degrees and sunny in SF.", tool_call_id="call_1"),
        AIMessage(content="The weather in SF is 75 degrees and sunny."),
    ]

    # Log inputs, outputs, and reference outputs to LangSmith
    t.log_inputs({})
    t.log_outputs({"messages": result["messages"]})
    t.log_reference_outputs({"messages": reference_trajectory})

    trajectory_evaluator(
        outputs=result["messages"],
        reference_outputs=reference_trajectory
    )
Run the evaluation with pytest:Copypytest test_trajectory.py --langsmith-output
Results will be automatically logged to LangSmith.

Using the evaluate functionAlternatively, you can create a dataset in LangSmith and use the evaluate function:Copyfrom langsmith import Client
from agentevals.trajectory.llm import create_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT

client = Client()

trajectory_evaluator = create_trajectory_llm_as_judge(
    model="openai:o3-mini",
    prompt=TRAJECTORY_ACCURACY_PROMPT,
)

def run_agent(inputs):
    """Your agent function that returns trajectory messages."""
    return agent.invoke(inputs)["messages"]

experiment_results = client.evaluate(
    run_agent,
    data="your_dataset_name",
    evaluators=[trajectory_evaluator]
)
Results will be automatically logged to LangSmith.

To learn more about evaluating your agent, see the LangSmith docs.
```

#### ​Recording & Replaying HTTP Calls

Integration tests that call real LLM APIs can be slow and expensive, especially when run frequently in CI/CD pipelines. We recommend using a library for recording HTTP requests and responses, then replaying them in subsequent runs without making actual network calls.

You can use vcrpy to achieve this. If you’re using pytest, the pytest-recording plugin provides a simple way to enable this with minimal configuration. Request/responses are recorded in cassettes, which are then used to mock the real network calls in subsequent runs.

Set up your conftest.py file to filter out sensitive information from the cassettes:

conftest.pyCopyimport pytest

```python
@pytest.fixture(scope="session")
def vcr_config():
    return {
        "filter_headers": [
            ("authorization", "XXXX"),
            ("x-api-key", "XXXX"),
            # ... other headers you want to mask
        ],
        "filter_query_parameters": [
            ("api_key", "XXXX"),
            ("key", "XXXX"),
        ],
    }

Then configure your project to recognise the vcr marker:

pytest.inipyproject.tomlCopy[pytest]
markers =
    vcr: record/replay HTTP via VCR
addopts = --record-mode=once

The --record-mode=once option records HTTP interactions on the first run and replays them on subsequent runs.

Now, simply decorate your tests with the vcr marker:

Copy@pytest.mark.vcr()
def test_agent_trajectory():
    # ...

The first time you run this test, your agent will make real network calls and pytest will generate a cassette file test_agent_trajectory.yaml in the tests/cassettes directory. Subsequent runs will use that cassette to mock the real network calls, granted the agent’s requests don’t change from the previous run. If they do, the test will fail and you’ll need to delete the cassette and rerun the test to record fresh interactions.

When you modify prompts, add new tools, or change expected trajectories, your saved cassettes will become outdated and your existing tests will fail. You should delete the corresponding cassette files and rerun the tests to record fresh interactions.

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```


---

## Model Context Protocol (MCP) - Docs by LangChain {#doc-25}

**Source:** [https://docs.langchain.com/oss/python/langchain/mcp](https://docs.langchain.com/oss/python/langchain/mcp)

### Model Context Protocol (MCP)

Copy page

#### ​Quickstart

Install the langchain-mcp-adapters library:

pipuvCopypip install langchain-mcp-adapters

langchain-mcp-adapters enables agents to use tools defined across one or more MCP servers.

MultiServerMCPClient is stateless by default. Each tool invocation creates a fresh MCP ClientSession, executes the tool, and then cleans up. See the stateful sessions section for more details.

Accessing multiple MCP serversCopyfrom langchain_mcp_adapters.client import MultiServerMCPClient
```python
from langchain.agents import create_agent

client = MultiServerMCPClient(
    {
        "math": {
            "transport": "stdio",  # Local subprocess communication
            "command": "python",
            # Absolute path to your math_server.py file
            "args": ["/path/to/math_server.py"],
        },
        "weather": {
            "transport": "http",  # HTTP-based remote server
            # Ensure you start your weather server on port 8000
            "url": "http://localhost:8000/mcp",
        }
    }
)

tools = await client.get_tools()
agent = create_agent(
    "claude-sonnet-4-5-20250929",
    tools
)
math_response = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "what's (3 + 5) x 12?"}]}
)
weather_response = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "what is the weather in nyc?"}]}
)
```

#### ​Custom servers

To create a custom MCP server, use the FastMCP library:

pipuvCopypip install fastmcp

To test your agent with MCP tool servers, use the following examples:

Math server (stdio transport)Weather server (streamable HTTP transport)Copyfrom fastmcp import FastMCP

mcp = FastMCP("Math")

```python
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

#### ​Transports

MCP supports different transport mechanisms for client-server communication.

##### ​HTTP

The http transport (also referred to as streamable-http) uses HTTP requests for client-server communication. See the MCP HTTP transport specification for more details.

Copyclient = MultiServerMCPClient(
```
    {
        "weather": {
            "transport": "http",
            "url": "http://localhost:8000/mcp",
        }
    }
)
```

###### ​Passing headers

When connecting to MCP servers over HTTP, you can include custom headers (e.g., for authentication or tracing) using the headers field in the connection configuration. This is supported for sse (deprecated by MCP spec) and streamable_http transports.

Passing headers with MultiServerMCPClientCopyfrom langchain_mcp_adapters.client import MultiServerMCPClient
```python
from langchain.agents import create_agent

client = MultiServerMCPClient(
    {
        "weather": {
            "transport": "http",
            "url": "http://localhost:8000/mcp",
            "headers": {
                "Authorization": "Bearer YOUR_TOKEN",
                "X-Custom-Header": "custom-value"
            },
        }
    }
)
tools = await client.get_tools()
agent = create_agent("openai:gpt-4.1", tools)
response = await agent.ainvoke({"messages": "what is the weather in nyc?"})
```

###### ​Authentication

The langchain-mcp-adapters library uses the official MCP SDK under the hood, which allows you to provide a custom authentication mechanism by implementing the httpx.Auth interface.

Copyfrom langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient(
```
    {
        "weather": {
            "transport": "http",
            "url": "http://localhost:8000/mcp",
            "auth": auth,
        }
    }
)

- Example custom auth implementation
- Built-in OAuth flow
```

##### ​stdio

Client launches server as a subprocess and communicates via standard input/output. Best for local tools and simple setups.

Unlike HTTP transports, stdio connections are inherently stateful—the subprocess persists for the lifetime of the client connection. However, when using MultiServerMCPClient without explicit session management, each tool call still creates a new session. See stateful sessions for managing persistent connections.

Copyclient = MultiServerMCPClient(
```
    {
        "math": {
            "transport": "stdio",
            "command": "python",
            "args": ["/path/to/math_server.py"],
        }
    }
)
```

#### ​Stateful sessions

By default, MultiServerMCPClient is stateless—each tool invocation creates a fresh MCP session, executes the tool, and then cleans up.

If you need to control the lifecycle of an MCP session (for example, when working with a stateful server that maintains context across tool calls), you can create a persistent ClientSession using client.session().

Using MCP ClientSession for stateful tool usageCopyfrom langchain_mcp_adapters.client import MultiServerMCPClient
```python
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import create_agent

client = MultiServerMCPClient({...})

# Create a session explicitly
async with client.session("server_name") as session:
    # Pass the session to load tools, resources, or prompts
    tools = await load_mcp_tools(session)
    agent = create_agent(
        "anthropic:claude-3-7-sonnet-latest",
        tools
    )
```

#### ​Core features

##### ​Tools

Tools allow MCP servers to expose executable functions that LLMs can invoke to perform actions—such as querying databases, calling APIs, or interacting with external systems. LangChain converts MCP tools into LangChain tools, making them directly usable in any LangChain agent or workflow.

###### ​Loading tools

Use client.get_tools() to retrieve tools from MCP servers and pass them to your agent:

Copyfrom langchain_mcp_adapters.client import MultiServerMCPClient
```python
from langchain.agents import create_agent

client = MultiServerMCPClient({...})
tools = await client.get_tools()
agent = create_agent("claude-sonnet-4-5-20250929", tools)
```

###### ​Structured content

MCP tools can return structured content alongside the human-readable text response. This is useful when a tool needs to return machine-parseable data (like JSON) in addition to text that gets shown to the model.

When an MCP tool returns structuredContent, the adapter wraps it in an MCPToolArtifact and returns it as the tool’s artifact. You can access this using the artifact field on the ToolMessage. You can also use interceptors to process or transform structured content automatically.

Extracting structured content from artifact

After invoking your agent, you can access the structured content from tool messages in the response:

Copyfrom langchain_mcp_adapters.client import MultiServerMCPClient
```python
from langchain.agents import create_agent
from langchain.messages import ToolMessage

client = MultiServerMCPClient({...})
tools = await client.get_tools()
agent = create_agent("claude-sonnet-4-5-20250929", tools)

result = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "Get data from the server"}]}
)

# Extract structured content from tool messages
for message in result["messages"]:
    if isinstance(message, ToolMessage) and message.artifact:
        structured_content = message.artifact["structured_content"]

Appending structured content via interceptor

If you want structured content to be visible in the conversation history (visible to the model), you can use an interceptor to automatically append structured content to the tool result:

Copyimport json

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.interceptors import MCPToolCallRequest
from mcp.types import TextContent

async def append_structured_content(request: MCPToolCallRequest, handler):
    """Append structured content from artifact to tool message."""
    result = await handler(request)
    if result.structuredContent:
        result.content += [
            TextContent(type="text", text=json.dumps(result.structuredContent)),
        ]
    return result

client = MultiServerMCPClient({...}, tool_interceptors=[append_structured_content])
```

###### ​Multimodal tool content

MCP tools can return multimodal content (images, text, etc.) in their responses. When an MCP server returns content with multiple parts (e.g., text and images), the adapter converts them to LangChain’s standard content blocks. You can access the standardized representation via the content_blocks property on the ToolMessage:

Copyfrom langchain_mcp_adapters.client import MultiServerMCPClient
```python
from langchain.agents import create_agent

client = MultiServerMCPClient({...})
tools = await client.get_tools()
agent = create_agent("claude-sonnet-4-5-20250929", tools)

result = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "Take a screenshot of the current page"}]}
)

# Access multimodal content from tool messages
for message in result["messages"]:
    if message.type == "tool":
        # Raw content in provider-native format
        print(f"Raw content: {message.content}")

        # Standardized content blocks  #
        for block in message.content_blocks:
            if block["type"] == "text":
                print(f"Text: {block['text']}")
            elif block["type"] == "image":
                print(f"Image URL: {block.get('url')}")
                print(f"Image base64: {block.get('base64', '')[:50]}...")

This allows you to handle multimodal tool responses in a provider-agnostic way, regardless of how the underlying MCP server formats its content.
```

##### ​Resources

Resources allow MCP servers to expose data—such as files, database records, or API responses—that can be read by clients. LangChain converts MCP resources into Blob objects, which provide a unified interface for handling both text and binary content.

###### ​Loading resources

Use client.get_resources() to load resources from an MCP server:

Copyfrom langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({...})

# Load all resources from a server
blobs = await client.get_resources("server_name")

# Or load specific resources by URI
blobs = await client.get_resources("server_name", uris=["file:///path/to/file.txt"])

for blob in blobs:
    print(f"URI: {blob.metadata['uri']}, MIME type: {blob.mimetype}")
    print(blob.as_string())  # For text content

You can also use load_mcp_resources directly with a session for more control:

Copyfrom langchain_mcp_adapters.client import MultiServerMCPClient
```python
from langchain_mcp_adapters.resources import load_mcp_resources

client = MultiServerMCPClient({...})

async with client.session("server_name") as session:
    # Load all resources
    blobs = await load_mcp_resources(session)

    # Or load specific resources by URI
    blobs = await load_mcp_resources(session, uris=["file:///path/to/file.txt"])
```

##### ​Prompts

Prompts allow MCP servers to expose reusable prompt templates that can be retrieved and used by clients. LangChain converts MCP prompts into messages, making them easy to integrate into chat-based workflows.

###### ​Loading prompts

Use client.get_prompt() to load a prompt from an MCP server:

Copyfrom langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({...})

# Load a prompt by name
messages = await client.get_prompt("server_name", "summarize")

# Load a prompt with arguments
messages = await client.get_prompt(
    "server_name",
    "code_review",
    arguments={"language": "python", "focus": "security"}
)

# Use the messages in your workflow
for message in messages:
    print(f"{message.type}: {message.content}")

You can also use load_mcp_prompt directly with a session for more control:

Copyfrom langchain_mcp_adapters.client import MultiServerMCPClient
```python
from langchain_mcp_adapters.prompts import load_mcp_prompt

client = MultiServerMCPClient({...})

async with client.session("server_name") as session:
    # Load a prompt by name
    messages = await load_mcp_prompt(session, "summarize")

    # Load a prompt with arguments
    messages = await load_mcp_prompt(
        session,
        "code_review",
        arguments={"language": "python", "focus": "security"}
    )
```

#### ​Advanced features

##### ​Tool Interceptors

MCP servers run as separate processes—they can’t access LangGraph runtime information like the store, context, or agent state. Interceptors bridge this gap by giving you access to this runtime context during MCP tool execution.

Interceptors also provide middleware-like control over tool calls: you can modify requests, implement retries, add headers dynamically, or short-circuit execution entirely.

SectionDescriptionAccessing runtime contextRead user IDs, API keys, store data, and agent stateState updates and commandsUpdate agent state or control graph flow with CommandWriting interceptorsPatterns for modifying requests, composing interceptors, and error handling

###### ​Accessing runtime context

When MCP tools are used within a LangChain agent (via create_agent), interceptors receive access to the ToolRuntime context. This provides access to the tool call ID, state, config, and store—enabling powerful patterns for accessing user data, persisting information, and controlling agent behavior.

Runtime context Store State Tool call IDAccess user-specific configuration like user IDs, API keys, or permissions that are passed at invocation time:Inject user context into MCP tool callsCopyfrom dataclasses import dataclass
```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.interceptors import MCPToolCallRequest
from langchain.agents import create_agent

@dataclass
class Context:
    user_id: str
    api_key: str

async def inject_user_context(
    request: MCPToolCallRequest,
    handler,
):
    """Inject user credentials into MCP tool calls."""
    runtime = request.runtime
    user_id = runtime.context.user_id
    api_key = runtime.context.api_key

    # Add user context to tool arguments
    modified_request = request.override(
        args={**request.args, "user_id": user_id}
    )
    return await handler(modified_request)

client = MultiServerMCPClient(
    {...},
    tool_interceptors=[inject_user_context],
)
tools = await client.get_tools()
agent = create_agent("gpt-4o", tools, context_schema=Context)

# Invoke with user context
result = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "Search my orders"}]},
    context={"user_id": "user_123", "api_key": "sk-..."}
)
Access long-term memory to retrieve user preferences or persist data across conversations:Access user preferences from storeCopyfrom dataclasses import dataclass
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.interceptors import MCPToolCallRequest
from langchain.agents import create_agent
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

async def personalize_search(
    request: MCPToolCallRequest,
    handler,
):
    """Personalize MCP tool calls using stored preferences."""
    runtime = request.runtime
    user_id = runtime.context.user_id
    store = runtime.store

    # Read user preferences from store
    prefs = store.get(("preferences",), user_id)

    if prefs and request.name == "search":
        # Apply user's preferred language and result limit
        modified_args = {
            **request.args,
            "language": prefs.value.get("language", "en"),
            "limit": prefs.value.get("result_limit", 10),
        }
        request = request.override(args=modified_args)

    return await handler(request)

client = MultiServerMCPClient(
    {...},
    tool_interceptors=[personalize_search],
)
tools = await client.get_tools()
agent = create_agent(
    "gpt-4o",
    tools,
    context_schema=Context,
    store=InMemoryStore()
)
Access conversation state to make decisions based on the current session:Filter tools based on authentication stateCopyfrom langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.interceptors import MCPToolCallRequest
from langchain.messages import ToolMessage

async def require_authentication(
    request: MCPToolCallRequest,
    handler,
):
    """Block sensitive MCP tools if user is not authenticated."""
    runtime = request.runtime
    state = runtime.state
    is_authenticated = state.get("authenticated", False)

    sensitive_tools = ["delete_file", "update_settings", "export_data"]

    if request.name in sensitive_tools and not is_authenticated:
        # Return error instead of calling tool
        return ToolMessage(
            content="Authentication required. Please log in first.",
            tool_call_id=runtime.tool_call_id,
        )

    return await handler(request)

client = MultiServerMCPClient(
    {...},
    tool_interceptors=[require_authentication],
)
Access the tool call ID to return properly formatted responses or track tool executions:Return custom responses with tool call IDCopyfrom langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.interceptors import MCPToolCallRequest
from langchain.messages import ToolMessage

async def rate_limit_interceptor(
    request: MCPToolCallRequest,
    handler,
):
    """Rate limit expensive MCP tool calls."""
    runtime = request.runtime
    tool_call_id = runtime.tool_call_id

    # Check rate limit (simplified example)
    if is_rate_limited(request.name):
        return ToolMessage(
            content="Rate limit exceeded. Please try again later.",
            tool_call_id=tool_call_id,
        )

    result = await handler(request)

    # Log successful tool call
    log_tool_execution(tool_call_id, request.name, success=True)

    return result

client = MultiServerMCPClient(
    {...},
    tool_interceptors=[rate_limit_interceptor],
)

For more context engineering patterns, see Context engineering and Tools.
```

###### ​State updates and commands

Interceptors can return Command objects to update agent state or control graph execution flow. This is useful for tracking task progress, switching between agents, or ending execution early.

Mark task complete and switch agentsCopyfrom langchain.agents import AgentState, create_agent
```python
from langchain_mcp_adapters.interceptors import MCPToolCallRequest
from langchain.messages import ToolMessage
from langgraph.types import Command

async def handle_task_completion(
    request: MCPToolCallRequest,
    handler,
):
    """Mark task complete and hand off to summary agent."""
    result = await handler(request)

    if request.name == "submit_order":
        return Command(
            update={
                "messages": [result] if isinstance(result, ToolMessage) else [],
                "task_status": "completed",
            },
            goto="summary_agent",
        )

    return result

Use Command with goto="__end__" to end execution early:

End agent run on completionCopyasync def end_on_success(
    request: MCPToolCallRequest,
    handler,
):
    """End agent run when task is marked complete."""
    result = await handler(request)

    if request.name == "mark_complete":
        return Command(
            update={"messages": [result], "status": "done"},
            goto="__end__",
        )

    return result
```

###### ​Custom interceptors

Interceptors are async functions that wrap tool execution, enabling request/response modification, retry logic, and other cross-cutting concerns. They follow an “onion” pattern where the first interceptor in the list is the outermost layer.

Basic pattern

An interceptor is an async function that receives a request and a handler. You can modify the request before calling the handler, modify the response after, or skip the handler entirely.

Basic interceptor patternCopyfrom langchain_mcp_adapters.client import MultiServerMCPClient
```python
from langchain_mcp_adapters.interceptors import MCPToolCallRequest

async def logging_interceptor(
    request: MCPToolCallRequest,
    handler,
):
    """Log tool calls before and after execution."""
    print(f"Calling tool: {request.name} with args: {request.args}")
    result = await handler(request)
    print(f"Tool {request.name} returned: {result}")
    return result

client = MultiServerMCPClient(
    {"math": {"transport": "stdio", "command": "python", "args": ["/path/to/server.py"]}},
    tool_interceptors=[logging_interceptor],
)

Modifying requests

Use request.override() to create a modified request. This follows an immutable pattern, leaving the original request unchanged.

Modifying tool argumentsCopyasync def double_args_interceptor(
    request: MCPToolCallRequest,
    handler,
):
    """Double all numeric arguments before execution."""
    modified_args = {k: v * 2 for k, v in request.args.items()}
    modified_request = request.override(args=modified_args)
    return await handler(modified_request)

# Original call: add(a=2, b=3) becomes add(a=4, b=6)

Modifying headers at runtime

Interceptors can modify HTTP headers dynamically based on the request context:

Dynamic header modificationCopyasync def auth_header_interceptor(
    request: MCPToolCallRequest,
    handler,
):
    """Add authentication headers based on the tool being called."""
    token = get_token_for_tool(request.name)
    modified_request = request.override(
        headers={"Authorization": f"Bearer {token}"}
    )
    return await handler(modified_request)

Composing interceptors

Multiple interceptors compose in “onion” order — the first interceptor in the list is the outermost layer:

Composing multiple interceptorsCopyasync def outer_interceptor(request, handler):
    print("outer: before")
    result = await handler(request)
    print("outer: after")
    return result

async def inner_interceptor(request, handler):
    print("inner: before")
    result = await handler(request)
    print("inner: after")
    return result

client = MultiServerMCPClient(
    {...},
    tool_interceptors=[outer_interceptor, inner_interceptor],
)

# Execution order:
# outer: before -> inner: before -> tool execution -> inner: after -> outer: after

Error handling

Use interceptors to catch tool execution errors and implement retry logic:

Retry on errorCopyimport asyncio

async def retry_interceptor(
    request: MCPToolCallRequest,
    handler,
    max_retries: int = 3,
    delay: float = 1.0,
):
    """Retry failed tool calls with exponential backoff."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return await handler(request)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                print(f"Tool {request.name} failed (attempt {attempt + 1}), retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
    raise last_error

client = MultiServerMCPClient(
    {...},
    tool_interceptors=[retry_interceptor],
)

You can also catch specific error types and return fallback values:

Error handling with fallbackCopyasync def fallback_interceptor(
    request: MCPToolCallRequest,
    handler,
):
    """Return a fallback value if tool execution fails."""
    try:
        return await handler(request)
    except TimeoutError:
        return f"Tool {request.name} timed out. Please try again later."
    except ConnectionError:
        return f"Could not connect to {request.name} service. Using cached data."
```

##### ​Progress notifications

Subscribe to progress updates for long-running tool executions:

Progress callbackCopyfrom langchain_mcp_adapters.client import MultiServerMCPClient
```python
from langchain_mcp_adapters.callbacks import Callbacks, CallbackContext

async def on_progress(
    progress: float,
    total: float | None,
    message: str | None,
    context: CallbackContext,
):
    """Handle progress updates from MCP servers."""
    percent = (progress / total * 100) if total else progress
    tool_info = f" ({context.tool_name})" if context.tool_name else ""
    print(f"[{context.server_name}{tool_info}] Progress: {percent:.1f}% - {message}")

client = MultiServerMCPClient(
    {...},
    callbacks=Callbacks(on_progress=on_progress),
)

The CallbackContext provides:

- server_name: Name of the MCP server
- tool_name: Name of the tool being executed (available during tool calls)
```

##### ​Logging

The MCP protocol supports logging notifications from servers. Use the Callbacks class to subscribe to these events.

Logging callbackCopyfrom langchain_mcp_adapters.client import MultiServerMCPClient
```python
from langchain_mcp_adapters.callbacks import Callbacks, CallbackContext
from mcp.types import LoggingMessageNotificationParams

async def on_logging_message(
    params: LoggingMessageNotificationParams,
    context: CallbackContext,
):
    """Handle log messages from MCP servers."""
    print(f"[{context.server_name}] {params.level}: {params.data}")

client = MultiServerMCPClient(
    {...},
    callbacks=Callbacks(on_logging_message=on_logging_message),
)
```

##### ​Elicitation

Elicitation allows MCP servers to request additional input from users during tool execution. Instead of requiring all inputs upfront, servers can interactively ask for information as needed.

###### ​Server setup

Define a tool that uses ctx.elicit() to request user input with a schema:

MCP server with elicitationCopyfrom pydantic import BaseModel
```python
from mcp.server.fastmcp import Context, FastMCP

server = FastMCP("Profile")

class UserDetails(BaseModel):
    email: str
    age: int

@server.tool()
async def create_profile(name: str, ctx: Context) -> str:
    """Create a user profile, requesting details via elicitation."""
    result = await ctx.elicit(
        message=f"Please provide details for {name}'s profile:",
        schema=UserDetails,
    )
    if result.action == "accept" and result.data:
        return f"Created profile for {name}: email={result.data.email}, age={result.data.age}"
    if result.action == "decline":
        return f"User declined. Created minimal profile for {name}."
    return "Profile creation cancelled."

if __name__ == "__main__":
    server.run(transport="http")
```

###### ​Client setup

Handle elicitation requests by providing a callback to MultiServerMCPClient:

Handling elicitation requestsCopyfrom langchain_mcp_adapters.client import MultiServerMCPClient
```python
from langchain_mcp_adapters.callbacks import Callbacks, CallbackContext
from mcp.shared.context import RequestContext
from mcp.types import ElicitRequestParams, ElicitResult

async def on_elicitation(
    mcp_context: RequestContext,
    params: ElicitRequestParams,
    context: CallbackContext,
) -> ElicitResult:
    """Handle elicitation requests from MCP servers."""
    # In a real application, you would prompt the user for input
    # based on params.message and params.requestedSchema
    return ElicitResult(
        action="accept",
        content={"email": "user@example.com", "age": 25},
    )

client = MultiServerMCPClient(
    {
        "profile": {
            "url": "http://localhost:8000/mcp",
            "transport": "http",
        }
    },
    callbacks=Callbacks(on_elicitation=on_elicitation),
)
```

###### ​Response actions

The elicitation callback can return one of three actions:

ActionDescriptionacceptUser provided valid input. Include the data in the content field.declineUser chose not to provide the requested information.cancelUser cancelled the operation entirely.

Response action examplesCopy# Accept with data
ElicitResult(action="accept", content={"email": "user@example.com", "age": 25})

# Decline (user doesn't want to provide info)
ElicitResult(action="decline")

# Cancel (abort the operation)
ElicitResult(action="cancel")

#### ​Additional resources

- MCP documentation
- MCP Transport documentation
- langchain-mcp-adapters
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Retrieval - Docs by LangChain {#doc-26}

**Source:** [https://docs.langchain.com/oss/python/langchain/retrieval](https://docs.langchain.com/oss/python/langchain/retrieval)

### Retrieval

Copy page

#### ​Building a knowledge base

A knowledge base is a repository of documents or structured data used during retrieval.

If you need a custom knowledge base, you can use LangChain’s document loaders and vector stores to build one from your own data.

If you already have a knowledge base (e.g., a SQL database, CRM, or internal documentation system), you do not need to rebuild it. You can:
Connect it as a tool for an agent in Agentic RAG.
Query it and supply the retrieved content as context to the LLM (2-Step RAG).

See the following tutorial to build a searchable knowledge base and minimal RAG workflow:

Tutorial: Semantic searchLearn how to create a searchable knowledge base from your own data using LangChain’s document loaders, embeddings, and vector stores.
In this tutorial, you’ll build a search engine over a PDF, enabling retrieval of passages relevant to a query. You’ll also implement a minimal RAG workflow on top of this engine to see how external knowledge can be integrated into LLM reasoning.Learn more

​From retrieval to RAG

Retrieval allows LLMs to access relevant context at runtime. But most real-world applications go one step further: they integrate retrieval with generation to produce grounded, context-aware answers.

This is the core idea behind Retrieval-Augmented Generation (RAG). The retrieval pipeline becomes a foundation for a broader system that combines search with generation.

​Retrieval Pipeline

A typical retrieval workflow looks like this:

Each component is modular: you can swap loaders, splitters, embeddings, or vector stores without rewriting the app’s logic.

​Building Blocks

Document loadersIngest data from external sources (Google Drive, Slack, Notion, etc.), returning standardized Document objects.Learn moreText splittersBreak large docs into smaller chunks that will be retrievable individually and fit within a model’s context window.Learn moreEmbedding modelsAn embedding model turns text into a vector of numbers so that texts with similar meaning land close together in that vector space.Learn moreVector storesSpecialized databases for storing and searching embeddings.Learn moreRetrieversA retriever is an interface that returns documents given an unstructured query.Learn more

​RAG Architectures

RAG can be implemented in multiple ways, depending on your system’s needs. We outline each type in the sections below.

ArchitectureDescriptionControlFlexibilityLatencyExample Use Case2-Step RAGRetrieval always happens before generation. Simple and predictableHigh❌ Low⚡ FastFAQs, documentation botsAgentic RAGAn LLM-powered agent decides when and how to retrieve during reasoning❌ LowHigh⏳ VariableResearch assistants with access to multiple toolsHybridCombines characteristics of both approaches with validation steps⚖️ Medium⚖️ Medium⏳ VariableDomain-specific Q&A with quality validation

Latency: Latency is generally more predictable in 2-Step RAG, as the maximum number of LLM calls is known and capped. This predictability assumes that LLM inference time is the dominant factor. However, real-world latency may also be affected by the performance of retrieval steps—such as API response times, network delays, or database queries—which can vary based on the tools and infrastructure in use.

​2-step RAG

In 2-Step RAG, the retrieval step is always executed before the generation step. This architecture is straightforward and predictable, making it suitable for many applications where the retrieval of relevant documents is a clear prerequisite for generating an answer.

Tutorial: Retrieval-Augmented Generation (RAG)See how to build a Q&A chatbot that can answer questions grounded in your data using Retrieval-Augmented Generation.
This tutorial walks through two approaches:
A RAG agent that runs searches with a flexible tool—great for general-purpose use.
A 2-step RAG chain that requires just one LLM call per query—fast and efficient for simpler tasks.
Learn more

​Agentic RAG

Agentic Retrieval-Augmented Generation (RAG) combines the strengths of Retrieval-Augmented Generation with agent-based reasoning. Instead of retrieving documents before answering, an agent (powered by an LLM) reasons step-by-step and decides when and how to retrieve information during the interaction.

The only thing an agent needs to enable RAG behavior is access to one or more tools that can fetch external knowledge — such as documentation loaders, web APIs, or database queries.

Copyimport requests
```python
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent

@tool
def fetch_url(url: str) -> str:
    """Fetch text content from a URL"""
    response = requests.get(url, timeout=10.0)
    response.raise_for_status()
    return response.text

system_prompt = """\
Use fetch_url when you need to fetch information from a web-page; quote relevant snippets.
"""

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[fetch_url], # A tool for retrieval
    system_prompt=system_prompt,
)

Show Extended example: Agentic RAG for LangGraph's llms.txtThis example implements an Agentic RAG system to assist users in querying LangGraph documentation. The agent begins by loading llms.txt, which lists available documentation URLs, and can then dynamically use a fetch_documentation tool to retrieve and process the relevant content based on the user’s question.Copyimport requests
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.tools import tool
from markdownify import markdownify

ALLOWED_DOMAINS = ["https://langchain-ai.github.io/"]
LLMS_TXT = 'https://langchain-ai.github.io/langgraph/llms.txt'

@tool
def fetch_documentation(url: str) -> str:
    """Fetch and convert documentation from a URL"""
    if not any(url.startswith(domain) for domain in ALLOWED_DOMAINS):
        return (
            "Error: URL not allowed. "
            f"Must start with one of: {', '.join(ALLOWED_DOMAINS)}"
        )
    response = requests.get(url, timeout=10.0)
    response.raise_for_status()
    return markdownify(response.text)

# We will fetch the content of llms.txt, so this can
# be done ahead of time without requiring an LLM request.
llms_txt_content = requests.get(LLMS_TXT).text

# System prompt for the agent
system_prompt = f"""
You are an expert Python developer and technical assistant.
Your primary role is to help users with questions about LangGraph and related tools.

Instructions:

1. If a user asks a question you're unsure about — or one that likely involves API usage,
   behavior, or configuration — you MUST use the `fetch_documentation` tool to consult the relevant docs.
2. When citing documentation, summarize clearly and include relevant context from the content.
3. Do not use any URLs outside of the allowed domain.
4. If a documentation fetch fails, tell the user and proceed with your best expert understanding.

You can access official documentation from the following approved sources:

{llms_txt_content}

You MUST consult the documentation to get up to date documentation
before answering a user's question about LangGraph.

Your answers should be clear, concise, and technically accurate.
"""

tools = [fetch_documentation]

model = init_chat_model("claude-sonnet-4-0", max_tokens=32_000)

agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt,
    name="Agentic RAG",
)

response = agent.invoke({
    'messages': [
        HumanMessage(content=(
            "Write a short example of a langgraph agent using the "
            "prebuilt create react agent. the agent should be able "
            "to look up stock pricing information."
        ))
    ]
})

print(response['messages'][-1].content)

Tutorial: Retrieval-Augmented Generation (RAG)See how to build a Q&A chatbot that can answer questions grounded in your data using Retrieval-Augmented Generation.
This tutorial walks through two approaches:
A RAG agent that runs searches with a flexible tool—great for general-purpose use.
A 2-step RAG chain that requires just one LLM call per query—fast and efficient for simpler tasks.
Learn more

​Hybrid RAG

Hybrid RAG combines characteristics of both 2-Step and Agentic RAG. It introduces intermediate steps such as query preprocessing, retrieval validation, and post-generation checks. These systems offer more flexibility than fixed pipelines while maintaining some control over execution.

Typical components include:

- Query enhancement: Modify the input question to improve retrieval quality. This can involve rewriting unclear queries, generating multiple variations, or expanding queries with additional context.
- Retrieval validation: Evaluate whether retrieved documents are relevant and sufficient. If not, the system may refine the query and retrieve again.
- Answer validation: Check the generated answer for accuracy, completeness, and alignment with source content. If needed, the system can regenerate or revise the answer.
The architecture often supports multiple iterations between these steps:

This architecture is suitable for:

- Applications with ambiguous or underspecified queries
- Systems that require validation or quality control steps
- Workflows involving multiple sources or iterative refinement
Tutorial: Agentic RAG with Self-CorrectionAn example of Hybrid RAG that combines agentic reasoning with retrieval and self-correction.Learn more

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```

#### Tutorial: Semantic search

Learn how to create a searchable knowledge base from your own data using LangChain’s document loaders, embeddings, and vector stores.
In this tutorial, you’ll build a search engine over a PDF, enabling retrieval of passages relevant to a query. You’ll also implement a minimal RAG workflow on top of this engine to see how external knowledge can be integrated into LLM reasoning.

Learn more

##### ​From retrieval to RAG

Retrieval allows LLMs to access relevant context at runtime. But most real-world applications go one step further: they integrate retrieval with generation to produce grounded, context-aware answers.

This is the core idea behind Retrieval-Augmented Generation (RAG). The retrieval pipeline becomes a foundation for a broader system that combines search with generation.

##### ​Retrieval Pipeline

A typical retrieval workflow looks like this:

Each component is modular: you can swap loaders, splitters, embeddings, or vector stores without rewriting the app’s logic.

##### ​Building Blocks

Document loadersIngest data from external sources (Google Drive, Slack, Notion, etc.), returning standardized Document objects.Learn moreText splittersBreak large docs into smaller chunks that will be retrievable individually and fit within a model’s context window.Learn moreEmbedding modelsAn embedding model turns text into a vector of numbers so that texts with similar meaning land close together in that vector space.Learn moreVector storesSpecialized databases for storing and searching embeddings.Learn moreRetrieversA retriever is an interface that returns documents given an unstructured query.Learn more

​RAG Architectures

RAG can be implemented in multiple ways, depending on your system’s needs. We outline each type in the sections below.

ArchitectureDescriptionControlFlexibilityLatencyExample Use Case2-Step RAGRetrieval always happens before generation. Simple and predictableHigh❌ Low⚡ FastFAQs, documentation botsAgentic RAGAn LLM-powered agent decides when and how to retrieve during reasoning❌ LowHigh⏳ VariableResearch assistants with access to multiple toolsHybridCombines characteristics of both approaches with validation steps⚖️ Medium⚖️ Medium⏳ VariableDomain-specific Q&A with quality validation

Latency: Latency is generally more predictable in 2-Step RAG, as the maximum number of LLM calls is known and capped. This predictability assumes that LLM inference time is the dominant factor. However, real-world latency may also be affected by the performance of retrieval steps—such as API response times, network delays, or database queries—which can vary based on the tools and infrastructure in use.

​2-step RAG

In 2-Step RAG, the retrieval step is always executed before the generation step. This architecture is straightforward and predictable, making it suitable for many applications where the retrieval of relevant documents is a clear prerequisite for generating an answer.

Tutorial: Retrieval-Augmented Generation (RAG)See how to build a Q&A chatbot that can answer questions grounded in your data using Retrieval-Augmented Generation.
This tutorial walks through two approaches:
A RAG agent that runs searches with a flexible tool—great for general-purpose use.
A 2-step RAG chain that requires just one LLM call per query—fast and efficient for simpler tasks.
Learn more

​Agentic RAG

Agentic Retrieval-Augmented Generation (RAG) combines the strengths of Retrieval-Augmented Generation with agent-based reasoning. Instead of retrieving documents before answering, an agent (powered by an LLM) reasons step-by-step and decides when and how to retrieve information during the interaction.

The only thing an agent needs to enable RAG behavior is access to one or more tools that can fetch external knowledge — such as documentation loaders, web APIs, or database queries.

Copyimport requests
```python
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent

@tool
def fetch_url(url: str) -> str:
    """Fetch text content from a URL"""
    response = requests.get(url, timeout=10.0)
    response.raise_for_status()
    return response.text

system_prompt = """\
Use fetch_url when you need to fetch information from a web-page; quote relevant snippets.
"""

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[fetch_url], # A tool for retrieval
    system_prompt=system_prompt,
)

Show Extended example: Agentic RAG for LangGraph's llms.txtThis example implements an Agentic RAG system to assist users in querying LangGraph documentation. The agent begins by loading llms.txt, which lists available documentation URLs, and can then dynamically use a fetch_documentation tool to retrieve and process the relevant content based on the user’s question.Copyimport requests
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.tools import tool
from markdownify import markdownify

ALLOWED_DOMAINS = ["https://langchain-ai.github.io/"]
LLMS_TXT = 'https://langchain-ai.github.io/langgraph/llms.txt'

@tool
def fetch_documentation(url: str) -> str:
    """Fetch and convert documentation from a URL"""
    if not any(url.startswith(domain) for domain in ALLOWED_DOMAINS):
        return (
            "Error: URL not allowed. "
            f"Must start with one of: {', '.join(ALLOWED_DOMAINS)}"
        )
    response = requests.get(url, timeout=10.0)
    response.raise_for_status()
    return markdownify(response.text)

# We will fetch the content of llms.txt, so this can
# be done ahead of time without requiring an LLM request.
llms_txt_content = requests.get(LLMS_TXT).text

# System prompt for the agent
system_prompt = f"""
You are an expert Python developer and technical assistant.
Your primary role is to help users with questions about LangGraph and related tools.

Instructions:

1. If a user asks a question you're unsure about — or one that likely involves API usage,
   behavior, or configuration — you MUST use the `fetch_documentation` tool to consult the relevant docs.
2. When citing documentation, summarize clearly and include relevant context from the content.
3. Do not use any URLs outside of the allowed domain.
4. If a documentation fetch fails, tell the user and proceed with your best expert understanding.

You can access official documentation from the following approved sources:

{llms_txt_content}

You MUST consult the documentation to get up to date documentation
before answering a user's question about LangGraph.

Your answers should be clear, concise, and technically accurate.
"""

tools = [fetch_documentation]

model = init_chat_model("claude-sonnet-4-0", max_tokens=32_000)

agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt,
    name="Agentic RAG",
)

response = agent.invoke({
    'messages': [
        HumanMessage(content=(
            "Write a short example of a langgraph agent using the "
            "prebuilt create react agent. the agent should be able "
            "to look up stock pricing information."
        ))
    ]
})

print(response['messages'][-1].content)

Tutorial: Retrieval-Augmented Generation (RAG)See how to build a Q&A chatbot that can answer questions grounded in your data using Retrieval-Augmented Generation.
This tutorial walks through two approaches:
A RAG agent that runs searches with a flexible tool—great for general-purpose use.
A 2-step RAG chain that requires just one LLM call per query—fast and efficient for simpler tasks.
Learn more

​Hybrid RAG

Hybrid RAG combines characteristics of both 2-Step and Agentic RAG. It introduces intermediate steps such as query preprocessing, retrieval validation, and post-generation checks. These systems offer more flexibility than fixed pipelines while maintaining some control over execution.

Typical components include:

- Query enhancement: Modify the input question to improve retrieval quality. This can involve rewriting unclear queries, generating multiple variations, or expanding queries with additional context.
- Retrieval validation: Evaluate whether retrieved documents are relevant and sufficient. If not, the system may refine the query and retrieve again.
- Answer validation: Check the generated answer for accuracy, completeness, and alignment with source content. If needed, the system can regenerate or revise the answer.
The architecture often supports multiple iterations between these steps:

This architecture is suitable for:

- Applications with ambiguous or underspecified queries
- Systems that require validation or quality control steps
- Workflows involving multiple sources or iterative refinement
Tutorial: Agentic RAG with Self-CorrectionAn example of Hybrid RAG that combines agentic reasoning with retrieval and self-correction.Learn more

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```

#### Document loaders

Ingest data from external sources (Google Drive, Slack, Notion, etc.), returning standardized Document objects.

Learn more

#### Text splitters

Break large docs into smaller chunks that will be retrievable individually and fit within a model’s context window.

Learn more

#### Embedding models

An embedding model turns text into a vector of numbers so that texts with similar meaning land close together in that vector space.

Learn more

#### Vector stores

Specialized databases for storing and searching embeddings.

Learn more

#### Retrievers

A retriever is an interface that returns documents given an unstructured query.

Learn more

#### ​RAG Architectures

RAG can be implemented in multiple ways, depending on your system’s needs. We outline each type in the sections below.

ArchitectureDescriptionControlFlexibilityLatencyExample Use Case2-Step RAGRetrieval always happens before generation. Simple and predictableHigh❌ Low⚡ FastFAQs, documentation botsAgentic RAGAn LLM-powered agent decides when and how to retrieve during reasoning❌ LowHigh⏳ VariableResearch assistants with access to multiple toolsHybridCombines characteristics of both approaches with validation steps⚖️ Medium⚖️ Medium⏳ VariableDomain-specific Q&A with quality validation

Latency: Latency is generally more predictable in 2-Step RAG, as the maximum number of LLM calls is known and capped. This predictability assumes that LLM inference time is the dominant factor. However, real-world latency may also be affected by the performance of retrieval steps—such as API response times, network delays, or database queries—which can vary based on the tools and infrastructure in use.

##### ​2-step RAG

In 2-Step RAG, the retrieval step is always executed before the generation step. This architecture is straightforward and predictable, making it suitable for many applications where the retrieval of relevant documents is a clear prerequisite for generating an answer.

Tutorial: Retrieval-Augmented Generation (RAG)See how to build a Q&A chatbot that can answer questions grounded in your data using Retrieval-Augmented Generation.
This tutorial walks through two approaches:
A RAG agent that runs searches with a flexible tool—great for general-purpose use.
A 2-step RAG chain that requires just one LLM call per query—fast and efficient for simpler tasks.
Learn more

​Agentic RAG

Agentic Retrieval-Augmented Generation (RAG) combines the strengths of Retrieval-Augmented Generation with agent-based reasoning. Instead of retrieving documents before answering, an agent (powered by an LLM) reasons step-by-step and decides when and how to retrieve information during the interaction.

The only thing an agent needs to enable RAG behavior is access to one or more tools that can fetch external knowledge — such as documentation loaders, web APIs, or database queries.

Copyimport requests
```python
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent

@tool
def fetch_url(url: str) -> str:
    """Fetch text content from a URL"""
    response = requests.get(url, timeout=10.0)
    response.raise_for_status()
    return response.text

system_prompt = """\
Use fetch_url when you need to fetch information from a web-page; quote relevant snippets.
"""

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[fetch_url], # A tool for retrieval
    system_prompt=system_prompt,
)

Show Extended example: Agentic RAG for LangGraph's llms.txtThis example implements an Agentic RAG system to assist users in querying LangGraph documentation. The agent begins by loading llms.txt, which lists available documentation URLs, and can then dynamically use a fetch_documentation tool to retrieve and process the relevant content based on the user’s question.Copyimport requests
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.tools import tool
from markdownify import markdownify

ALLOWED_DOMAINS = ["https://langchain-ai.github.io/"]
LLMS_TXT = 'https://langchain-ai.github.io/langgraph/llms.txt'

@tool
def fetch_documentation(url: str) -> str:
    """Fetch and convert documentation from a URL"""
    if not any(url.startswith(domain) for domain in ALLOWED_DOMAINS):
        return (
            "Error: URL not allowed. "
            f"Must start with one of: {', '.join(ALLOWED_DOMAINS)}"
        )
    response = requests.get(url, timeout=10.0)
    response.raise_for_status()
    return markdownify(response.text)

# We will fetch the content of llms.txt, so this can
# be done ahead of time without requiring an LLM request.
llms_txt_content = requests.get(LLMS_TXT).text

# System prompt for the agent
system_prompt = f"""
You are an expert Python developer and technical assistant.
Your primary role is to help users with questions about LangGraph and related tools.

Instructions:

1. If a user asks a question you're unsure about — or one that likely involves API usage,
   behavior, or configuration — you MUST use the `fetch_documentation` tool to consult the relevant docs.
2. When citing documentation, summarize clearly and include relevant context from the content.
3. Do not use any URLs outside of the allowed domain.
4. If a documentation fetch fails, tell the user and proceed with your best expert understanding.

You can access official documentation from the following approved sources:

{llms_txt_content}

You MUST consult the documentation to get up to date documentation
before answering a user's question about LangGraph.

Your answers should be clear, concise, and technically accurate.
"""

tools = [fetch_documentation]

model = init_chat_model("claude-sonnet-4-0", max_tokens=32_000)

agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt,
    name="Agentic RAG",
)

response = agent.invoke({
    'messages': [
        HumanMessage(content=(
            "Write a short example of a langgraph agent using the "
            "prebuilt create react agent. the agent should be able "
            "to look up stock pricing information."
        ))
    ]
})

print(response['messages'][-1].content)

Tutorial: Retrieval-Augmented Generation (RAG)See how to build a Q&A chatbot that can answer questions grounded in your data using Retrieval-Augmented Generation.
This tutorial walks through two approaches:
A RAG agent that runs searches with a flexible tool—great for general-purpose use.
A 2-step RAG chain that requires just one LLM call per query—fast and efficient for simpler tasks.
Learn more

​Hybrid RAG

Hybrid RAG combines characteristics of both 2-Step and Agentic RAG. It introduces intermediate steps such as query preprocessing, retrieval validation, and post-generation checks. These systems offer more flexibility than fixed pipelines while maintaining some control over execution.

Typical components include:

- Query enhancement: Modify the input question to improve retrieval quality. This can involve rewriting unclear queries, generating multiple variations, or expanding queries with additional context.
- Retrieval validation: Evaluate whether retrieved documents are relevant and sufficient. If not, the system may refine the query and retrieve again.
- Answer validation: Check the generated answer for accuracy, completeness, and alignment with source content. If needed, the system can regenerate or revise the answer.
The architecture often supports multiple iterations between these steps:

This architecture is suitable for:

- Applications with ambiguous or underspecified queries
- Systems that require validation or quality control steps
- Workflows involving multiple sources or iterative refinement
Tutorial: Agentic RAG with Self-CorrectionAn example of Hybrid RAG that combines agentic reasoning with retrieval and self-correction.Learn more

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```

#### Tutorial: Retrieval-Augmented Generation (RAG)

See how to build a Q&A chatbot that can answer questions grounded in your data using Retrieval-Augmented Generation.
This tutorial walks through two approaches:
A RAG agent that runs searches with a flexible tool—great for general-purpose use.
A 2-step RAG chain that requires just one LLM call per query—fast and efficient for simpler tasks.

Learn more

##### ​Agentic RAG

Agentic Retrieval-Augmented Generation (RAG) combines the strengths of Retrieval-Augmented Generation with agent-based reasoning. Instead of retrieving documents before answering, an agent (powered by an LLM) reasons step-by-step and decides when and how to retrieve information during the interaction.

The only thing an agent needs to enable RAG behavior is access to one or more tools that can fetch external knowledge — such as documentation loaders, web APIs, or database queries.

Copyimport requests
```python
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent

@tool
def fetch_url(url: str) -> str:
    """Fetch text content from a URL"""
    response = requests.get(url, timeout=10.0)
    response.raise_for_status()
    return response.text

system_prompt = """\
Use fetch_url when you need to fetch information from a web-page; quote relevant snippets.
"""

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[fetch_url], # A tool for retrieval
    system_prompt=system_prompt,
)

Show Extended example: Agentic RAG for LangGraph's llms.txtThis example implements an Agentic RAG system to assist users in querying LangGraph documentation. The agent begins by loading llms.txt, which lists available documentation URLs, and can then dynamically use a fetch_documentation tool to retrieve and process the relevant content based on the user’s question.Copyimport requests
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.tools import tool
from markdownify import markdownify

ALLOWED_DOMAINS = ["https://langchain-ai.github.io/"]
LLMS_TXT = 'https://langchain-ai.github.io/langgraph/llms.txt'

@tool
def fetch_documentation(url: str) -> str:
    """Fetch and convert documentation from a URL"""
    if not any(url.startswith(domain) for domain in ALLOWED_DOMAINS):
        return (
            "Error: URL not allowed. "
            f"Must start with one of: {', '.join(ALLOWED_DOMAINS)}"
        )
    response = requests.get(url, timeout=10.0)
    response.raise_for_status()
    return markdownify(response.text)

# We will fetch the content of llms.txt, so this can
# be done ahead of time without requiring an LLM request.
llms_txt_content = requests.get(LLMS_TXT).text

# System prompt for the agent
system_prompt = f"""
You are an expert Python developer and technical assistant.
Your primary role is to help users with questions about LangGraph and related tools.

Instructions:

1. If a user asks a question you're unsure about — or one that likely involves API usage,
   behavior, or configuration — you MUST use the `fetch_documentation` tool to consult the relevant docs.
2. When citing documentation, summarize clearly and include relevant context from the content.
3. Do not use any URLs outside of the allowed domain.
4. If a documentation fetch fails, tell the user and proceed with your best expert understanding.

You can access official documentation from the following approved sources:

{llms_txt_content}

You MUST consult the documentation to get up to date documentation
before answering a user's question about LangGraph.

Your answers should be clear, concise, and technically accurate.
"""

tools = [fetch_documentation]

model = init_chat_model("claude-sonnet-4-0", max_tokens=32_000)

agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt,
    name="Agentic RAG",
)

response = agent.invoke({
    'messages': [
        HumanMessage(content=(
            "Write a short example of a langgraph agent using the "
            "prebuilt create react agent. the agent should be able "
            "to look up stock pricing information."
        ))
    ]
})

print(response['messages'][-1].content)

Tutorial: Retrieval-Augmented Generation (RAG)See how to build a Q&A chatbot that can answer questions grounded in your data using Retrieval-Augmented Generation.
This tutorial walks through two approaches:
A RAG agent that runs searches with a flexible tool—great for general-purpose use.
A 2-step RAG chain that requires just one LLM call per query—fast and efficient for simpler tasks.
Learn more

​Hybrid RAG

Hybrid RAG combines characteristics of both 2-Step and Agentic RAG. It introduces intermediate steps such as query preprocessing, retrieval validation, and post-generation checks. These systems offer more flexibility than fixed pipelines while maintaining some control over execution.

Typical components include:

- Query enhancement: Modify the input question to improve retrieval quality. This can involve rewriting unclear queries, generating multiple variations, or expanding queries with additional context.
- Retrieval validation: Evaluate whether retrieved documents are relevant and sufficient. If not, the system may refine the query and retrieve again.
- Answer validation: Check the generated answer for accuracy, completeness, and alignment with source content. If needed, the system can regenerate or revise the answer.
The architecture often supports multiple iterations between these steps:

This architecture is suitable for:

- Applications with ambiguous or underspecified queries
- Systems that require validation or quality control steps
- Workflows involving multiple sources or iterative refinement
Tutorial: Agentic RAG with Self-CorrectionAn example of Hybrid RAG that combines agentic reasoning with retrieval and self-correction.Learn more

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```

#### Tutorial: Retrieval-Augmented Generation (RAG)

See how to build a Q&A chatbot that can answer questions grounded in your data using Retrieval-Augmented Generation.
This tutorial walks through two approaches:
A RAG agent that runs searches with a flexible tool—great for general-purpose use.
A 2-step RAG chain that requires just one LLM call per query—fast and efficient for simpler tasks.

Learn more

##### ​Hybrid RAG

Hybrid RAG combines characteristics of both 2-Step and Agentic RAG. It introduces intermediate steps such as query preprocessing, retrieval validation, and post-generation checks. These systems offer more flexibility than fixed pipelines while maintaining some control over execution.

Typical components include:

- Query enhancement: Modify the input question to improve retrieval quality. This can involve rewriting unclear queries, generating multiple variations, or expanding queries with additional context.
- Retrieval validation: Evaluate whether retrieved documents are relevant and sufficient. If not, the system may refine the query and retrieve again.
- Answer validation: Check the generated answer for accuracy, completeness, and alignment with source content. If needed, the system can regenerate or revise the answer.
The architecture often supports multiple iterations between these steps:

This architecture is suitable for:

- Applications with ambiguous or underspecified queries
- Systems that require validation or quality control steps
- Workflows involving multiple sources or iterative refinement
Tutorial: Agentic RAG with Self-CorrectionAn example of Hybrid RAG that combines agentic reasoning with retrieval and self-correction.Learn more

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.

#### Tutorial: Agentic RAG with Self-Correction

An example of Hybrid RAG that combines agentic reasoning with retrieval and self-correction.

Learn more


---

## LangSmith Studio - Docs by LangChain {#doc-27}

**Source:** [https://docs.langchain.com/oss/python/langchain/studio](https://docs.langchain.com/oss/python/langchain/studio)

### LangSmith Studio

Copy page

#### ​Prerequisites

Before you begin, ensure you have the following:

- A LangSmith account: Sign up (for free) or log in at smith.langchain.com.
- A LangSmith API key: Follow the Create an API key guide.
- If you don’t want data traced to LangSmith, set LANGSMITH_TRACING=false in your application’s .env file. With tracing disabled, no data leaves your local server.

#### ​Set up local Agent server

##### ​1. Install the LangGraph CLI

The LangGraph CLI provides a local development server (also called Agent Server) that connects your agent to Studio.

Copy# Python >= 3.11 is required.
```bash
pip install --upgrade "langgraph-cli[inmem]"
```

##### ​2. Prepare your agent

If you already have a LangChain agent, you can use it directly. This example uses a simple email agent:

agent.pyCopyfrom langchain.agents import create_agent

```python
def send_email(to: str, subject: str, body: str):
    """Send an email"""
    email = {
        "to": to,
        "subject": subject,
        "body": body
    }
    # ... email sending logic

    return f"Email sent to {to}"

agent = create_agent(
    "gpt-4o",
    tools=[send_email],
    system_prompt="You are an email assistant. Always use the send_email tool.",
)
```

##### ​3. Environment variables

Studio requires a LangSmith API key to connect your local agent. Create a .env file in the root of your project and add your API key from LangSmith.

Ensure your .env file is not committed to version control, such as Git.

.envCopyLANGSMITH_API_KEY=lsv2...

##### ​4. Create a LangGraph config file

The LangGraph CLI uses a configuration file to locate your agent and manage dependencies. Create a langgraph.json file in your app’s directory:

```
langgraph.jsonCopy{
  "dependencies": ["."],
  "graphs": {
    "agent": "./src/agent.py:agent"
  },
  "env": ".env"
}

The create_agent function automatically returns a compiled LangGraph graph, which is what the graphs key expects in the configuration file.

For detailed explanations of each key in the JSON object of the configuration file, refer to the LangGraph configuration file reference.

At this point, the project structure will look like this:

Copymy-app/
├── src
│   └── agent.py
├── .env
└── langgraph.json
```

##### ​5. Install dependencies

Install your project dependencies from the root directory:

pipuvCopypip install langchain langchain-openai

##### ​6. View your agent in Studio

Start the development server to connect your agent to Studio:

Copylanggraph dev

Safari blocks localhost connections to Studio. To work around this, run the above command with --tunnel to access Studio via a secure tunnel.

Once the server is running, your agent is accessible both via API at http://127.0.0.1:2024 and through the Studio UI at https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024:

With Studio connected to your local agent, you can iterate quickly on your agent’s behavior. Run a test input, inspect the full execution trace including prompts, tool arguments, return values, and token/latency metrics. When something goes wrong, Studio captures exceptions with the surrounding state to help you understand what happened.

The development server supports hot-reloading—make changes to prompts or tool signatures in your code, and Studio reflects them immediately. Re-run conversation threads from any step to test your changes without starting over. This workflow scales from simple single-tool agents to complex multi-node graphs.

For more information on how to run Studio, refer to the following guides in the LangSmith docs:

- Run application
- Manage assistants
- Manage threads
- Iterate on prompts
- Debug LangSmith traces
- Add node to dataset

#### ​Video guide

For more information about local and deployed agents, see Set up local Agent Server and Deploy.

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Long-term memory - Docs by LangChain {#doc-28}

**Source:** [https://docs.langchain.com/oss/python/langchain/long-term-memory](https://docs.langchain.com/oss/python/langchain/long-term-memory)

### Long-term memory

Copy page

#### ​Overview

LangChain agents use LangGraph persistence to enable long-term memory. This is a more advanced topic and requires knowledge of LangGraph to use.

#### ​Memory storage

LangGraph stores long-term memories as JSON documents in a store.

Each memory is organized under a custom namespace (similar to a folder) and a distinct key (like a file name). Namespaces often include user or org IDs or other labels that makes it easier to organize information.

This structure enables hierarchical organization of memories. Cross-namespace searching is then supported through content filters.

Copyfrom langgraph.store.memory import InMemoryStore

```python
def embed(texts: list[str]) -> list[list[float]]:
    # Replace with an actual embedding function or LangChain embeddings object
    return [[1.0, 2.0] * len(texts)]

# InMemoryStore saves data to an in-memory dictionary. Use a DB-backed store in production use.
store = InMemoryStore(index={"embed": embed, "dims": 2})
user_id = "my-user"
application_context = "chitchat"
namespace = (user_id, application_context)
store.put(
    namespace,
    "a-memory",
    {
        "rules": [
            "User likes short, direct language",
            "User only speaks English & python",
        ],
        "my-key": "my-value",
    },
)
# get the "memory" by ID
item = store.get(namespace, "a-memory")
# search for "memories" within this namespace, filtering on content equivalence, sorted by vector similarity
items = store.search(
    namespace, filter={"my-key": "my-value"}, query="language preferences"
)

For more information about the memory store, see the Persistence guide.
```

#### ​Read long-term memory in tools

A tool the agent can use to look up user informationCopyfrom dataclasses import dataclass

```python
from langchain_core.runnables import RunnableConfig
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

# InMemoryStore saves data to an in-memory dictionary. Use a DB-backed store in production.
store = InMemoryStore()

# Write sample data to the store using the put method
store.put(
    ("users",),  # Namespace to group related data together (users namespace for user data)
    "user_123",  # Key within the namespace (user ID as key)
    {
        "name": "John Smith",
        "language": "English",
    }  # Data to store for the given user
)

@tool
def get_user_info(runtime: ToolRuntime[Context]) -> str:
    """Look up user info."""
    # Access the store - same as that provided to `create_agent`
    store = runtime.store
    user_id = runtime.context.user_id
    # Retrieve data from store - returns StoreValue object with value and metadata
    user_info = store.get(("users",), user_id)
    return str(user_info.value) if user_info else "Unknown user"

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[get_user_info],
    # Pass store to agent - enables agent to access store when running tools
    store=store,
    context_schema=Context
)

# Run the agent
agent.invoke(
    {"messages": [{"role": "user", "content": "look up user information"}]},
    context=Context(user_id="user_123")
)
```

#### ​Write long-term memory from tools

Example of a tool that updates user informationCopyfrom dataclasses import dataclass
```python
from typing_extensions import TypedDict

from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langgraph.store.memory import InMemoryStore

# InMemoryStore saves data to an in-memory dictionary. Use a DB-backed store in production.
store = InMemoryStore()

@dataclass
class Context:
    user_id: str

# TypedDict defines the structure of user information for the LLM
class UserInfo(TypedDict):
    name: str

# Tool that allows agent to update user information (useful for chat applications)
@tool
def save_user_info(user_info: UserInfo, runtime: ToolRuntime[Context]) -> str:
    """Save user info."""
    # Access the store - same as that provided to `create_agent`
    store = runtime.store
    user_id = runtime.context.user_id
    # Store data in the store (namespace, key, data)
    store.put(("users",), user_id, user_info)
    return "Successfully saved user info."

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[save_user_info],
    store=store,
    context_schema=Context
)

# Run the agent
agent.invoke(
    {"messages": [{"role": "user", "content": "My name is John Smith"}]},
    # user_id passed in context to identify whose information is being updated
    context=Context(user_id="user_123")
)

# You can access the store directly to get the value
store.get(("users",), "user_123").value

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```


---

## Human-in-the-loop - Docs by LangChain {#doc-29}

**Source:** [https://docs.langchain.com/oss/python/langchain/human-in-the-loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)

### Human-in-the-loop

Copy page

#### ​Interrupt decision types

The middleware defines three built-in ways a human can respond to an interrupt:

Decision TypeDescriptionExample Use CaseapproveThe action is approved as-is and executed without changes.Send an email draft exactly as written✏️ editThe tool call is executed with modifications.Change the recipient before sending an email❌ rejectThe tool call is rejected, with an explanation added to the conversation.Reject an email draft and explain how to rewrite it

The available decision types for each tool depend on the policy you configure in interrupt_on.
When multiple tool calls are paused at the same time, each action requires a separate decision.
Decisions must be provided in the same order as the actions appear in the interrupt request.

When editing tool arguments, make changes conservatively. Significant modifications to the original arguments may cause the model to re-evaluate its approach and potentially execute the tool multiple times or take unexpected actions.

#### ​Configuring interrupts

To use HITL, add the middleware to the agent’s middleware list when creating the agent.

You configure it with a mapping of tool actions to the decision types that are allowed for each action. The middleware will interrupt execution when a tool call matches an action in the mapping.

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model="gpt-4o",
    tools=[write_file_tool, execute_sql_tool, read_data_tool],
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                "write_file": True,  # All decisions (approve, edit, reject) allowed
                "execute_sql": {"allowed_decisions": ["approve", "reject"]},  # No editing allowed
                # Safe operation, no approval needed
                "read_data": False,
            },
            # Prefix for interrupt messages - combined with tool name and args to form the full message
            # e.g., "Tool execution pending approval: execute_sql with query='DELETE FROM...'"
            # Individual tools can override this by specifying a "description" in their interrupt config
            description_prefix="Tool execution pending approval",
        ),
    ],
    # Human-in-the-loop requires checkpointing to handle interrupts.
    # In production, use a persistent checkpointer like AsyncPostgresSaver.
    checkpointer=InMemorySaver(),
)

You must configure a checkpointer to persist the graph state across interrupts.
In production, use a persistent checkpointer like AsyncPostgresSaver. For testing or prototyping, use InMemorySaver.When invoking the agent, pass a config that includes the thread ID to associate execution with a conversation thread.
See the LangGraph interrupts documentation for details.

Configuration options​interrupt_ondictrequiredMapping of tool names to approval configs. Values can be True (interrupt with default config), False (auto-approve), or an InterruptOnConfig object.​description_prefixstringdefault:"Tool execution requires approval"Prefix for action request descriptionsInterruptOnConfig options:​allowed_decisionslist[string]List of allowed decisions: 'approve', 'edit', or 'reject'​descriptionstring | callableStatic string or callable function for custom description
```

#### ​Responding to interrupts

When you invoke the agent, it runs until it either completes or an interrupt is raised. An interrupt is triggered when a tool call matches the policy you configured in interrupt_on. In that case, the invocation result will include an __interrupt__ field with the actions that require review. You can then present those actions to a reviewer and resume execution once decisions are provided.

Copyfrom langgraph.types import Command

# Human-in-the-loop leverages LangGraph's persistence layer.
# You must provide a thread ID to associate the execution with a conversation thread,
# so the conversation can be paused and resumed (as is needed for human review).
config = {"configurable": {"thread_id": "some_id"}}
# Run the graph until the interrupt is hit.
result = agent.invoke(
```
    {
        "messages": [
            {
                "role": "user",
                "content": "Delete old records from the database",
            }
        ]
    },
    config=config
)

# The interrupt contains the full HITL request with action_requests and review_configs
print(result['__interrupt__'])
# > [
# >    Interrupt(
# >       value={
# >          'action_requests': [
# >             {
# >                'name': 'execute_sql',
# >                'arguments': {'query': 'DELETE FROM records WHERE created_at < NOW() - INTERVAL \'30 days\';'},
# >                'description': 'Tool execution pending approval\n\nTool: execute_sql\nArgs: {...}'
# >             }
# >          ],
# >          'review_configs': [
# >             {
# >                'action_name': 'execute_sql',
# >                'allowed_decisions': ['approve', 'reject']
# >             }
# >          ]
# >       }
# >    )
# > ]

# Resume with approval decision
agent.invoke(
    Command(
        resume={"decisions": [{"type": "approve"}]}  # or "reject"
    ),
    config=config # Same thread ID to resume the paused conversation
)
```

##### ​Decision types

approve ✏️ edit ❌ rejectUse approve to approve the tool call as-is and execute it without changes.Copyagent.invoke(
    Command(
        # Decisions are provided as a list, one per action under review.
        # The order of decisions must match the order of actions
        # listed in the `__interrupt__` request.
```
        resume={
            "decisions": [
                {
                    "type": "approve",
                }
            ]
        }
    ),
    config=config  # Same thread ID to resume the paused conversation
)
Use edit to modify the tool call before execution.
Provide the edited action with the new tool name and arguments.Copyagent.invoke(
    Command(
        # Decisions are provided as a list, one per action under review.
        # The order of decisions must match the order of actions
        # listed in the `__interrupt__` request.
        resume={
            "decisions": [
                {
                    "type": "edit",
                    # Edited action with tool name and args
                    "edited_action": {
                        # Tool name to call.
                        # Will usually be the same as the original action.
                        "name": "new_tool_name",
                        # Arguments to pass to the tool.
                        "args": {"key1": "new_value", "key2": "original_value"},
                    }
                }
            ]
        }
    ),
    config=config  # Same thread ID to resume the paused conversation
)
When editing tool arguments, make changes conservatively. Significant modifications to the original arguments may cause the model to re-evaluate its approach and potentially execute the tool multiple times or take unexpected actions.Use reject to reject the tool call and provide feedback instead of execution.Copyagent.invoke(
    Command(
        # Decisions are provided as a list, one per action under review.
        # The order of decisions must match the order of actions
        # listed in the `__interrupt__` request.
        resume={
            "decisions": [
                {
                    "type": "reject",
                    # An explanation about why the action was rejected
                    "message": "No, this is wrong because ..., instead do this ...",
                }
            ]
        }
    ),
    config=config  # Same thread ID to resume the paused conversation
)
The message is added to the conversation as feedback to help the agent understand why the action was rejected and what it should do instead.​Multiple decisionsWhen multiple actions are under review, provide a decision for each action in the same order as they appear in the interrupt:Copy{
    "decisions": [
        {"type": "approve"},
        {
            "type": "edit",
            "edited_action": {
                "name": "tool_name",
                "args": {"param": "new_value"}
            }
        },
        {
            "type": "reject",
            "message": "This action is not allowed"
        }
    ]
}

​Streaming with human-in-the-loop

You can use stream() instead of invoke() to get real-time updates while the agent runs and handles interrupts. Use stream_mode=['updates', 'messages'] to stream both agent progress and LLM tokens.

Copyfrom langgraph.types import Command

config = {"configurable": {"thread_id": "some_id"}}

# Stream agent progress and LLM tokens until interrupt
for mode, chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Delete old records from the database"}]},
    config=config,
    stream_mode=["updates", "messages"],
):
    if mode == "messages":
        # LLM token
        token, metadata = chunk
        if token.content:
            print(token.content, end="", flush=True)
    elif mode == "updates":
        # Check for interrupt
        if "__interrupt__" in chunk:
            print(f"\n\nInterrupt: {chunk['__interrupt__']}")

# Resume with streaming after human decision
for mode, chunk in agent.stream(
    Command(resume={"decisions": [{"type": "approve"}]}),
    config=config,
    stream_mode=["updates", "messages"],
):
    if mode == "messages":
        token, metadata = chunk
        if token.content:
            print(token.content, end="", flush=True)

See the Streaming guide for more details on stream modes.

​Execution lifecycle

The middleware defines an after_model hook that runs after the model generates a response but before any tool calls are executed:

- The agent invokes the model to generate a response.
- The middleware inspects the response for tool calls.
- If any calls require human input, the middleware builds a HITLRequest with action_requests and review_configs and calls interrupt.
- The agent waits for human decisions.
- Based on the HITLResponse decisions, the middleware executes approved or edited calls, synthesizes ToolMessage’s for rejected calls, and resumes execution.
​Custom HITL logic

For more specialized workflows, you can build custom HITL logic directly using the interrupt primitive and middleware abstraction.

Review the execution lifecycle above to understand how to integrate interrupts into the agent’s operation.

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```

##### ​Multiple decisions

When multiple actions are under review, provide a decision for each action in the same order as they appear in the interrupt:

```
Copy{
    "decisions": [
        {"type": "approve"},
        {
            "type": "edit",
            "edited_action": {
                "name": "tool_name",
                "args": {"param": "new_value"}
            }
        },
        {
            "type": "reject",
            "message": "This action is not allowed"
        }
    ]
}
```

#### ​Streaming with human-in-the-loop

You can use stream() instead of invoke() to get real-time updates while the agent runs and handles interrupts. Use stream_mode=['updates', 'messages'] to stream both agent progress and LLM tokens.

Copyfrom langgraph.types import Command

config = {"configurable": {"thread_id": "some_id"}}

# Stream agent progress and LLM tokens until interrupt
for mode, chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Delete old records from the database"}]},
    config=config,
    stream_mode=["updates", "messages"],
):
    if mode == "messages":
        # LLM token
        token, metadata = chunk
        if token.content:
            print(token.content, end="", flush=True)
    elif mode == "updates":
        # Check for interrupt
        if "__interrupt__" in chunk:
            print(f"\n\nInterrupt: {chunk['__interrupt__']}")

# Resume with streaming after human decision
for mode, chunk in agent.stream(
    Command(resume={"decisions": [{"type": "approve"}]}),
    config=config,
    stream_mode=["updates", "messages"],
):
    if mode == "messages":
        token, metadata = chunk
        if token.content:
            print(token.content, end="", flush=True)

See the Streaming guide for more details on stream modes.

#### ​Execution lifecycle

The middleware defines an after_model hook that runs after the model generates a response but before any tool calls are executed:

- The agent invokes the model to generate a response.
- The middleware inspects the response for tool calls.
- If any calls require human input, the middleware builds a HITLRequest with action_requests and review_configs and calls interrupt.
- The agent waits for human decisions.
- Based on the HITLResponse decisions, the middleware executes approved or edited calls, synthesizes ToolMessage’s for rejected calls, and resumes execution.

#### ​Custom HITL logic

For more specialized workflows, you can build custom HITL logic directly using the interrupt primitive and middleware abstraction.

Review the execution lifecycle above to understand how to integrate interrupts into the agent’s operation.

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Runtime - Docs by LangChain {#doc-30}

**Source:** [https://docs.langchain.com/oss/python/langchain/runtime](https://docs.langchain.com/oss/python/langchain/runtime)

### Runtime

Copy page

#### ​Overview

LangChain’s create_agent runs on LangGraph’s runtime under the hood.

LangGraph exposes a Runtime object with the following information:

- Context: static information like user id, db connections, or other dependencies for an agent invocation
- Store: a BaseStore instance used for long-term memory
- Stream writer: an object used for streaming information via the "custom" stream mode
Runtime context provides dependency injection for your tools and middleware. Instead of hardcoding values or using global state, you can inject runtime dependencies (like database connections, user IDs, or configuration) when invoking your agent. This makes your tools more testable, reusable, and flexible.

You can access the runtime information within tools and middleware.

#### ​Access

When creating an agent with create_agent, you can specify a context_schema to define the structure of the context stored in the agent Runtime.

When invoking the agent, pass the context argument with the relevant configuration for the run:

Copyfrom dataclasses import dataclass

```python
from langchain.agents import create_agent

@dataclass
class Context:
    user_name: str

agent = create_agent(
    model="gpt-5-nano",
    tools=[...],
    context_schema=Context
)

agent.invoke(
    {"messages": [{"role": "user", "content": "What's my name?"}]},
    context=Context(user_name="John Smith")
)
```

##### ​Inside tools

You can access the runtime information inside tools to:

- Access the context
- Read or write long-term memory
- Write to the custom stream (ex, tool progress / updates)
Use the ToolRuntime parameter to access the Runtime object inside a tool.

Copyfrom dataclasses import dataclass
```python
from langchain.tools import tool, ToolRuntime

@dataclass
class Context:
    user_id: str

@tool
def fetch_user_email_preferences(runtime: ToolRuntime[Context]) -> str:
    """Fetch the user's email preferences from the store."""
    user_id = runtime.context.user_id

    preferences: str = "The user prefers you to write a brief and polite email."
    if runtime.store:
        if memory := runtime.store.get(("users",), user_id):
            preferences = memory.value["preferences"]

    return preferences
```

##### ​Inside middleware

You can access runtime information in middleware to create dynamic prompts, modify messages, or control agent behavior based on user context.

Use request.runtime to access the Runtime object inside middleware decorators. The runtime object is available in the ModelRequest parameter passed to middleware functions.

Copyfrom dataclasses import dataclass

```python
from langchain.messages import AnyMessage
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import dynamic_prompt, ModelRequest, before_model, after_model
from langgraph.runtime import Runtime

@dataclass
class Context:
    user_name: str

# Dynamic prompts
@dynamic_prompt
def dynamic_system_prompt(request: ModelRequest) -> str:
    user_name = request.runtime.context.user_name
    system_prompt = f"You are a helpful assistant. Address the user as {user_name}."
    return system_prompt

# Before model hook
@before_model
def log_before_model(state: AgentState, runtime: Runtime[Context]) -> dict | None:
    print(f"Processing request for user: {runtime.context.user_name}")
    return None

# After model hook
@after_model
def log_after_model(state: AgentState, runtime: Runtime[Context]) -> dict | None:
    print(f"Completed request for user: {runtime.context.user_name}")
    return None

agent = create_agent(
    model="gpt-5-nano",
    tools=[...],
    middleware=[dynamic_system_prompt, log_before_model, log_after_model],
    context_schema=Context
)

agent.invoke(
    {"messages": [{"role": "user", "content": "What's my name?"}]},
    context=Context(user_name="John Smith")
)

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```


---

## Context engineering in agents - Docs by LangChain {#doc-31}

**Source:** [https://docs.langchain.com/oss/python/langchain/context-engineering](https://docs.langchain.com/oss/python/langchain/context-engineering)

### Context engineering in agents

Copy page

#### ​Overview

The hard part of building agents (or any LLM application) is making them reliable enough. While they may work for a prototype, they often fail in real-world use cases.

##### ​Why do agents fail?

When agents fail, it’s usually because the LLM call inside the agent took the wrong action / didn’t do what we expected. LLMs fail for one of two reasons:

- The underlying LLM is not capable enough
- The “right” context was not passed to the LLM
More often than not - it’s actually the second reason that causes agents to not be reliable.

Context engineering is providing the right information and tools in the right format so the LLM can accomplish a task. This is the number one job of AI Engineers. This lack of “right” context is the number one blocker for more reliable agents, and LangChain’s agent abstractions are uniquely designed to facilitate context engineering.

New to context engineering? Start with the conceptual overview to understand the different types of context and when to use them.

##### ​The agent loop

A typical agent loop consists of two main steps:

- Model call - calls the LLM with a prompt and available tools, returns either a response or a request to execute tools
- Tool execution - executes the tools that the LLM requested, returns tool results
This loop continues until the LLM decides to finish.

##### ​What you can control

To build reliable agents, you need to control what happens at each step of the agent loop, as well as what happens between steps.

Context TypeWhat You ControlTransient or PersistentModel ContextWhat goes into model calls (instructions, message history, tools, response format)TransientTool ContextWhat tools can access and produce (reads/writes to state, store, runtime context)PersistentLife-cycle ContextWhat happens between model and tool calls (summarization, guardrails, logging, etc.)Persistent

Transient contextWhat the LLM sees for a single call. You can modify messages, tools, or prompts without changing what’s saved in state.Persistent contextWhat gets saved in state across turns. Life-cycle hooks and tool writes modify this permanently.

​Data sources

Throughout this process, your agent accesses (reads / writes) different sources of data:

Data SourceAlso Known AsScopeExamplesRuntime ContextStatic configurationConversation-scopedUser ID, API keys, database connections, permissions, environment settingsStateShort-term memoryConversation-scopedCurrent messages, uploaded files, authentication status, tool resultsStoreLong-term memoryCross-conversationUser preferences, extracted insights, memories, historical data

​How it works

LangChain middleware is the mechanism under the hood that makes context engineering practical for developers using LangChain.

Middleware allows you to hook into any step in the agent lifecycle and:

- Update context
- Jump to a different step in the agent lifecycle
Throughout this guide, you’ll see frequent use of the middleware API as a means to the context engineering end.

​Model Context

Control what goes into each model call - instructions, available tools, which model to use, and output format. These decisions directly impact reliability and cost.

System PromptBase instructions from the developer to the LLM.MessagesThe full list of messages (conversation history) sent to the LLM.ToolsUtilities the agent has access to to take actions.ModelThe actual model (including configuration) to be called.Response FormatSchema specification for the model’s final response.

All of these types of model context can draw from state (short-term memory), store (long-term memory), or runtime context (static configuration).

​System Prompt

The system prompt sets the LLM’s behavior and capabilities. Different users, contexts, or conversation stages need different instructions. Successful agents draw on memories, preferences, and configuration to provide the right instructions for the current state of the conversation.

State Store Runtime ContextAccess message count or conversation context from state:Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import dynamic_prompt, ModelRequest

@dynamic_prompt
def state_aware_prompt(request: ModelRequest) -> str:
    # request.messages is a shortcut for request.state["messages"]
    message_count = len(request.messages)

    base = "You are a helpful assistant."

    if message_count > 10:
        base += "\nThis is a long conversation - be extra concise."

    return base

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[state_aware_prompt]
)
Access user preferences from long-term memory:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

@dynamic_prompt
def store_aware_prompt(request: ModelRequest) -> str:
    user_id = request.runtime.context.user_id

    # Read from Store: get user preferences
    store = request.runtime.store
    user_prefs = store.get(("preferences",), user_id)

    base = "You are a helpful assistant."

    if user_prefs:
        style = user_prefs.value.get("communication_style", "balanced")
        base += f"\nUser prefers {style} responses."

    return base

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[store_aware_prompt],
    context_schema=Context,
    store=InMemoryStore()
)
Access user ID or configuration from Runtime Context:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

@dataclass
class Context:
    user_role: str
    deployment_env: str

@dynamic_prompt
def context_aware_prompt(request: ModelRequest) -> str:
    # Read from Runtime Context: user role and environment
    user_role = request.runtime.context.user_role
    env = request.runtime.context.deployment_env

    base = "You are a helpful assistant."

    if user_role == "admin":
        base += "\nYou have admin access. You can perform all operations."
    elif user_role == "viewer":
        base += "\nYou have read-only access. Guide users to read operations only."

    if env == "production":
        base += "\nBe extra careful with any data modifications."

    return base

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[context_aware_prompt],
    context_schema=Context
)

​Messages

Messages make up the prompt that is sent to the LLM.
It’s critical to manage the content of messages to ensure that the LLM has the right information to respond well.

State Store Runtime ContextInject uploaded file context from State when relevant to current query:Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@wrap_model_call
def inject_file_context(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Inject context about files user has uploaded this session."""
    # Read from State: get uploaded files metadata
    uploaded_files = request.state.get("uploaded_files", [])

    if uploaded_files:
        # Build context about available files
        file_descriptions = []
        for file in uploaded_files:
            file_descriptions.append(
                f"- {file['name']} ({file['type']}): {file['summary']}"
            )

        file_context = f"""Files you have access to in this conversation:
{chr(10).join(file_descriptions)}

Reference these files when answering questions."""

        # Inject file context before recent messages
        messages = [
            *request.messages,
            {"role": "user", "content": file_context},
        ]
        request = request.override(messages=messages)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[inject_file_context]
)
Inject user’s email writing style from Store to guide drafting:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

@wrap_model_call
def inject_writing_style(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Inject user's email writing style from Store."""
    user_id = request.runtime.context.user_id

    # Read from Store: get user's writing style examples
    store = request.runtime.store
    writing_style = store.get(("writing_style",), user_id)

    if writing_style:
        style = writing_style.value
        # Build style guide from stored examples
        style_context = f"""Your writing style:
- Tone: {style.get('tone', 'professional')}
- Typical greeting: "{style.get('greeting', 'Hi')}"
- Typical sign-off: "{style.get('sign_off', 'Best')}"
- Example email you've written:
{style.get('example_email', '')}"""

        # Append at end - models pay more attention to final messages
        messages = [
            *request.messages,
            {"role": "user", "content": style_context}
        ]
        request = request.override(messages=messages)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[inject_writing_style],
    context_schema=Context,
    store=InMemoryStore()
)
Inject compliance rules from Runtime Context based on user’s jurisdiction:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@dataclass
class Context:
    user_jurisdiction: str
    industry: str
    compliance_frameworks: list[str]

@wrap_model_call
def inject_compliance_rules(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Inject compliance constraints from Runtime Context."""
    # Read from Runtime Context: get compliance requirements
    jurisdiction = request.runtime.context.user_jurisdiction
    industry = request.runtime.context.industry
    frameworks = request.runtime.context.compliance_frameworks

    # Build compliance constraints
    rules = []
    if "GDPR" in frameworks:
        rules.append("- Must obtain explicit consent before processing personal data")
        rules.append("- Users have right to data deletion")
    if "HIPAA" in frameworks:
        rules.append("- Cannot share patient health information without authorization")
        rules.append("- Must use secure, encrypted communication")
    if industry == "finance":
        rules.append("- Cannot provide financial advice without proper disclaimers")

    if rules:
        compliance_context = f"""Compliance requirements for {jurisdiction}:
{chr(10).join(rules)}"""

        # Append at end - models pay more attention to final messages
        messages = [
            *request.messages,
            {"role": "user", "content": compliance_context}
        ]
        request = request.override(messages=messages)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[inject_compliance_rules],
    context_schema=Context
)

Transient vs Persistent Message Updates:The examples above use wrap_model_call to make transient updates - modifying what messages are sent to the model for a single call without changing what’s saved in state.For persistent updates that modify state (like the summarization example in Life-cycle Context), use life-cycle hooks like before_model or after_model to permanently update the conversation history. See the middleware documentation for more details.

​Tools

Tools let the model interact with databases, APIs, and external systems. How you define and select tools directly impacts whether the model can complete tasks effectively.

​Defining tools

Each tool needs a clear name, description, argument names, and argument descriptions. These aren’t just metadata—they guide the model’s reasoning about when and how to use the tool.

Copyfrom langchain.tools import tool

@tool(parse_docstring=True)
def search_orders(
    user_id: str,
    status: str,
    limit: int = 10
) -> str:
    """Search for user orders by status.

    Use this when the user asks about order history or wants to check
    order status. Always filter by the provided status.

    Args:
        user_id: Unique identifier for the user
        status: Order status: 'pending', 'shipped', or 'delivered'
        limit: Maximum number of results to return
    """
    # Implementation here
    pass

​Selecting tools

Not every tool is appropriate for every situation. Too many tools may overwhelm the model (overload context) and increase errors; too few limit capabilities. Dynamic tool selection adapts the available toolset based on authentication state, user permissions, feature flags, or conversation stage.

State Store Runtime ContextEnable advanced tools only after certain conversation milestones:Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@wrap_model_call
def state_based_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Filter tools based on conversation State."""
    # Read from State: check if user has authenticated
    state = request.state
    is_authenticated = state.get("authenticated", False)
    message_count = len(state["messages"])

    # Only enable sensitive tools after authentication
    if not is_authenticated:
        tools = [t for t in request.tools if t.name.startswith("public_")]
        request = request.override(tools=tools)
    elif message_count < 5:
        # Limit tools early in conversation
        tools = [t for t in request.tools if t.name != "advanced_search"]
        request = request.override(tools=tools)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[public_search, private_search, advanced_search],
    middleware=[state_based_tools]
)
Filter tools based on user preferences or feature flags in Store:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

@wrap_model_call
def store_based_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Filter tools based on Store preferences."""
    user_id = request.runtime.context.user_id

    # Read from Store: get user's enabled features
    store = request.runtime.store
    feature_flags = store.get(("features",), user_id)

    if feature_flags:
        enabled_features = feature_flags.value.get("enabled_tools", [])
        # Only include tools that are enabled for this user
        tools = [t for t in request.tools if t.name in enabled_features]
        request = request.override(tools=tools)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[search_tool, analysis_tool, export_tool],
    middleware=[store_based_tools],
    context_schema=Context,
    store=InMemoryStore()
)
Filter tools based on user permissions from Runtime Context:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@dataclass
class Context:
    user_role: str

@wrap_model_call
def context_based_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Filter tools based on Runtime Context permissions."""
    # Read from Runtime Context: get user role
    user_role = request.runtime.context.user_role

    if user_role == "admin":
        # Admins get all tools
        pass
    elif user_role == "editor":
        # Editors can't delete
        tools = [t for t in request.tools if t.name != "delete_data"]
        request = request.override(tools=tools)
    else:
        # Viewers get read-only tools
        tools = [t for t in request.tools if t.name.startswith("read_")]
        request = request.override(tools=tools)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[read_data, write_data, delete_data],
    middleware=[context_based_tools],
    context_schema=Context
)

See Dynamically selecting tools for more examples.

​Model

Different models have different strengths, costs, and context windows. Select the right model for the task at hand, which
might change during an agent run.

State Store Runtime ContextUse different models based on conversation length from State:Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.chat_models import init_chat_model
from typing import Callable

# Initialize models once outside the middleware
large_model = init_chat_model("claude-sonnet-4-5-20250929")
standard_model = init_chat_model("gpt-4o")
efficient_model = init_chat_model("gpt-4o-mini")

@wrap_model_call
def state_based_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select model based on State conversation length."""
    # request.messages is a shortcut for request.state["messages"]
    message_count = len(request.messages)

    if message_count > 20:
        # Long conversation - use model with larger context window
        model = large_model
    elif message_count > 10:
        # Medium conversation
        model = standard_model
    else:
        # Short conversation - use efficient model
        model = efficient_model

    request = request.override(model=model)

    return handler(request)

agent = create_agent(
    model="gpt-4o-mini",
    tools=[...],
    middleware=[state_based_model]
)
Use user’s preferred model from Store:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.chat_models import init_chat_model
from typing import Callable
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

# Initialize available models once
MODEL_MAP = {
    "gpt-4o": init_chat_model("gpt-4o"),
    "gpt-4o-mini": init_chat_model("gpt-4o-mini"),
    "claude-sonnet": init_chat_model("claude-sonnet-4-5-20250929"),
}

@wrap_model_call
def store_based_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select model based on Store preferences."""
    user_id = request.runtime.context.user_id

    # Read from Store: get user's preferred model
    store = request.runtime.store
    user_prefs = store.get(("preferences",), user_id)

    if user_prefs:
        preferred_model = user_prefs.value.get("preferred_model")
        if preferred_model and preferred_model in MODEL_MAP:
            request = request.override(model=MODEL_MAP[preferred_model])

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[store_based_model],
    context_schema=Context,
    store=InMemoryStore()
)
Select model based on cost limits or environment from Runtime Context:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.chat_models import init_chat_model
from typing import Callable

@dataclass
class Context:
    cost_tier: str
    environment: str

# Initialize models once outside the middleware
premium_model = init_chat_model("claude-sonnet-4-5-20250929")
standard_model = init_chat_model("gpt-4o")
budget_model = init_chat_model("gpt-4o-mini")

@wrap_model_call
def context_based_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select model based on Runtime Context."""
    # Read from Runtime Context: cost tier and environment
    cost_tier = request.runtime.context.cost_tier
    environment = request.runtime.context.environment

    if environment == "production" and cost_tier == "premium":
        # Production premium users get best model
        model = premium_model
    elif cost_tier == "budget":
        # Budget tier gets efficient model
        model = budget_model
    else:
        # Standard tier
        model = standard_model

    request = request.override(model=model)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[context_based_model],
    context_schema=Context
)

See Dynamic model for more examples.

​Response Format

Structured output transforms unstructured text into validated, structured data. When extracting specific fields or returning data for downstream systems, free-form text isn’t sufficient.

How it works: When you provide a schema as the response format, the model’s final response is guaranteed to conform to that schema. The agent runs the model / tool calling loop until the model is done calling tools, then the final response is coerced into the provided format.

​Defining formats

Schema definitions guide the model. Field names, types, and descriptions specify exactly what format the output should adhere to.

Copyfrom pydantic import BaseModel, Field

class CustomerSupportTicket(BaseModel):
    """Structured ticket information extracted from customer message."""

    category: str = Field(
        description="Issue category: 'billing', 'technical', 'account', or 'product'"
    )
    priority: str = Field(
        description="Urgency level: 'low', 'medium', 'high', or 'critical'"
    )
    summary: str = Field(
        description="One-sentence summary of the customer's issue"
    )
    customer_sentiment: str = Field(
        description="Customer's emotional tone: 'frustrated', 'neutral', or 'satisfied'"
    )

​Selecting formats

Dynamic response format selection adapts schemas based on user preferences, conversation stage, or role—returning simple formats early and detailed formats as complexity increases.

State Store Runtime ContextConfigure structured output based on conversation state:Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from pydantic import BaseModel, Field
from typing import Callable

class SimpleResponse(BaseModel):
    """Simple response for early conversation."""
    answer: str = Field(description="A brief answer")

class DetailedResponse(BaseModel):
    """Detailed response for established conversation."""
    answer: str = Field(description="A detailed answer")
    reasoning: str = Field(description="Explanation of reasoning")
    confidence: float = Field(description="Confidence score 0-1")

@wrap_model_call
def state_based_output(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select output format based on State."""
    # request.messages is a shortcut for request.state["messages"]
    message_count = len(request.messages)

    if message_count < 3:
        # Early conversation - use simple format
        request = request.override(response_format=SimpleResponse)
    else:
        # Established conversation - use detailed format
        request = request.override(response_format=DetailedResponse)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[state_based_output]
)
Configure output format based on user preferences in Store:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from pydantic import BaseModel, Field
from typing import Callable
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

class VerboseResponse(BaseModel):
    """Verbose response with details."""
    answer: str = Field(description="Detailed answer")
    sources: list[str] = Field(description="Sources used")

class ConciseResponse(BaseModel):
    """Concise response."""
    answer: str = Field(description="Brief answer")

@wrap_model_call
def store_based_output(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select output format based on Store preferences."""
    user_id = request.runtime.context.user_id

    # Read from Store: get user's preferred response style
    store = request.runtime.store
    user_prefs = store.get(("preferences",), user_id)

    if user_prefs:
        style = user_prefs.value.get("response_style", "concise")
        if style == "verbose":
            request = request.override(response_format=VerboseResponse)
        else:
            request = request.override(response_format=ConciseResponse)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[store_based_output],
    context_schema=Context,
    store=InMemoryStore()
)
Configure output format based on Runtime Context like user role or environment:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from pydantic import BaseModel, Field
from typing import Callable

@dataclass
class Context:
    user_role: str
    environment: str

class AdminResponse(BaseModel):
    """Response with technical details for admins."""
    answer: str = Field(description="Answer")
    debug_info: dict = Field(description="Debug information")
    system_status: str = Field(description="System status")

class UserResponse(BaseModel):
    """Simple response for regular users."""
    answer: str = Field(description="Answer")

@wrap_model_call
def context_based_output(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select output format based on Runtime Context."""
    # Read from Runtime Context: user role and environment
    user_role = request.runtime.context.user_role
    environment = request.runtime.context.environment

    if user_role == "admin" and environment == "production":
        # Admins in production get detailed output
        request = request.override(response_format=AdminResponse)
    else:
        # Regular users get simple output
        request = request.override(response_format=UserResponse)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[context_based_output],
    context_schema=Context
)

​Tool Context

Tools are special in that they both read and write context.

In the most basic case, when a tool executes, it receives the LLM’s request parameters and returns a tool message back. The tool does its work and produces a result.

Tools can also fetch important information for the model that allows it to perform and complete tasks.

​Reads

Most real-world tools need more than just the LLM’s parameters. They need user IDs for database queries, API keys for external services, or current session state to make decisions. Tools read from state, store, and runtime context to access this information.

State Store Runtime ContextRead from State to check current session information:Copyfrom langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent

@tool
def check_authentication(
    runtime: ToolRuntime
) -> str:
    """Check if user is authenticated."""
    # Read from State: check current auth status
    current_state = runtime.state
    is_authenticated = current_state.get("authenticated", False)

    if is_authenticated:
        return "User is authenticated"
    else:
        return "User is not authenticated"

agent = create_agent(
    model="gpt-4o",
    tools=[check_authentication]
)
Read from Store to access persisted user preferences:Copyfrom dataclasses import dataclass
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

@tool
def get_preference(
    preference_key: str,
    runtime: ToolRuntime[Context]
) -> str:
    """Get user preference from Store."""
    user_id = runtime.context.user_id

    # Read from Store: get existing preferences
    store = runtime.store
    existing_prefs = store.get(("preferences",), user_id)

    if existing_prefs:
        value = existing_prefs.value.get(preference_key)
        return f"{preference_key}: {value}" if value else f"No preference set for {preference_key}"
    else:
        return "No preferences found"

agent = create_agent(
    model="gpt-4o",
    tools=[get_preference],
    context_schema=Context,
    store=InMemoryStore()
)
Read from Runtime Context for configuration like API keys and user IDs:Copyfrom dataclasses import dataclass
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent

@dataclass
class Context:
    user_id: str
    api_key: str
    db_connection: str

@tool
def fetch_user_data(
    query: str,
    runtime: ToolRuntime[Context]
) -> str:
    """Fetch data using Runtime Context configuration."""
    # Read from Runtime Context: get API key and DB connection
    user_id = runtime.context.user_id
    api_key = runtime.context.api_key
    db_connection = runtime.context.db_connection

    # Use configuration to fetch data
    results = perform_database_query(db_connection, query, api_key)

    return f"Found {len(results)} results for user {user_id}"

agent = create_agent(
    model="gpt-4o",
    tools=[fetch_user_data],
    context_schema=Context
)

# Invoke with runtime context
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Get my data"}]},
    context=Context(
        user_id="user_123",
        api_key="sk-...",
        db_connection="postgresql://..."
    )
)

​Writes

Tool results can be used to help an agent complete a given task. Tools can both return results directly to the model
and update the memory of the agent to make important context available to future steps.

State StoreWrite to State to track session-specific information using Command:Copyfrom langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent
from langgraph.types import Command

@tool
def authenticate_user(
    password: str,
    runtime: ToolRuntime
) -> Command:
    """Authenticate user and update State."""
    # Perform authentication (simplified)
    if password == "correct":
        # Write to State: mark as authenticated using Command
        return Command(
            update={"authenticated": True},
        )
    else:
        return Command(update={"authenticated": False})

agent = create_agent(
    model="gpt-4o",
    tools=[authenticate_user]
)
Write to Store to persist data across sessions:Copyfrom dataclasses import dataclass
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

@tool
def save_preference(
    preference_key: str,
    preference_value: str,
    runtime: ToolRuntime[Context]
) -> str:
    """Save user preference to Store."""
    user_id = runtime.context.user_id

    # Read existing preferences
    store = runtime.store
    existing_prefs = store.get(("preferences",), user_id)

    # Merge with new preference
    prefs = existing_prefs.value if existing_prefs else {}
    prefs[preference_key] = preference_value

    # Write to Store: save updated preferences
    store.put(("preferences",), user_id, prefs)

    return f"Saved preference: {preference_key} = {preference_value}"

agent = create_agent(
    model="gpt-4o",
    tools=[save_preference],
    context_schema=Context,
    store=InMemoryStore()
)

See Tools for comprehensive examples of accessing state, store, and runtime context in tools.

​Life-cycle Context

Control what happens between the core agent steps - intercepting data flow to implement cross-cutting concerns like summarization, guardrails, and logging.

As you’ve seen in Model Context and Tool Context, middleware is the mechanism that makes context engineering practical. Middleware allows you to hook into any step in the agent lifecycle and either:

- Update context - Modify state and store to persist changes, update conversation history, or save insights
- Jump in the lifecycle - Move to different steps in the agent cycle based on context (e.g., skip tool execution if a condition is met, repeat model call with modified context)
​Example: Summarization

One of the most common life-cycle patterns is automatically condensing conversation history when it gets too long. Unlike the transient message trimming shown in Model Context, summarization persistently updates state - permanently replacing old messages with a summary that’s saved for all future turns.

LangChain offers built-in middleware for this:

Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[
        SummarizationMiddleware(
            model="gpt-4o-mini",
            trigger={"tokens": 4000},
            keep={"messages": 20},
        ),
    ],
)

When the conversation exceeds the token limit, SummarizationMiddleware automatically:

- Summarizes older messages using a separate LLM call
- Replaces them with a summary message in State (permanently)
- Keeps recent messages intact for context
The summarized conversation history is permanently updated - future turns will see the summary instead of the original messages.

For a complete list of built-in middleware, available hooks, and how to create custom middleware, see the Middleware documentation.

​Best practices

- Start simple - Begin with static prompts and tools, add dynamics only when needed
- Test incrementally - Add one context engineering feature at a time
- Monitor performance - Track model calls, token usage, and latency
- Use built-in middleware - Leverage SummarizationMiddleware, LLMToolSelectorMiddleware, etc.
- Document your context strategy - Make it clear what context is being passed and why
- Understand transient vs persistent: Model context changes are transient (per-call), while life-cycle context changes persist to state
​Related resources

- Context conceptual overview - Understand context types and when to use them
- Middleware - Complete middleware guide
- Tools - Tool creation and context access
- Memory - Short-term and long-term memory patterns
- Agents - Core agent concepts
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```

#### Transient context

What the LLM sees for a single call. You can modify messages, tools, or prompts without changing what’s saved in state.

#### Persistent context

What gets saved in state across turns. Life-cycle hooks and tool writes modify this permanently.

##### ​Data sources

Throughout this process, your agent accesses (reads / writes) different sources of data:

Data SourceAlso Known AsScopeExamplesRuntime ContextStatic configurationConversation-scopedUser ID, API keys, database connections, permissions, environment settingsStateShort-term memoryConversation-scopedCurrent messages, uploaded files, authentication status, tool resultsStoreLong-term memoryCross-conversationUser preferences, extracted insights, memories, historical data

##### ​How it works

LangChain middleware is the mechanism under the hood that makes context engineering practical for developers using LangChain.

Middleware allows you to hook into any step in the agent lifecycle and:

- Update context
- Jump to a different step in the agent lifecycle
Throughout this guide, you’ll see frequent use of the middleware API as a means to the context engineering end.

#### ​Model Context

Control what goes into each model call - instructions, available tools, which model to use, and output format. These decisions directly impact reliability and cost.

System PromptBase instructions from the developer to the LLM.MessagesThe full list of messages (conversation history) sent to the LLM.ToolsUtilities the agent has access to to take actions.ModelThe actual model (including configuration) to be called.Response FormatSchema specification for the model’s final response.

All of these types of model context can draw from state (short-term memory), store (long-term memory), or runtime context (static configuration).

​System Prompt

The system prompt sets the LLM’s behavior and capabilities. Different users, contexts, or conversation stages need different instructions. Successful agents draw on memories, preferences, and configuration to provide the right instructions for the current state of the conversation.

State Store Runtime ContextAccess message count or conversation context from state:Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import dynamic_prompt, ModelRequest

@dynamic_prompt
def state_aware_prompt(request: ModelRequest) -> str:
    # request.messages is a shortcut for request.state["messages"]
    message_count = len(request.messages)

    base = "You are a helpful assistant."

    if message_count > 10:
        base += "\nThis is a long conversation - be extra concise."

    return base

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[state_aware_prompt]
)
Access user preferences from long-term memory:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

@dynamic_prompt
def store_aware_prompt(request: ModelRequest) -> str:
    user_id = request.runtime.context.user_id

    # Read from Store: get user preferences
    store = request.runtime.store
    user_prefs = store.get(("preferences",), user_id)

    base = "You are a helpful assistant."

    if user_prefs:
        style = user_prefs.value.get("communication_style", "balanced")
        base += f"\nUser prefers {style} responses."

    return base

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[store_aware_prompt],
    context_schema=Context,
    store=InMemoryStore()
)
Access user ID or configuration from Runtime Context:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

@dataclass
class Context:
    user_role: str
    deployment_env: str

@dynamic_prompt
def context_aware_prompt(request: ModelRequest) -> str:
    # Read from Runtime Context: user role and environment
    user_role = request.runtime.context.user_role
    env = request.runtime.context.deployment_env

    base = "You are a helpful assistant."

    if user_role == "admin":
        base += "\nYou have admin access. You can perform all operations."
    elif user_role == "viewer":
        base += "\nYou have read-only access. Guide users to read operations only."

    if env == "production":
        base += "\nBe extra careful with any data modifications."

    return base

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[context_aware_prompt],
    context_schema=Context
)

​Messages

Messages make up the prompt that is sent to the LLM.
It’s critical to manage the content of messages to ensure that the LLM has the right information to respond well.

State Store Runtime ContextInject uploaded file context from State when relevant to current query:Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@wrap_model_call
def inject_file_context(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Inject context about files user has uploaded this session."""
    # Read from State: get uploaded files metadata
    uploaded_files = request.state.get("uploaded_files", [])

    if uploaded_files:
        # Build context about available files
        file_descriptions = []
        for file in uploaded_files:
            file_descriptions.append(
                f"- {file['name']} ({file['type']}): {file['summary']}"
            )

        file_context = f"""Files you have access to in this conversation:
{chr(10).join(file_descriptions)}

Reference these files when answering questions."""

        # Inject file context before recent messages
        messages = [
            *request.messages,
            {"role": "user", "content": file_context},
        ]
        request = request.override(messages=messages)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[inject_file_context]
)
Inject user’s email writing style from Store to guide drafting:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

@wrap_model_call
def inject_writing_style(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Inject user's email writing style from Store."""
    user_id = request.runtime.context.user_id

    # Read from Store: get user's writing style examples
    store = request.runtime.store
    writing_style = store.get(("writing_style",), user_id)

    if writing_style:
        style = writing_style.value
        # Build style guide from stored examples
        style_context = f"""Your writing style:
- Tone: {style.get('tone', 'professional')}
- Typical greeting: "{style.get('greeting', 'Hi')}"
- Typical sign-off: "{style.get('sign_off', 'Best')}"
- Example email you've written:
{style.get('example_email', '')}"""

        # Append at end - models pay more attention to final messages
        messages = [
            *request.messages,
            {"role": "user", "content": style_context}
        ]
        request = request.override(messages=messages)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[inject_writing_style],
    context_schema=Context,
    store=InMemoryStore()
)
Inject compliance rules from Runtime Context based on user’s jurisdiction:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@dataclass
class Context:
    user_jurisdiction: str
    industry: str
    compliance_frameworks: list[str]

@wrap_model_call
def inject_compliance_rules(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Inject compliance constraints from Runtime Context."""
    # Read from Runtime Context: get compliance requirements
    jurisdiction = request.runtime.context.user_jurisdiction
    industry = request.runtime.context.industry
    frameworks = request.runtime.context.compliance_frameworks

    # Build compliance constraints
    rules = []
    if "GDPR" in frameworks:
        rules.append("- Must obtain explicit consent before processing personal data")
        rules.append("- Users have right to data deletion")
    if "HIPAA" in frameworks:
        rules.append("- Cannot share patient health information without authorization")
        rules.append("- Must use secure, encrypted communication")
    if industry == "finance":
        rules.append("- Cannot provide financial advice without proper disclaimers")

    if rules:
        compliance_context = f"""Compliance requirements for {jurisdiction}:
{chr(10).join(rules)}"""

        # Append at end - models pay more attention to final messages
        messages = [
            *request.messages,
            {"role": "user", "content": compliance_context}
        ]
        request = request.override(messages=messages)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[inject_compliance_rules],
    context_schema=Context
)

Transient vs Persistent Message Updates:The examples above use wrap_model_call to make transient updates - modifying what messages are sent to the model for a single call without changing what’s saved in state.For persistent updates that modify state (like the summarization example in Life-cycle Context), use life-cycle hooks like before_model or after_model to permanently update the conversation history. See the middleware documentation for more details.

​Tools

Tools let the model interact with databases, APIs, and external systems. How you define and select tools directly impacts whether the model can complete tasks effectively.

​Defining tools

Each tool needs a clear name, description, argument names, and argument descriptions. These aren’t just metadata—they guide the model’s reasoning about when and how to use the tool.

Copyfrom langchain.tools import tool

@tool(parse_docstring=True)
def search_orders(
    user_id: str,
    status: str,
    limit: int = 10
) -> str:
    """Search for user orders by status.

    Use this when the user asks about order history or wants to check
    order status. Always filter by the provided status.

    Args:
        user_id: Unique identifier for the user
        status: Order status: 'pending', 'shipped', or 'delivered'
        limit: Maximum number of results to return
    """
    # Implementation here
    pass

​Selecting tools

Not every tool is appropriate for every situation. Too many tools may overwhelm the model (overload context) and increase errors; too few limit capabilities. Dynamic tool selection adapts the available toolset based on authentication state, user permissions, feature flags, or conversation stage.

State Store Runtime ContextEnable advanced tools only after certain conversation milestones:Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@wrap_model_call
def state_based_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Filter tools based on conversation State."""
    # Read from State: check if user has authenticated
    state = request.state
    is_authenticated = state.get("authenticated", False)
    message_count = len(state["messages"])

    # Only enable sensitive tools after authentication
    if not is_authenticated:
        tools = [t for t in request.tools if t.name.startswith("public_")]
        request = request.override(tools=tools)
    elif message_count < 5:
        # Limit tools early in conversation
        tools = [t for t in request.tools if t.name != "advanced_search"]
        request = request.override(tools=tools)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[public_search, private_search, advanced_search],
    middleware=[state_based_tools]
)
Filter tools based on user preferences or feature flags in Store:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

@wrap_model_call
def store_based_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Filter tools based on Store preferences."""
    user_id = request.runtime.context.user_id

    # Read from Store: get user's enabled features
    store = request.runtime.store
    feature_flags = store.get(("features",), user_id)

    if feature_flags:
        enabled_features = feature_flags.value.get("enabled_tools", [])
        # Only include tools that are enabled for this user
        tools = [t for t in request.tools if t.name in enabled_features]
        request = request.override(tools=tools)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[search_tool, analysis_tool, export_tool],
    middleware=[store_based_tools],
    context_schema=Context,
    store=InMemoryStore()
)
Filter tools based on user permissions from Runtime Context:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@dataclass
class Context:
    user_role: str

@wrap_model_call
def context_based_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Filter tools based on Runtime Context permissions."""
    # Read from Runtime Context: get user role
    user_role = request.runtime.context.user_role

    if user_role == "admin":
        # Admins get all tools
        pass
    elif user_role == "editor":
        # Editors can't delete
        tools = [t for t in request.tools if t.name != "delete_data"]
        request = request.override(tools=tools)
    else:
        # Viewers get read-only tools
        tools = [t for t in request.tools if t.name.startswith("read_")]
        request = request.override(tools=tools)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[read_data, write_data, delete_data],
    middleware=[context_based_tools],
    context_schema=Context
)

See Dynamically selecting tools for more examples.

​Model

Different models have different strengths, costs, and context windows. Select the right model for the task at hand, which
might change during an agent run.

State Store Runtime ContextUse different models based on conversation length from State:Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.chat_models import init_chat_model
from typing import Callable

# Initialize models once outside the middleware
large_model = init_chat_model("claude-sonnet-4-5-20250929")
standard_model = init_chat_model("gpt-4o")
efficient_model = init_chat_model("gpt-4o-mini")

@wrap_model_call
def state_based_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select model based on State conversation length."""
    # request.messages is a shortcut for request.state["messages"]
    message_count = len(request.messages)

    if message_count > 20:
        # Long conversation - use model with larger context window
        model = large_model
    elif message_count > 10:
        # Medium conversation
        model = standard_model
    else:
        # Short conversation - use efficient model
        model = efficient_model

    request = request.override(model=model)

    return handler(request)

agent = create_agent(
    model="gpt-4o-mini",
    tools=[...],
    middleware=[state_based_model]
)
Use user’s preferred model from Store:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.chat_models import init_chat_model
from typing import Callable
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

# Initialize available models once
MODEL_MAP = {
    "gpt-4o": init_chat_model("gpt-4o"),
    "gpt-4o-mini": init_chat_model("gpt-4o-mini"),
    "claude-sonnet": init_chat_model("claude-sonnet-4-5-20250929"),
}

@wrap_model_call
def store_based_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select model based on Store preferences."""
    user_id = request.runtime.context.user_id

    # Read from Store: get user's preferred model
    store = request.runtime.store
    user_prefs = store.get(("preferences",), user_id)

    if user_prefs:
        preferred_model = user_prefs.value.get("preferred_model")
        if preferred_model and preferred_model in MODEL_MAP:
            request = request.override(model=MODEL_MAP[preferred_model])

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[store_based_model],
    context_schema=Context,
    store=InMemoryStore()
)
Select model based on cost limits or environment from Runtime Context:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.chat_models import init_chat_model
from typing import Callable

@dataclass
class Context:
    cost_tier: str
    environment: str

# Initialize models once outside the middleware
premium_model = init_chat_model("claude-sonnet-4-5-20250929")
standard_model = init_chat_model("gpt-4o")
budget_model = init_chat_model("gpt-4o-mini")

@wrap_model_call
def context_based_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select model based on Runtime Context."""
    # Read from Runtime Context: cost tier and environment
    cost_tier = request.runtime.context.cost_tier
    environment = request.runtime.context.environment

    if environment == "production" and cost_tier == "premium":
        # Production premium users get best model
        model = premium_model
    elif cost_tier == "budget":
        # Budget tier gets efficient model
        model = budget_model
    else:
        # Standard tier
        model = standard_model

    request = request.override(model=model)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[context_based_model],
    context_schema=Context
)

See Dynamic model for more examples.

​Response Format

Structured output transforms unstructured text into validated, structured data. When extracting specific fields or returning data for downstream systems, free-form text isn’t sufficient.

How it works: When you provide a schema as the response format, the model’s final response is guaranteed to conform to that schema. The agent runs the model / tool calling loop until the model is done calling tools, then the final response is coerced into the provided format.

​Defining formats

Schema definitions guide the model. Field names, types, and descriptions specify exactly what format the output should adhere to.

Copyfrom pydantic import BaseModel, Field

class CustomerSupportTicket(BaseModel):
    """Structured ticket information extracted from customer message."""

    category: str = Field(
        description="Issue category: 'billing', 'technical', 'account', or 'product'"
    )
    priority: str = Field(
        description="Urgency level: 'low', 'medium', 'high', or 'critical'"
    )
    summary: str = Field(
        description="One-sentence summary of the customer's issue"
    )
    customer_sentiment: str = Field(
        description="Customer's emotional tone: 'frustrated', 'neutral', or 'satisfied'"
    )

​Selecting formats

Dynamic response format selection adapts schemas based on user preferences, conversation stage, or role—returning simple formats early and detailed formats as complexity increases.

State Store Runtime ContextConfigure structured output based on conversation state:Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from pydantic import BaseModel, Field
from typing import Callable

class SimpleResponse(BaseModel):
    """Simple response for early conversation."""
    answer: str = Field(description="A brief answer")

class DetailedResponse(BaseModel):
    """Detailed response for established conversation."""
    answer: str = Field(description="A detailed answer")
    reasoning: str = Field(description="Explanation of reasoning")
    confidence: float = Field(description="Confidence score 0-1")

@wrap_model_call
def state_based_output(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select output format based on State."""
    # request.messages is a shortcut for request.state["messages"]
    message_count = len(request.messages)

    if message_count < 3:
        # Early conversation - use simple format
        request = request.override(response_format=SimpleResponse)
    else:
        # Established conversation - use detailed format
        request = request.override(response_format=DetailedResponse)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[state_based_output]
)
Configure output format based on user preferences in Store:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from pydantic import BaseModel, Field
from typing import Callable
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

class VerboseResponse(BaseModel):
    """Verbose response with details."""
    answer: str = Field(description="Detailed answer")
    sources: list[str] = Field(description="Sources used")

class ConciseResponse(BaseModel):
    """Concise response."""
    answer: str = Field(description="Brief answer")

@wrap_model_call
def store_based_output(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select output format based on Store preferences."""
    user_id = request.runtime.context.user_id

    # Read from Store: get user's preferred response style
    store = request.runtime.store
    user_prefs = store.get(("preferences",), user_id)

    if user_prefs:
        style = user_prefs.value.get("response_style", "concise")
        if style == "verbose":
            request = request.override(response_format=VerboseResponse)
        else:
            request = request.override(response_format=ConciseResponse)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[store_based_output],
    context_schema=Context,
    store=InMemoryStore()
)
Configure output format based on Runtime Context like user role or environment:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from pydantic import BaseModel, Field
from typing import Callable

@dataclass
class Context:
    user_role: str
    environment: str

class AdminResponse(BaseModel):
    """Response with technical details for admins."""
    answer: str = Field(description="Answer")
    debug_info: dict = Field(description="Debug information")
    system_status: str = Field(description="System status")

class UserResponse(BaseModel):
    """Simple response for regular users."""
    answer: str = Field(description="Answer")

@wrap_model_call
def context_based_output(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select output format based on Runtime Context."""
    # Read from Runtime Context: user role and environment
    user_role = request.runtime.context.user_role
    environment = request.runtime.context.environment

    if user_role == "admin" and environment == "production":
        # Admins in production get detailed output
        request = request.override(response_format=AdminResponse)
    else:
        # Regular users get simple output
        request = request.override(response_format=UserResponse)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[context_based_output],
    context_schema=Context
)

​Tool Context

Tools are special in that they both read and write context.

In the most basic case, when a tool executes, it receives the LLM’s request parameters and returns a tool message back. The tool does its work and produces a result.

Tools can also fetch important information for the model that allows it to perform and complete tasks.

​Reads

Most real-world tools need more than just the LLM’s parameters. They need user IDs for database queries, API keys for external services, or current session state to make decisions. Tools read from state, store, and runtime context to access this information.

State Store Runtime ContextRead from State to check current session information:Copyfrom langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent

@tool
def check_authentication(
    runtime: ToolRuntime
) -> str:
    """Check if user is authenticated."""
    # Read from State: check current auth status
    current_state = runtime.state
    is_authenticated = current_state.get("authenticated", False)

    if is_authenticated:
        return "User is authenticated"
    else:
        return "User is not authenticated"

agent = create_agent(
    model="gpt-4o",
    tools=[check_authentication]
)
Read from Store to access persisted user preferences:Copyfrom dataclasses import dataclass
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

@tool
def get_preference(
    preference_key: str,
    runtime: ToolRuntime[Context]
) -> str:
    """Get user preference from Store."""
    user_id = runtime.context.user_id

    # Read from Store: get existing preferences
    store = runtime.store
    existing_prefs = store.get(("preferences",), user_id)

    if existing_prefs:
        value = existing_prefs.value.get(preference_key)
        return f"{preference_key}: {value}" if value else f"No preference set for {preference_key}"
    else:
        return "No preferences found"

agent = create_agent(
    model="gpt-4o",
    tools=[get_preference],
    context_schema=Context,
    store=InMemoryStore()
)
Read from Runtime Context for configuration like API keys and user IDs:Copyfrom dataclasses import dataclass
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent

@dataclass
class Context:
    user_id: str
    api_key: str
    db_connection: str

@tool
def fetch_user_data(
    query: str,
    runtime: ToolRuntime[Context]
) -> str:
    """Fetch data using Runtime Context configuration."""
    # Read from Runtime Context: get API key and DB connection
    user_id = runtime.context.user_id
    api_key = runtime.context.api_key
    db_connection = runtime.context.db_connection

    # Use configuration to fetch data
    results = perform_database_query(db_connection, query, api_key)

    return f"Found {len(results)} results for user {user_id}"

agent = create_agent(
    model="gpt-4o",
    tools=[fetch_user_data],
    context_schema=Context
)

# Invoke with runtime context
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Get my data"}]},
    context=Context(
        user_id="user_123",
        api_key="sk-...",
        db_connection="postgresql://..."
    )
)

​Writes

Tool results can be used to help an agent complete a given task. Tools can both return results directly to the model
and update the memory of the agent to make important context available to future steps.

State StoreWrite to State to track session-specific information using Command:Copyfrom langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent
from langgraph.types import Command

@tool
def authenticate_user(
    password: str,
    runtime: ToolRuntime
) -> Command:
    """Authenticate user and update State."""
    # Perform authentication (simplified)
    if password == "correct":
        # Write to State: mark as authenticated using Command
        return Command(
            update={"authenticated": True},
        )
    else:
        return Command(update={"authenticated": False})

agent = create_agent(
    model="gpt-4o",
    tools=[authenticate_user]
)
Write to Store to persist data across sessions:Copyfrom dataclasses import dataclass
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

@tool
def save_preference(
    preference_key: str,
    preference_value: str,
    runtime: ToolRuntime[Context]
) -> str:
    """Save user preference to Store."""
    user_id = runtime.context.user_id

    # Read existing preferences
    store = runtime.store
    existing_prefs = store.get(("preferences",), user_id)

    # Merge with new preference
    prefs = existing_prefs.value if existing_prefs else {}
    prefs[preference_key] = preference_value

    # Write to Store: save updated preferences
    store.put(("preferences",), user_id, prefs)

    return f"Saved preference: {preference_key} = {preference_value}"

agent = create_agent(
    model="gpt-4o",
    tools=[save_preference],
    context_schema=Context,
    store=InMemoryStore()
)

See Tools for comprehensive examples of accessing state, store, and runtime context in tools.

​Life-cycle Context

Control what happens between the core agent steps - intercepting data flow to implement cross-cutting concerns like summarization, guardrails, and logging.

As you’ve seen in Model Context and Tool Context, middleware is the mechanism that makes context engineering practical. Middleware allows you to hook into any step in the agent lifecycle and either:

- Update context - Modify state and store to persist changes, update conversation history, or save insights
- Jump in the lifecycle - Move to different steps in the agent cycle based on context (e.g., skip tool execution if a condition is met, repeat model call with modified context)
​Example: Summarization

One of the most common life-cycle patterns is automatically condensing conversation history when it gets too long. Unlike the transient message trimming shown in Model Context, summarization persistently updates state - permanently replacing old messages with a summary that’s saved for all future turns.

LangChain offers built-in middleware for this:

Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[
        SummarizationMiddleware(
            model="gpt-4o-mini",
            trigger={"tokens": 4000},
            keep={"messages": 20},
        ),
    ],
)

When the conversation exceeds the token limit, SummarizationMiddleware automatically:

- Summarizes older messages using a separate LLM call
- Replaces them with a summary message in State (permanently)
- Keeps recent messages intact for context
The summarized conversation history is permanently updated - future turns will see the summary instead of the original messages.

For a complete list of built-in middleware, available hooks, and how to create custom middleware, see the Middleware documentation.

​Best practices

- Start simple - Begin with static prompts and tools, add dynamics only when needed
- Test incrementally - Add one context engineering feature at a time
- Monitor performance - Track model calls, token usage, and latency
- Use built-in middleware - Leverage SummarizationMiddleware, LLMToolSelectorMiddleware, etc.
- Document your context strategy - Make it clear what context is being passed and why
- Understand transient vs persistent: Model context changes are transient (per-call), while life-cycle context changes persist to state
​Related resources

- Context conceptual overview - Understand context types and when to use them
- Middleware - Complete middleware guide
- Tools - Tool creation and context access
- Memory - Short-term and long-term memory patterns
- Agents - Core agent concepts
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```

#### System Prompt

Base instructions from the developer to the LLM.

#### Messages

The full list of messages (conversation history) sent to the LLM.

#### Tools

Utilities the agent has access to to take actions.

#### Model

The actual model (including configuration) to be called.

#### Response Format

Schema specification for the model’s final response.

##### ​System Prompt

The system prompt sets the LLM’s behavior and capabilities. Different users, contexts, or conversation stages need different instructions. Successful agents draw on memories, preferences, and configuration to provide the right instructions for the current state of the conversation.

State Store Runtime ContextAccess message count or conversation context from state:Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import dynamic_prompt, ModelRequest

@dynamic_prompt
def state_aware_prompt(request: ModelRequest) -> str:
    # request.messages is a shortcut for request.state["messages"]
    message_count = len(request.messages)

    base = "You are a helpful assistant."

    if message_count > 10:
        base += "\nThis is a long conversation - be extra concise."

    return base

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[state_aware_prompt]
)
Access user preferences from long-term memory:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

@dynamic_prompt
def store_aware_prompt(request: ModelRequest) -> str:
    user_id = request.runtime.context.user_id

    # Read from Store: get user preferences
    store = request.runtime.store
    user_prefs = store.get(("preferences",), user_id)

    base = "You are a helpful assistant."

    if user_prefs:
        style = user_prefs.value.get("communication_style", "balanced")
        base += f"\nUser prefers {style} responses."

    return base

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[store_aware_prompt],
    context_schema=Context,
    store=InMemoryStore()
)
Access user ID or configuration from Runtime Context:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

@dataclass
class Context:
    user_role: str
    deployment_env: str

@dynamic_prompt
def context_aware_prompt(request: ModelRequest) -> str:
    # Read from Runtime Context: user role and environment
    user_role = request.runtime.context.user_role
    env = request.runtime.context.deployment_env

    base = "You are a helpful assistant."

    if user_role == "admin":
        base += "\nYou have admin access. You can perform all operations."
    elif user_role == "viewer":
        base += "\nYou have read-only access. Guide users to read operations only."

    if env == "production":
        base += "\nBe extra careful with any data modifications."

    return base

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[context_aware_prompt],
    context_schema=Context
)
```

##### ​Messages

Messages make up the prompt that is sent to the LLM.
It’s critical to manage the content of messages to ensure that the LLM has the right information to respond well.

State Store Runtime ContextInject uploaded file context from State when relevant to current query:Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@wrap_model_call
def inject_file_context(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Inject context about files user has uploaded this session."""
    # Read from State: get uploaded files metadata
    uploaded_files = request.state.get("uploaded_files", [])

    if uploaded_files:
        # Build context about available files
        file_descriptions = []
        for file in uploaded_files:
            file_descriptions.append(
                f"- {file['name']} ({file['type']}): {file['summary']}"
            )

        file_context = f"""Files you have access to in this conversation:
{chr(10).join(file_descriptions)}

Reference these files when answering questions."""

        # Inject file context before recent messages
        messages = [
            *request.messages,
            {"role": "user", "content": file_context},
        ]
        request = request.override(messages=messages)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[inject_file_context]
)
Inject user’s email writing style from Store to guide drafting:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

@wrap_model_call
def inject_writing_style(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Inject user's email writing style from Store."""
    user_id = request.runtime.context.user_id

    # Read from Store: get user's writing style examples
    store = request.runtime.store
    writing_style = store.get(("writing_style",), user_id)

    if writing_style:
        style = writing_style.value
        # Build style guide from stored examples
        style_context = f"""Your writing style:
- Tone: {style.get('tone', 'professional')}
- Typical greeting: "{style.get('greeting', 'Hi')}"
- Typical sign-off: "{style.get('sign_off', 'Best')}"
- Example email you've written:
{style.get('example_email', '')}"""

        # Append at end - models pay more attention to final messages
        messages = [
            *request.messages,
            {"role": "user", "content": style_context}
        ]
        request = request.override(messages=messages)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[inject_writing_style],
    context_schema=Context,
    store=InMemoryStore()
)
Inject compliance rules from Runtime Context based on user’s jurisdiction:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@dataclass
class Context:
    user_jurisdiction: str
    industry: str
    compliance_frameworks: list[str]

@wrap_model_call
def inject_compliance_rules(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Inject compliance constraints from Runtime Context."""
    # Read from Runtime Context: get compliance requirements
    jurisdiction = request.runtime.context.user_jurisdiction
    industry = request.runtime.context.industry
    frameworks = request.runtime.context.compliance_frameworks

    # Build compliance constraints
    rules = []
    if "GDPR" in frameworks:
        rules.append("- Must obtain explicit consent before processing personal data")
        rules.append("- Users have right to data deletion")
    if "HIPAA" in frameworks:
        rules.append("- Cannot share patient health information without authorization")
        rules.append("- Must use secure, encrypted communication")
    if industry == "finance":
        rules.append("- Cannot provide financial advice without proper disclaimers")

    if rules:
        compliance_context = f"""Compliance requirements for {jurisdiction}:
{chr(10).join(rules)}"""

        # Append at end - models pay more attention to final messages
        messages = [
            *request.messages,
            {"role": "user", "content": compliance_context}
        ]
        request = request.override(messages=messages)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[inject_compliance_rules],
    context_schema=Context
)

Transient vs Persistent Message Updates:The examples above use wrap_model_call to make transient updates - modifying what messages are sent to the model for a single call without changing what’s saved in state.For persistent updates that modify state (like the summarization example in Life-cycle Context), use life-cycle hooks like before_model or after_model to permanently update the conversation history. See the middleware documentation for more details.
```

##### ​Tools

Tools let the model interact with databases, APIs, and external systems. How you define and select tools directly impacts whether the model can complete tasks effectively.

###### ​Defining tools

Each tool needs a clear name, description, argument names, and argument descriptions. These aren’t just metadata—they guide the model’s reasoning about when and how to use the tool.

Copyfrom langchain.tools import tool

```python
@tool(parse_docstring=True)
def search_orders(
    user_id: str,
    status: str,
    limit: int = 10
) -> str:
    """Search for user orders by status.

    Use this when the user asks about order history or wants to check
    order status. Always filter by the provided status.

    Args:
        user_id: Unique identifier for the user
        status: Order status: 'pending', 'shipped', or 'delivered'
        limit: Maximum number of results to return
    """
    # Implementation here
    pass
```

###### ​Selecting tools

Not every tool is appropriate for every situation. Too many tools may overwhelm the model (overload context) and increase errors; too few limit capabilities. Dynamic tool selection adapts the available toolset based on authentication state, user permissions, feature flags, or conversation stage.

State Store Runtime ContextEnable advanced tools only after certain conversation milestones:Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@wrap_model_call
def state_based_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Filter tools based on conversation State."""
    # Read from State: check if user has authenticated
    state = request.state
    is_authenticated = state.get("authenticated", False)
    message_count = len(state["messages"])

    # Only enable sensitive tools after authentication
    if not is_authenticated:
        tools = [t for t in request.tools if t.name.startswith("public_")]
        request = request.override(tools=tools)
    elif message_count < 5:
        # Limit tools early in conversation
        tools = [t for t in request.tools if t.name != "advanced_search"]
        request = request.override(tools=tools)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[public_search, private_search, advanced_search],
    middleware=[state_based_tools]
)
Filter tools based on user preferences or feature flags in Store:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

@wrap_model_call
def store_based_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Filter tools based on Store preferences."""
    user_id = request.runtime.context.user_id

    # Read from Store: get user's enabled features
    store = request.runtime.store
    feature_flags = store.get(("features",), user_id)

    if feature_flags:
        enabled_features = feature_flags.value.get("enabled_tools", [])
        # Only include tools that are enabled for this user
        tools = [t for t in request.tools if t.name in enabled_features]
        request = request.override(tools=tools)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[search_tool, analysis_tool, export_tool],
    middleware=[store_based_tools],
    context_schema=Context,
    store=InMemoryStore()
)
Filter tools based on user permissions from Runtime Context:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@dataclass
class Context:
    user_role: str

@wrap_model_call
def context_based_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Filter tools based on Runtime Context permissions."""
    # Read from Runtime Context: get user role
    user_role = request.runtime.context.user_role

    if user_role == "admin":
        # Admins get all tools
        pass
    elif user_role == "editor":
        # Editors can't delete
        tools = [t for t in request.tools if t.name != "delete_data"]
        request = request.override(tools=tools)
    else:
        # Viewers get read-only tools
        tools = [t for t in request.tools if t.name.startswith("read_")]
        request = request.override(tools=tools)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[read_data, write_data, delete_data],
    middleware=[context_based_tools],
    context_schema=Context
)

See Dynamically selecting tools for more examples.
```

##### ​Model

Different models have different strengths, costs, and context windows. Select the right model for the task at hand, which
might change during an agent run.

State Store Runtime ContextUse different models based on conversation length from State:Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.chat_models import init_chat_model
from typing import Callable

# Initialize models once outside the middleware
large_model = init_chat_model("claude-sonnet-4-5-20250929")
standard_model = init_chat_model("gpt-4o")
efficient_model = init_chat_model("gpt-4o-mini")

@wrap_model_call
def state_based_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select model based on State conversation length."""
    # request.messages is a shortcut for request.state["messages"]
    message_count = len(request.messages)

    if message_count > 20:
        # Long conversation - use model with larger context window
        model = large_model
    elif message_count > 10:
        # Medium conversation
        model = standard_model
    else:
        # Short conversation - use efficient model
        model = efficient_model

    request = request.override(model=model)

    return handler(request)

agent = create_agent(
    model="gpt-4o-mini",
    tools=[...],
    middleware=[state_based_model]
)
Use user’s preferred model from Store:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.chat_models import init_chat_model
from typing import Callable
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

# Initialize available models once
MODEL_MAP = {
    "gpt-4o": init_chat_model("gpt-4o"),
    "gpt-4o-mini": init_chat_model("gpt-4o-mini"),
    "claude-sonnet": init_chat_model("claude-sonnet-4-5-20250929"),
}

@wrap_model_call
def store_based_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select model based on Store preferences."""
    user_id = request.runtime.context.user_id

    # Read from Store: get user's preferred model
    store = request.runtime.store
    user_prefs = store.get(("preferences",), user_id)

    if user_prefs:
        preferred_model = user_prefs.value.get("preferred_model")
        if preferred_model and preferred_model in MODEL_MAP:
            request = request.override(model=MODEL_MAP[preferred_model])

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[store_based_model],
    context_schema=Context,
    store=InMemoryStore()
)
Select model based on cost limits or environment from Runtime Context:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.chat_models import init_chat_model
from typing import Callable

@dataclass
class Context:
    cost_tier: str
    environment: str

# Initialize models once outside the middleware
premium_model = init_chat_model("claude-sonnet-4-5-20250929")
standard_model = init_chat_model("gpt-4o")
budget_model = init_chat_model("gpt-4o-mini")

@wrap_model_call
def context_based_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select model based on Runtime Context."""
    # Read from Runtime Context: cost tier and environment
    cost_tier = request.runtime.context.cost_tier
    environment = request.runtime.context.environment

    if environment == "production" and cost_tier == "premium":
        # Production premium users get best model
        model = premium_model
    elif cost_tier == "budget":
        # Budget tier gets efficient model
        model = budget_model
    else:
        # Standard tier
        model = standard_model

    request = request.override(model=model)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[context_based_model],
    context_schema=Context
)

See Dynamic model for more examples.
```

##### ​Response Format

Structured output transforms unstructured text into validated, structured data. When extracting specific fields or returning data for downstream systems, free-form text isn’t sufficient.

How it works: When you provide a schema as the response format, the model’s final response is guaranteed to conform to that schema. The agent runs the model / tool calling loop until the model is done calling tools, then the final response is coerced into the provided format.

###### ​Defining formats

Schema definitions guide the model. Field names, types, and descriptions specify exactly what format the output should adhere to.

Copyfrom pydantic import BaseModel, Field

```python
class CustomerSupportTicket(BaseModel):
    """Structured ticket information extracted from customer message."""

    category: str = Field(
        description="Issue category: 'billing', 'technical', 'account', or 'product'"
    )
    priority: str = Field(
        description="Urgency level: 'low', 'medium', 'high', or 'critical'"
    )
    summary: str = Field(
        description="One-sentence summary of the customer's issue"
    )
    customer_sentiment: str = Field(
        description="Customer's emotional tone: 'frustrated', 'neutral', or 'satisfied'"
    )
```

###### ​Selecting formats

Dynamic response format selection adapts schemas based on user preferences, conversation stage, or role—returning simple formats early and detailed formats as complexity increases.

State Store Runtime ContextConfigure structured output based on conversation state:Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from pydantic import BaseModel, Field
from typing import Callable

class SimpleResponse(BaseModel):
    """Simple response for early conversation."""
    answer: str = Field(description="A brief answer")

class DetailedResponse(BaseModel):
    """Detailed response for established conversation."""
    answer: str = Field(description="A detailed answer")
    reasoning: str = Field(description="Explanation of reasoning")
    confidence: float = Field(description="Confidence score 0-1")

@wrap_model_call
def state_based_output(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select output format based on State."""
    # request.messages is a shortcut for request.state["messages"]
    message_count = len(request.messages)

    if message_count < 3:
        # Early conversation - use simple format
        request = request.override(response_format=SimpleResponse)
    else:
        # Established conversation - use detailed format
        request = request.override(response_format=DetailedResponse)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[state_based_output]
)
Configure output format based on user preferences in Store:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from pydantic import BaseModel, Field
from typing import Callable
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

class VerboseResponse(BaseModel):
    """Verbose response with details."""
    answer: str = Field(description="Detailed answer")
    sources: list[str] = Field(description="Sources used")

class ConciseResponse(BaseModel):
    """Concise response."""
    answer: str = Field(description="Brief answer")

@wrap_model_call
def store_based_output(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select output format based on Store preferences."""
    user_id = request.runtime.context.user_id

    # Read from Store: get user's preferred response style
    store = request.runtime.store
    user_prefs = store.get(("preferences",), user_id)

    if user_prefs:
        style = user_prefs.value.get("response_style", "concise")
        if style == "verbose":
            request = request.override(response_format=VerboseResponse)
        else:
            request = request.override(response_format=ConciseResponse)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[store_based_output],
    context_schema=Context,
    store=InMemoryStore()
)
Configure output format based on Runtime Context like user role or environment:Copyfrom dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from pydantic import BaseModel, Field
from typing import Callable

@dataclass
class Context:
    user_role: str
    environment: str

class AdminResponse(BaseModel):
    """Response with technical details for admins."""
    answer: str = Field(description="Answer")
    debug_info: dict = Field(description="Debug information")
    system_status: str = Field(description="System status")

class UserResponse(BaseModel):
    """Simple response for regular users."""
    answer: str = Field(description="Answer")

@wrap_model_call
def context_based_output(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select output format based on Runtime Context."""
    # Read from Runtime Context: user role and environment
    user_role = request.runtime.context.user_role
    environment = request.runtime.context.environment

    if user_role == "admin" and environment == "production":
        # Admins in production get detailed output
        request = request.override(response_format=AdminResponse)
    else:
        # Regular users get simple output
        request = request.override(response_format=UserResponse)

    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[context_based_output],
    context_schema=Context
)
```

#### ​Tool Context

Tools are special in that they both read and write context.

In the most basic case, when a tool executes, it receives the LLM’s request parameters and returns a tool message back. The tool does its work and produces a result.

Tools can also fetch important information for the model that allows it to perform and complete tasks.

##### ​Reads

Most real-world tools need more than just the LLM’s parameters. They need user IDs for database queries, API keys for external services, or current session state to make decisions. Tools read from state, store, and runtime context to access this information.

State Store Runtime ContextRead from State to check current session information:Copyfrom langchain.tools import tool, ToolRuntime
```python
from langchain.agents import create_agent

@tool
def check_authentication(
    runtime: ToolRuntime
) -> str:
    """Check if user is authenticated."""
    # Read from State: check current auth status
    current_state = runtime.state
    is_authenticated = current_state.get("authenticated", False)

    if is_authenticated:
        return "User is authenticated"
    else:
        return "User is not authenticated"

agent = create_agent(
    model="gpt-4o",
    tools=[check_authentication]
)
Read from Store to access persisted user preferences:Copyfrom dataclasses import dataclass
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

@tool
def get_preference(
    preference_key: str,
    runtime: ToolRuntime[Context]
) -> str:
    """Get user preference from Store."""
    user_id = runtime.context.user_id

    # Read from Store: get existing preferences
    store = runtime.store
    existing_prefs = store.get(("preferences",), user_id)

    if existing_prefs:
        value = existing_prefs.value.get(preference_key)
        return f"{preference_key}: {value}" if value else f"No preference set for {preference_key}"
    else:
        return "No preferences found"

agent = create_agent(
    model="gpt-4o",
    tools=[get_preference],
    context_schema=Context,
    store=InMemoryStore()
)
Read from Runtime Context for configuration like API keys and user IDs:Copyfrom dataclasses import dataclass
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent

@dataclass
class Context:
    user_id: str
    api_key: str
    db_connection: str

@tool
def fetch_user_data(
    query: str,
    runtime: ToolRuntime[Context]
) -> str:
    """Fetch data using Runtime Context configuration."""
    # Read from Runtime Context: get API key and DB connection
    user_id = runtime.context.user_id
    api_key = runtime.context.api_key
    db_connection = runtime.context.db_connection

    # Use configuration to fetch data
    results = perform_database_query(db_connection, query, api_key)

    return f"Found {len(results)} results for user {user_id}"

agent = create_agent(
    model="gpt-4o",
    tools=[fetch_user_data],
    context_schema=Context
)

# Invoke with runtime context
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Get my data"}]},
    context=Context(
        user_id="user_123",
        api_key="sk-...",
        db_connection="postgresql://..."
    )
)
```

##### ​Writes

Tool results can be used to help an agent complete a given task. Tools can both return results directly to the model
and update the memory of the agent to make important context available to future steps.

State StoreWrite to State to track session-specific information using Command:Copyfrom langchain.tools import tool, ToolRuntime
```python
from langchain.agents import create_agent
from langgraph.types import Command

@tool
def authenticate_user(
    password: str,
    runtime: ToolRuntime
) -> Command:
    """Authenticate user and update State."""
    # Perform authentication (simplified)
    if password == "correct":
        # Write to State: mark as authenticated using Command
        return Command(
            update={"authenticated": True},
        )
    else:
        return Command(update={"authenticated": False})

agent = create_agent(
    model="gpt-4o",
    tools=[authenticate_user]
)
Write to Store to persist data across sessions:Copyfrom dataclasses import dataclass
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str

@tool
def save_preference(
    preference_key: str,
    preference_value: str,
    runtime: ToolRuntime[Context]
) -> str:
    """Save user preference to Store."""
    user_id = runtime.context.user_id

    # Read existing preferences
    store = runtime.store
    existing_prefs = store.get(("preferences",), user_id)

    # Merge with new preference
    prefs = existing_prefs.value if existing_prefs else {}
    prefs[preference_key] = preference_value

    # Write to Store: save updated preferences
    store.put(("preferences",), user_id, prefs)

    return f"Saved preference: {preference_key} = {preference_value}"

agent = create_agent(
    model="gpt-4o",
    tools=[save_preference],
    context_schema=Context,
    store=InMemoryStore()
)

See Tools for comprehensive examples of accessing state, store, and runtime context in tools.
```

#### ​Life-cycle Context

Control what happens between the core agent steps - intercepting data flow to implement cross-cutting concerns like summarization, guardrails, and logging.

As you’ve seen in Model Context and Tool Context, middleware is the mechanism that makes context engineering practical. Middleware allows you to hook into any step in the agent lifecycle and either:

- Update context - Modify state and store to persist changes, update conversation history, or save insights
- Jump in the lifecycle - Move to different steps in the agent cycle based on context (e.g., skip tool execution if a condition is met, repeat model call with modified context)

##### ​Example: Summarization

One of the most common life-cycle patterns is automatically condensing conversation history when it gets too long. Unlike the transient message trimming shown in Model Context, summarization persistently updates state - permanently replacing old messages with a summary that’s saved for all future turns.

LangChain offers built-in middleware for this:

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import SummarizationMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[...],
    middleware=[
        SummarizationMiddleware(
            model="gpt-4o-mini",
            trigger={"tokens": 4000},
            keep={"messages": 20},
        ),
    ],
)

When the conversation exceeds the token limit, SummarizationMiddleware automatically:

- Summarizes older messages using a separate LLM call
- Replaces them with a summary message in State (permanently)
- Keeps recent messages intact for context
The summarized conversation history is permanently updated - future turns will see the summary instead of the original messages.

For a complete list of built-in middleware, available hooks, and how to create custom middleware, see the Middleware documentation.
```

#### ​Best practices

- Start simple - Begin with static prompts and tools, add dynamics only when needed
- Test incrementally - Add one context engineering feature at a time
- Monitor performance - Track model calls, token usage, and latency
- Use built-in middleware - Leverage SummarizationMiddleware, LLMToolSelectorMiddleware, etc.
- Document your context strategy - Make it clear what context is being passed and why
- Understand transient vs persistent: Model context changes are transient (per-call), while life-cycle context changes persist to state

#### ​Related resources

- Context conceptual overview - Understand context types and when to use them
- Middleware - Complete middleware guide
- Tools - Tool creation and context access
- Memory - Short-term and long-term memory patterns
- Agents - Core agent concepts
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Guardrails - Docs by LangChain {#doc-32}

**Source:** [https://docs.langchain.com/oss/python/langchain/guardrails](https://docs.langchain.com/oss/python/langchain/guardrails)

### Guardrails

Copy page

#### Deterministic guardrails

Use rule-based logic like regex patterns, keyword matching, or explicit checks. Fast, predictable, and cost-effective, but may miss nuanced violations.

#### Model-based guardrails

Use LLMs or classifiers to evaluate content with semantic understanding. Catch subtle issues that rules miss, but are slower and more expensive.

#### ​Built-in guardrails

##### ​PII detection

LangChain provides built-in middleware for detecting and handling Personally Identifiable Information (PII) in conversations. This middleware can detect common PII types like emails, credit cards, IP addresses, and more.

PII detection middleware is helpful for cases such as health care and financial applications with compliance requirements, customer service agents that need to sanitize logs, and generally any application handling sensitive user data.

The PII middleware supports multiple strategies for handling detected PII:

StrategyDescriptionExampleredactReplace with [REDACTED_{PII_TYPE}][REDACTED_EMAIL]maskPartially obscure (e.g., last 4 digits)****-****-****-1234hashReplace with deterministic hasha8f5f167...blockRaise exception when detectedError thrown

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import PIIMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[customer_service_tool, email_tool],
    middleware=[
        # Redact emails in user input before sending to model
        PIIMiddleware(
            "email",
            strategy="redact",
            apply_to_input=True,
        ),
        # Mask credit cards in user input
        PIIMiddleware(
            "credit_card",
            strategy="mask",
            apply_to_input=True,
        ),
        # Block API keys - raise error if detected
        PIIMiddleware(
            "api_key",
            detector=r"sk-[a-zA-Z0-9]{32}",
            strategy="block",
            apply_to_input=True,
        ),
    ],
)

# When user provides PII, it will be handled according to the strategy
result = agent.invoke({
    "messages": [{"role": "user", "content": "My email is john.doe@example.com and card is 5105-1051-0510-5100"}]
})

Built-in PII types and configurationBuilt-in PII types:
email - Email addresses
credit_card - Credit card numbers (Luhn validated)
ip - IP addresses
mac_address - MAC addresses
url - URLs
Configuration options:ParameterDescriptionDefaultpii_typeType of PII to detect (built-in or custom)RequiredstrategyHow to handle detected PII ("block", "redact", "mask", "hash")"redact"detectorCustom detector function or regex patternNone (uses built-in)apply_to_inputCheck user messages before model callTrueapply_to_outputCheck AI messages after model callFalseapply_to_tool_resultsCheck tool result messages after executionFalse

See the middleware documentation for complete details on PII detection capabilities.
```

##### ​Human-in-the-loop

LangChain provides built-in middleware for requiring human approval before executing sensitive operations. This is one of the most effective guardrails for high-stakes decisions.

Human-in-the-loop middleware is helpful for cases such as financial transactions and transfers, deleting or modifying production data, sending communications to external parties, and any operation with significant business impact.

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

agent = create_agent(
    model="gpt-4o",
    tools=[search_tool, send_email_tool, delete_database_tool],
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                # Require approval for sensitive operations
                "send_email": True,
                "delete_database": True,
                # Auto-approve safe operations
                "search": False,
            }
        ),
    ],
    # Persist the state across interrupts
    checkpointer=InMemorySaver(),
)

# Human-in-the-loop requires a thread ID for persistence
config = {"configurable": {"thread_id": "some_id"}}

# Agent will pause and wait for approval before executing sensitive tools
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Send an email to the team"}]},
    config=config
)

result = agent.invoke(
    Command(resume={"decisions": [{"type": "approve"}]}),
    config=config  # Same thread ID to resume the paused conversation
)

See the human-in-the-loop documentation for complete details on implementing approval workflows.
```

#### ​Custom guardrails

For more sophisticated guardrails, you can create custom middleware that runs before or after the agent executes. This gives you full control over validation logic, content filtering, and safety checks.

##### ​Before agent guardrails

Use “before agent” hooks to validate requests once at the start of each invocation. This is useful for session-level checks like authentication, rate limiting, or blocking inappropriate requests before any processing begins.

Class syntaxDecorator syntaxCopyfrom typing import Any

```python
from langchain.agents.middleware import AgentMiddleware, AgentState, hook_config
from langgraph.runtime import Runtime

class ContentFilterMiddleware(AgentMiddleware):
    """Deterministic guardrail: Block requests containing banned keywords."""

    def __init__(self, banned_keywords: list[str]):
        super().__init__()
        self.banned_keywords = [kw.lower() for kw in banned_keywords]

    @hook_config(can_jump_to=["end"])
    def before_agent(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        # Get the first user message
        if not state["messages"]:
            return None

        first_message = state["messages"][0]
        if first_message.type != "human":
            return None

        content = first_message.content.lower()

        # Check for banned keywords
        for keyword in self.banned_keywords:
            if keyword in content:
                # Block execution before any processing
                return {
                    "messages": [{
                        "role": "assistant",
                        "content": "I cannot process requests containing inappropriate content. Please rephrase your request."
                    }],
                    "jump_to": "end"
                }

        return None

# Use the custom guardrail
from langchain.agents import create_agent

agent = create_agent(
    model="gpt-4o",
    tools=[search_tool, calculator_tool],
    middleware=[
        ContentFilterMiddleware(
            banned_keywords=["hack", "exploit", "malware"]
        ),
    ],
)

# This request will be blocked before any processing
result = agent.invoke({
    "messages": [{"role": "user", "content": "How do I hack into a database?"}]
})
```

##### ​After agent guardrails

Use “after agent” hooks to validate final outputs once before returning to the user. This is useful for model-based safety checks, quality validation, or final compliance scans on the complete agent response.

Class syntaxDecorator syntaxCopyfrom langchain.agents.middleware import AgentMiddleware, AgentState, hook_config
```python
from langgraph.runtime import Runtime
from langchain.messages import AIMessage
from langchain.chat_models import init_chat_model
from typing import Any

class SafetyGuardrailMiddleware(AgentMiddleware):
    """Model-based guardrail: Use an LLM to evaluate response safety."""

    def __init__(self):
        super().__init__()
        self.safety_model = init_chat_model("gpt-4o-mini")

    @hook_config(can_jump_to=["end"])
    def after_agent(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        # Get the final AI response
        if not state["messages"]:
            return None

        last_message = state["messages"][-1]
        if not isinstance(last_message, AIMessage):
            return None

        # Use a model to evaluate safety
        safety_prompt = f"""Evaluate if this response is safe and appropriate.
        Respond with only 'SAFE' or 'UNSAFE'.

        Response: {last_message.content}"""

        result = self.safety_model.invoke([{"role": "user", "content": safety_prompt}])

        if "UNSAFE" in result.content:
            last_message.content = "I cannot provide that response. Please rephrase your request."

        return None

# Use the safety guardrail
from langchain.agents import create_agent

agent = create_agent(
    model="gpt-4o",
    tools=[search_tool, calculator_tool],
    middleware=[SafetyGuardrailMiddleware()],
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "How do I make explosives?"}]
})
```

##### ​Combine multiple guardrails

You can stack multiple guardrails by adding them to the middleware array. They execute in order, allowing you to build layered protection:

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import PIIMiddleware, HumanInTheLoopMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[search_tool, send_email_tool],
    middleware=[
        # Layer 1: Deterministic input filter (before agent)
        ContentFilterMiddleware(banned_keywords=["hack", "exploit"]),

        # Layer 2: PII protection (before and after model)
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
        PIIMiddleware("email", strategy="redact", apply_to_output=True),

        # Layer 3: Human approval for sensitive tools
        HumanInTheLoopMiddleware(interrupt_on={"send_email": True}),

        # Layer 4: Model-based safety check (after agent)
        SafetyGuardrailMiddleware(),
    ],
)
```

#### ​Additional resources

- Middleware documentation - Complete guide to custom middleware
- Middleware API reference - Complete guide to custom middleware
- Human-in-the-loop - Add human review for sensitive operations
- Testing agents - Strategies for testing safety mechanisms
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Custom middleware - Docs by LangChain {#doc-33}

**Source:** [https://docs.langchain.com/oss/python/langchain/middleware/custom](https://docs.langchain.com/oss/python/langchain/middleware/custom)

### Custom middleware

Copy page

#### ​Hooks

Middleware provides two styles of hooks to intercept agent execution:

Node-style hooksRun sequentially at specific execution points.Wrap-style hooksRun around each model or tool call.

​Node-style hooks

Run sequentially at specific execution points. Use for logging, validation, and state updates.

Available hooks:

- before_agent - Before agent starts (once per invocation)
- before_model - Before each model call
- after_model - After each model response
- after_agent - After agent completes (once per invocation)
Example:

Decorator ClassCopyfrom langchain.agents.middleware import before_model, after_model, AgentState
```python
from langchain.messages import AIMessage
from langgraph.runtime import Runtime
from typing import Any

@before_model(can_jump_to=["end"])
def check_message_limit(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    if len(state["messages"]) >= 50:
        return {
            "messages": [AIMessage("Conversation limit reached.")],
            "jump_to": "end"
        }
    return None

@after_model
def log_response(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    print(f"Model returned: {state['messages'][-1].content}")
    return None
Copyfrom langchain.agents.middleware import AgentMiddleware, AgentState, hook_config
from langchain.messages import AIMessage
from langgraph.runtime import Runtime
from typing import Any

class MessageLimitMiddleware(AgentMiddleware):
    def __init__(self, max_messages: int = 50):
        super().__init__()
        self.max_messages = max_messages

    @hook_config(can_jump_to=["end"])
    def before_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        if len(state["messages"]) == self.max_messages:
            return {
                "messages": [AIMessage("Conversation limit reached.")],
                "jump_to": "end"
            }
        return None

    def after_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        print(f"Model returned: {state['messages'][-1].content}")
        return None

​Wrap-style hooks

Intercept execution and control when the handler is called. Use for retries, caching, and transformation.

You decide if the handler is called zero times (short-circuit), once (normal flow), or multiple times (retry logic).

Available hooks:

- wrap_model_call - Around each model call
- wrap_tool_call - Around each tool call
Example:

Decorator ClassCopyfrom langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@wrap_model_call
def retry_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    for attempt in range(3):
        try:
            return handler(request)
        except Exception as e:
            if attempt == 2:
                raise
            print(f"Retry {attempt + 1}/3 after error: {e}")
Copyfrom langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from typing import Callable

class RetryMiddleware(AgentMiddleware):
    def __init__(self, max_retries: int = 3):
        super().__init__()
        self.max_retries = max_retries

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        for attempt in range(self.max_retries):
            try:
                return handler(request)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                print(f"Retry {attempt + 1}/{self.max_retries} after error: {e}")

​Create middleware

You can create middleware in two ways:

Decorator-based middlewareQuick and simple for single-hook middleware. Use decorators to wrap individual functions.Class-based middlewareMore powerful for complex middleware with multiple hooks or configuration.

​Decorator-based middleware

Quick and simple for single-hook middleware. Use decorators to wrap individual functions.

Available decorators:

Node-style:

- @before_agent - Runs before agent starts (once per invocation)
- @before_model - Runs before each model call
- @after_model - Runs after each model response
- @after_agent - Runs after agent completes (once per invocation)
Wrap-style:

- @wrap_model_call - Wraps each model call with custom logic
- @wrap_tool_call - Wraps each tool call with custom logic
Convenience:

- @dynamic_prompt - Generates dynamic system prompts
Example:

Copyfrom langchain.agents.middleware import (
    before_model,
    wrap_model_call,
    AgentState,
    ModelRequest,
    ModelResponse,
)
from langchain.agents import create_agent
from langgraph.runtime import Runtime
from typing import Any, Callable

@before_model
def log_before_model(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    print(f"About to call model with {len(state['messages'])} messages")
    return None

@wrap_model_call
def retry_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    for attempt in range(3):
        try:
            return handler(request)
        except Exception as e:
            if attempt == 2:
                raise
            print(f"Retry {attempt + 1}/3 after error: {e}")

agent = create_agent(
    model="gpt-4o",
    middleware=[log_before_model, retry_model],
    tools=[...],
)

When to use decorators:

- Single hook needed
- No complex configuration
- Quick prototyping
​Class-based middleware

More powerful for complex middleware with multiple hooks or configuration. Use classes when you need to define both sync and async implementations for the same hook, or when you want to combine multiple hooks in a single middleware.

Example:

Copyfrom langchain.agents.middleware import (
    AgentMiddleware,
    AgentState,
    ModelRequest,
    ModelResponse,
)
from langgraph.runtime import Runtime
from typing import Any, Callable

class LoggingMiddleware(AgentMiddleware):
    def before_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        print(f"About to call model with {len(state['messages'])} messages")
        return None

    def after_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        print(f"Model returned: {state['messages'][-1].content}")
        return None

agent = create_agent(
    model="gpt-4o",
    middleware=[LoggingMiddleware()],
    tools=[...],
)

When to use classes:

- Defining both sync and async implementations for the same hook
- Multiple hooks needed in a single middleware
- Complex configuration required (e.g., configurable thresholds, custom models)
- Reuse across projects with init-time configuration
​Custom state schema

Middleware can extend the agent’s state with custom properties. This enables middleware to:

- Track state across execution: Maintain counters, flags, or other values that persist throughout the agent’s execution lifecycle
- Share data between hooks: Pass information from before_model to after_model or between different middleware instances
- Implement cross-cutting concerns: Add functionality like rate limiting, usage tracking, user context, or audit logging without modifying the core agent logic
- Make conditional decisions: Use accumulated state to determine whether to continue execution, jump to different nodes, or modify behavior dynamically
Decorator ClassCopyfrom langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.agents.middleware import AgentState, before_model, after_model
from typing_extensions import NotRequired
from typing import Any
from langgraph.runtime import Runtime

class CustomState(AgentState):
    model_call_count: NotRequired[int]
    user_id: NotRequired[str]

@before_model(state_schema=CustomState, can_jump_to=["end"])
def check_call_limit(state: CustomState, runtime: Runtime) -> dict[str, Any] | None:
    count = state.get("model_call_count", 0)
    if count > 10:
        return {"jump_to": "end"}
    return None

@after_model(state_schema=CustomState)
def increment_counter(state: CustomState, runtime: Runtime) -> dict[str, Any] | None:
    return {"model_call_count": state.get("model_call_count", 0) + 1}

agent = create_agent(
    model="gpt-4o",
    middleware=[check_call_limit, increment_counter],
    tools=[],
)

# Invoke with custom state
result = agent.invoke({
    "messages": [HumanMessage("Hello")],
    "model_call_count": 0,
    "user_id": "user-123",
})
Copyfrom langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.agents.middleware import AgentState, AgentMiddleware
from typing_extensions import NotRequired
from typing import Any

class CustomState(AgentState):
    model_call_count: NotRequired[int]
    user_id: NotRequired[str]

class CallCounterMiddleware(AgentMiddleware[CustomState]):
    state_schema = CustomState

    def before_model(self, state: CustomState, runtime) -> dict[str, Any] | None:
        count = state.get("model_call_count", 0)
        if count > 10:
            return {"jump_to": "end"}
        return None

    def after_model(self, state: CustomState, runtime) -> dict[str, Any] | None:
        return {"model_call_count": state.get("model_call_count", 0) + 1}

agent = create_agent(
    model="gpt-4o",
    middleware=[CallCounterMiddleware()],
    tools=[],
)

# Invoke with custom state
result = agent.invoke({
    "messages": [HumanMessage("Hello")],
    "model_call_count": 0,
    "user_id": "user-123",
})

​Execution order

When using multiple middleware, understand how they execute:

Copyagent = create_agent(
    model="gpt-4o",
    middleware=[middleware1, middleware2, middleware3],
    tools=[...],
)

Execution flowBefore hooks run in order:
middleware1.before_agent()
middleware2.before_agent()
middleware3.before_agent()
Agent loop starts
middleware1.before_model()
middleware2.before_model()
middleware3.before_model()
Wrap hooks nest like function calls:
middleware1.wrap_model_call() → middleware2.wrap_model_call() → middleware3.wrap_model_call() → model
After hooks run in reverse order:
middleware3.after_model()
middleware2.after_model()
middleware1.after_model()
Agent loop ends
middleware3.after_agent()
middleware2.after_agent()
middleware1.after_agent()

Key rules:

- before_* hooks: First to last
- after_* hooks: Last to first (reverse)
- wrap_* hooks: Nested (first middleware wraps all others)
​Agent jumps

To exit early from middleware, return a dictionary with jump_to:

Available jump targets:

- 'end': Jump to the end of the agent execution (or the first after_agent hook)
- 'tools': Jump to the tools node
- 'model': Jump to the model node (or the first before_model hook)
Decorator ClassCopyfrom langchain.agents.middleware import after_model, hook_config, AgentState
from langchain.messages import AIMessage
from langgraph.runtime import Runtime
from typing import Any

@after_model
@hook_config(can_jump_to=["end"])
def check_for_blocked(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    last_message = state["messages"][-1]
    if "BLOCKED" in last_message.content:
        return {
            "messages": [AIMessage("I cannot respond to that request.")],
            "jump_to": "end"
        }
    return None
Copyfrom langchain.agents.middleware import AgentMiddleware, hook_config, AgentState
from langchain.messages import AIMessage
from langgraph.runtime import Runtime
from typing import Any

class BlockedContentMiddleware(AgentMiddleware):
    @hook_config(can_jump_to=["end"])
    def after_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        last_message = state["messages"][-1]
        if "BLOCKED" in last_message.content:
            return {
                "messages": [AIMessage("I cannot respond to that request.")],
                "jump_to": "end"
            }
        return None

​Best practices

- Keep middleware focused - each should do one thing well
- Handle errors gracefully - don’t let middleware errors crash the agent
- Use appropriate hook types:

Node-style for sequential logic (logging, validation)
Wrap-style for control flow (retry, fallback, caching)
- Node-style for sequential logic (logging, validation)
- Wrap-style for control flow (retry, fallback, caching)
- Clearly document any custom state properties
- Unit test middleware independently before integrating
- Consider execution order - place critical middleware first in the list
- Use built-in middleware when possible
​Examples

​Dynamic model selection

Decorator ClassCopyfrom langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.chat_models import init_chat_model
from typing import Callable

complex_model = init_chat_model("gpt-4o")
simple_model = init_chat_model("gpt-4o-mini")

@wrap_model_call
def dynamic_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    # Use different model based on conversation length
    if len(request.messages) > 10:
        model = complex_model
    else:
        model = simple_model
    return handler(request.override(model=model))
Copyfrom langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.chat_models import init_chat_model
from typing import Callable

complex_model = init_chat_model("gpt-4o")
simple_model = init_chat_model("gpt-4o-mini")

class DynamicModelMiddleware(AgentMiddleware):
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        # Use different model based on conversation length
        if len(request.messages) > 10:
            model = complex_model
        else:
            model = simple_model
        return handler(request.override(model=model))

​Tool call monitoring

Decorator ClassCopyfrom langchain.agents.middleware import wrap_tool_call
from langchain.tools.tool_node import ToolCallRequest
from langchain.messages import ToolMessage
from langgraph.types import Command
from typing import Callable

@wrap_tool_call
def monitor_tool(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:
    print(f"Executing tool: {request.tool_call['name']}")
    print(f"Arguments: {request.tool_call['args']}")
    try:
        result = handler(request)
        print(f"Tool completed successfully")
        return result
    except Exception as e:
        print(f"Tool failed: {e}")
        raise
Copyfrom langchain.tools.tool_node import ToolCallRequest
from langchain.agents.middleware import AgentMiddleware
from langchain.messages import ToolMessage
from langgraph.types import Command
from typing import Callable

class ToolMonitoringMiddleware(AgentMiddleware):
    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        print(f"Executing tool: {request.tool_call['name']}")
        print(f"Arguments: {request.tool_call['args']}")
        try:
            result = handler(request)
            print(f"Tool completed successfully")
            return result
        except Exception as e:
            print(f"Tool failed: {e}")
            raise

​Dynamically selecting tools

Select relevant tools at runtime to improve performance and accuracy.

Benefits:

- Shorter prompts - Reduce complexity by exposing only relevant tools
- Better accuracy - Models choose correctly from fewer options
- Permission control - Dynamically filter tools based on user access
Decorator ClassCopyfrom langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@wrap_model_call
def select_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """Middleware to select relevant tools based on state/context."""
    # Select a small, relevant subset of tools based on state/context
    relevant_tools = select_relevant_tools(request.state, request.runtime)
    return handler(request.override(tools=relevant_tools))

agent = create_agent(
    model="gpt-4o",
    tools=all_tools,  # All available tools need to be registered upfront
    middleware=[select_tools],
)
Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from typing import Callable

class ToolSelectorMiddleware(AgentMiddleware):
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Middleware to select relevant tools based on state/context."""
        # Select a small, relevant subset of tools based on state/context
        relevant_tools = select_relevant_tools(request.state, request.runtime)
        return handler(request.override(tools=relevant_tools))

agent = create_agent(
    model="gpt-4o",
    tools=all_tools,  # All available tools need to be registered upfront
    middleware=[ToolSelectorMiddleware()],
)

​Working with system messages

Modify system messages in middleware using the system_message field on ModelRequest. The system_message field contains a SystemMessage object (even if the agent was created with a string system_prompt).

Example: Adding context to system message

Decorator ClassCopyfrom langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.messages import SystemMessage
from typing import Callable

@wrap_model_call
def add_context(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    # Always work with content blocks
    new_content = list(request.system_message.content_blocks) + [
        {"type": "text", "text": "Additional context."}
    ]
    new_system_message = SystemMessage(content=new_content)
    return handler(request.override(system_message=new_system_message))
Copyfrom langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.messages import SystemMessage
from typing import Callable

class ContextMiddleware(AgentMiddleware):
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        # Always work with content blocks
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": "Additional context."}
        ]
        new_system_message = SystemMessage(content=new_content)
        return handler(request.override(system_message=new_system_message))

Example: Working with cache control (Anthropic)

When working with Anthropic models, you can use structured content blocks with cache control directives to cache large system prompts:

Decorator ClassCopyfrom langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.messages import SystemMessage
from typing import Callable

@wrap_model_call
def add_cached_context(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    # Always work with content blocks
    new_content = list(request.system_message.content_blocks) + [
        {
            "type": "text",
            "text": "Here is a large document to analyze:\n\n<document>...</document>",
            # content up until this point is cached
            "cache_control": {"type": "ephemeral"}
        }
    ]

    new_system_message = SystemMessage(content=new_content)
    return handler(request.override(system_message=new_system_message))
Copyfrom langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.messages import SystemMessage
from typing import Callable

class CachedContextMiddleware(AgentMiddleware):
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        # Always work with content blocks
        new_content = list(request.system_message.content_blocks) + [
            {
                "type": "text",
                "text": "Here is a large document to analyze:\n\n<document>...</document>",
                "cache_control": {"type": "ephemeral"}  # This content will be cached
            }
        ]

        new_system_message = SystemMessage(content=new_content)
        return handler(request.override(system_message=new_system_message))

Notes:

- ModelRequest.system_message is always a SystemMessage object, even if the agent was created with system_prompt="string"
- Use SystemMessage.content_blocks to access content as a list of blocks, regardless of whether the original content was a string or list
- When modifying system messages, use content_blocks and append new blocks to preserve existing structure
- You can pass SystemMessage objects directly to create_agent’s system_prompt parameter for advanced use cases like cache control
​Additional resources

- Middleware API reference
- Built-in middleware
- Testing agents
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```

#### Node-style hooks

Run sequentially at specific execution points.

#### Wrap-style hooks

Run around each model or tool call.

##### ​Node-style hooks

Run sequentially at specific execution points. Use for logging, validation, and state updates.

Available hooks:

- before_agent - Before agent starts (once per invocation)
- before_model - Before each model call
- after_model - After each model response
- after_agent - After agent completes (once per invocation)
Example:

Decorator ClassCopyfrom langchain.agents.middleware import before_model, after_model, AgentState
```python
from langchain.messages import AIMessage
from langgraph.runtime import Runtime
from typing import Any

@before_model(can_jump_to=["end"])
def check_message_limit(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    if len(state["messages"]) >= 50:
        return {
            "messages": [AIMessage("Conversation limit reached.")],
            "jump_to": "end"
        }
    return None

@after_model
def log_response(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    print(f"Model returned: {state['messages'][-1].content}")
    return None
Copyfrom langchain.agents.middleware import AgentMiddleware, AgentState, hook_config
from langchain.messages import AIMessage
from langgraph.runtime import Runtime
from typing import Any

class MessageLimitMiddleware(AgentMiddleware):
    def __init__(self, max_messages: int = 50):
        super().__init__()
        self.max_messages = max_messages

    @hook_config(can_jump_to=["end"])
    def before_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        if len(state["messages"]) == self.max_messages:
            return {
                "messages": [AIMessage("Conversation limit reached.")],
                "jump_to": "end"
            }
        return None

    def after_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        print(f"Model returned: {state['messages'][-1].content}")
        return None
```

##### ​Wrap-style hooks

Intercept execution and control when the handler is called. Use for retries, caching, and transformation.

You decide if the handler is called zero times (short-circuit), once (normal flow), or multiple times (retry logic).

Available hooks:

- wrap_model_call - Around each model call
- wrap_tool_call - Around each tool call
Example:

Decorator ClassCopyfrom langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
```python
from typing import Callable

@wrap_model_call
def retry_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    for attempt in range(3):
        try:
            return handler(request)
        except Exception as e:
            if attempt == 2:
                raise
            print(f"Retry {attempt + 1}/3 after error: {e}")
Copyfrom langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from typing import Callable

class RetryMiddleware(AgentMiddleware):
    def __init__(self, max_retries: int = 3):
        super().__init__()
        self.max_retries = max_retries

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        for attempt in range(self.max_retries):
            try:
                return handler(request)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                print(f"Retry {attempt + 1}/{self.max_retries} after error: {e}")
```

#### ​Create middleware

You can create middleware in two ways:

Decorator-based middlewareQuick and simple for single-hook middleware. Use decorators to wrap individual functions.Class-based middlewareMore powerful for complex middleware with multiple hooks or configuration.

​Decorator-based middleware

Quick and simple for single-hook middleware. Use decorators to wrap individual functions.

Available decorators:

Node-style:

- @before_agent - Runs before agent starts (once per invocation)
- @before_model - Runs before each model call
- @after_model - Runs after each model response
- @after_agent - Runs after agent completes (once per invocation)
Wrap-style:

- @wrap_model_call - Wraps each model call with custom logic
- @wrap_tool_call - Wraps each tool call with custom logic
Convenience:

- @dynamic_prompt - Generates dynamic system prompts
Example:

Copyfrom langchain.agents.middleware import (
    before_model,
    wrap_model_call,
    AgentState,
    ModelRequest,
    ModelResponse,
)
```python
from langchain.agents import create_agent
from langgraph.runtime import Runtime
from typing import Any, Callable

@before_model
def log_before_model(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    print(f"About to call model with {len(state['messages'])} messages")
    return None

@wrap_model_call
def retry_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    for attempt in range(3):
        try:
            return handler(request)
        except Exception as e:
            if attempt == 2:
                raise
            print(f"Retry {attempt + 1}/3 after error: {e}")

agent = create_agent(
    model="gpt-4o",
    middleware=[log_before_model, retry_model],
    tools=[...],
)

When to use decorators:

- Single hook needed
- No complex configuration
- Quick prototyping
​Class-based middleware

More powerful for complex middleware with multiple hooks or configuration. Use classes when you need to define both sync and async implementations for the same hook, or when you want to combine multiple hooks in a single middleware.

Example:

Copyfrom langchain.agents.middleware import (
    AgentMiddleware,
    AgentState,
    ModelRequest,
    ModelResponse,
)
from langgraph.runtime import Runtime
from typing import Any, Callable

class LoggingMiddleware(AgentMiddleware):
    def before_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        print(f"About to call model with {len(state['messages'])} messages")
        return None

    def after_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        print(f"Model returned: {state['messages'][-1].content}")
        return None

agent = create_agent(
    model="gpt-4o",
    middleware=[LoggingMiddleware()],
    tools=[...],
)

When to use classes:

- Defining both sync and async implementations for the same hook
- Multiple hooks needed in a single middleware
- Complex configuration required (e.g., configurable thresholds, custom models)
- Reuse across projects with init-time configuration
​Custom state schema

Middleware can extend the agent’s state with custom properties. This enables middleware to:

- Track state across execution: Maintain counters, flags, or other values that persist throughout the agent’s execution lifecycle
- Share data between hooks: Pass information from before_model to after_model or between different middleware instances
- Implement cross-cutting concerns: Add functionality like rate limiting, usage tracking, user context, or audit logging without modifying the core agent logic
- Make conditional decisions: Use accumulated state to determine whether to continue execution, jump to different nodes, or modify behavior dynamically
Decorator ClassCopyfrom langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.agents.middleware import AgentState, before_model, after_model
from typing_extensions import NotRequired
from typing import Any
from langgraph.runtime import Runtime

class CustomState(AgentState):
    model_call_count: NotRequired[int]
    user_id: NotRequired[str]

@before_model(state_schema=CustomState, can_jump_to=["end"])
def check_call_limit(state: CustomState, runtime: Runtime) -> dict[str, Any] | None:
    count = state.get("model_call_count", 0)
    if count > 10:
        return {"jump_to": "end"}
    return None

@after_model(state_schema=CustomState)
def increment_counter(state: CustomState, runtime: Runtime) -> dict[str, Any] | None:
    return {"model_call_count": state.get("model_call_count", 0) + 1}

agent = create_agent(
    model="gpt-4o",
    middleware=[check_call_limit, increment_counter],
    tools=[],
)

# Invoke with custom state
result = agent.invoke({
    "messages": [HumanMessage("Hello")],
    "model_call_count": 0,
    "user_id": "user-123",
})
Copyfrom langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.agents.middleware import AgentState, AgentMiddleware
from typing_extensions import NotRequired
from typing import Any

class CustomState(AgentState):
    model_call_count: NotRequired[int]
    user_id: NotRequired[str]

class CallCounterMiddleware(AgentMiddleware[CustomState]):
    state_schema = CustomState

    def before_model(self, state: CustomState, runtime) -> dict[str, Any] | None:
        count = state.get("model_call_count", 0)
        if count > 10:
            return {"jump_to": "end"}
        return None

    def after_model(self, state: CustomState, runtime) -> dict[str, Any] | None:
        return {"model_call_count": state.get("model_call_count", 0) + 1}

agent = create_agent(
    model="gpt-4o",
    middleware=[CallCounterMiddleware()],
    tools=[],
)

# Invoke with custom state
result = agent.invoke({
    "messages": [HumanMessage("Hello")],
    "model_call_count": 0,
    "user_id": "user-123",
})

​Execution order

When using multiple middleware, understand how they execute:

Copyagent = create_agent(
    model="gpt-4o",
    middleware=[middleware1, middleware2, middleware3],
    tools=[...],
)

Execution flowBefore hooks run in order:
middleware1.before_agent()
middleware2.before_agent()
middleware3.before_agent()
Agent loop starts
middleware1.before_model()
middleware2.before_model()
middleware3.before_model()
Wrap hooks nest like function calls:
middleware1.wrap_model_call() → middleware2.wrap_model_call() → middleware3.wrap_model_call() → model
After hooks run in reverse order:
middleware3.after_model()
middleware2.after_model()
middleware1.after_model()
Agent loop ends
middleware3.after_agent()
middleware2.after_agent()
middleware1.after_agent()

Key rules:

- before_* hooks: First to last
- after_* hooks: Last to first (reverse)
- wrap_* hooks: Nested (first middleware wraps all others)
​Agent jumps

To exit early from middleware, return a dictionary with jump_to:

Available jump targets:

- 'end': Jump to the end of the agent execution (or the first after_agent hook)
- 'tools': Jump to the tools node
- 'model': Jump to the model node (or the first before_model hook)
Decorator ClassCopyfrom langchain.agents.middleware import after_model, hook_config, AgentState
from langchain.messages import AIMessage
from langgraph.runtime import Runtime
from typing import Any

@after_model
@hook_config(can_jump_to=["end"])
def check_for_blocked(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    last_message = state["messages"][-1]
    if "BLOCKED" in last_message.content:
        return {
            "messages": [AIMessage("I cannot respond to that request.")],
            "jump_to": "end"
        }
    return None
Copyfrom langchain.agents.middleware import AgentMiddleware, hook_config, AgentState
from langchain.messages import AIMessage
from langgraph.runtime import Runtime
from typing import Any

class BlockedContentMiddleware(AgentMiddleware):
    @hook_config(can_jump_to=["end"])
    def after_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        last_message = state["messages"][-1]
        if "BLOCKED" in last_message.content:
            return {
                "messages": [AIMessage("I cannot respond to that request.")],
                "jump_to": "end"
            }
        return None

​Best practices

- Keep middleware focused - each should do one thing well
- Handle errors gracefully - don’t let middleware errors crash the agent
- Use appropriate hook types:

Node-style for sequential logic (logging, validation)
Wrap-style for control flow (retry, fallback, caching)
- Node-style for sequential logic (logging, validation)
- Wrap-style for control flow (retry, fallback, caching)
- Clearly document any custom state properties
- Unit test middleware independently before integrating
- Consider execution order - place critical middleware first in the list
- Use built-in middleware when possible
​Examples

​Dynamic model selection

Decorator ClassCopyfrom langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.chat_models import init_chat_model
from typing import Callable

complex_model = init_chat_model("gpt-4o")
simple_model = init_chat_model("gpt-4o-mini")

@wrap_model_call
def dynamic_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    # Use different model based on conversation length
    if len(request.messages) > 10:
        model = complex_model
    else:
        model = simple_model
    return handler(request.override(model=model))
Copyfrom langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.chat_models import init_chat_model
from typing import Callable

complex_model = init_chat_model("gpt-4o")
simple_model = init_chat_model("gpt-4o-mini")

class DynamicModelMiddleware(AgentMiddleware):
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        # Use different model based on conversation length
        if len(request.messages) > 10:
            model = complex_model
        else:
            model = simple_model
        return handler(request.override(model=model))

​Tool call monitoring

Decorator ClassCopyfrom langchain.agents.middleware import wrap_tool_call
from langchain.tools.tool_node import ToolCallRequest
from langchain.messages import ToolMessage
from langgraph.types import Command
from typing import Callable

@wrap_tool_call
def monitor_tool(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:
    print(f"Executing tool: {request.tool_call['name']}")
    print(f"Arguments: {request.tool_call['args']}")
    try:
        result = handler(request)
        print(f"Tool completed successfully")
        return result
    except Exception as e:
        print(f"Tool failed: {e}")
        raise
Copyfrom langchain.tools.tool_node import ToolCallRequest
from langchain.agents.middleware import AgentMiddleware
from langchain.messages import ToolMessage
from langgraph.types import Command
from typing import Callable

class ToolMonitoringMiddleware(AgentMiddleware):
    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        print(f"Executing tool: {request.tool_call['name']}")
        print(f"Arguments: {request.tool_call['args']}")
        try:
            result = handler(request)
            print(f"Tool completed successfully")
            return result
        except Exception as e:
            print(f"Tool failed: {e}")
            raise

​Dynamically selecting tools

Select relevant tools at runtime to improve performance and accuracy.

Benefits:

- Shorter prompts - Reduce complexity by exposing only relevant tools
- Better accuracy - Models choose correctly from fewer options
- Permission control - Dynamically filter tools based on user access
Decorator ClassCopyfrom langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@wrap_model_call
def select_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """Middleware to select relevant tools based on state/context."""
    # Select a small, relevant subset of tools based on state/context
    relevant_tools = select_relevant_tools(request.state, request.runtime)
    return handler(request.override(tools=relevant_tools))

agent = create_agent(
    model="gpt-4o",
    tools=all_tools,  # All available tools need to be registered upfront
    middleware=[select_tools],
)
Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from typing import Callable

class ToolSelectorMiddleware(AgentMiddleware):
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Middleware to select relevant tools based on state/context."""
        # Select a small, relevant subset of tools based on state/context
        relevant_tools = select_relevant_tools(request.state, request.runtime)
        return handler(request.override(tools=relevant_tools))

agent = create_agent(
    model="gpt-4o",
    tools=all_tools,  # All available tools need to be registered upfront
    middleware=[ToolSelectorMiddleware()],
)

​Working with system messages

Modify system messages in middleware using the system_message field on ModelRequest. The system_message field contains a SystemMessage object (even if the agent was created with a string system_prompt).

Example: Adding context to system message

Decorator ClassCopyfrom langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.messages import SystemMessage
from typing import Callable

@wrap_model_call
def add_context(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    # Always work with content blocks
    new_content = list(request.system_message.content_blocks) + [
        {"type": "text", "text": "Additional context."}
    ]
    new_system_message = SystemMessage(content=new_content)
    return handler(request.override(system_message=new_system_message))
Copyfrom langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.messages import SystemMessage
from typing import Callable

class ContextMiddleware(AgentMiddleware):
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        # Always work with content blocks
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": "Additional context."}
        ]
        new_system_message = SystemMessage(content=new_content)
        return handler(request.override(system_message=new_system_message))

Example: Working with cache control (Anthropic)

When working with Anthropic models, you can use structured content blocks with cache control directives to cache large system prompts:

Decorator ClassCopyfrom langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.messages import SystemMessage
from typing import Callable

@wrap_model_call
def add_cached_context(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    # Always work with content blocks
    new_content = list(request.system_message.content_blocks) + [
        {
            "type": "text",
            "text": "Here is a large document to analyze:\n\n<document>...</document>",
            # content up until this point is cached
            "cache_control": {"type": "ephemeral"}
        }
    ]

    new_system_message = SystemMessage(content=new_content)
    return handler(request.override(system_message=new_system_message))
Copyfrom langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.messages import SystemMessage
from typing import Callable

class CachedContextMiddleware(AgentMiddleware):
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        # Always work with content blocks
        new_content = list(request.system_message.content_blocks) + [
            {
                "type": "text",
                "text": "Here is a large document to analyze:\n\n<document>...</document>",
                "cache_control": {"type": "ephemeral"}  # This content will be cached
            }
        ]

        new_system_message = SystemMessage(content=new_content)
        return handler(request.override(system_message=new_system_message))

Notes:

- ModelRequest.system_message is always a SystemMessage object, even if the agent was created with system_prompt="string"
- Use SystemMessage.content_blocks to access content as a list of blocks, regardless of whether the original content was a string or list
- When modifying system messages, use content_blocks and append new blocks to preserve existing structure
- You can pass SystemMessage objects directly to create_agent’s system_prompt parameter for advanced use cases like cache control
​Additional resources

- Middleware API reference
- Built-in middleware
- Testing agents
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```

#### Decorator-based middleware

Quick and simple for single-hook middleware. Use decorators to wrap individual functions.

#### Class-based middleware

More powerful for complex middleware with multiple hooks or configuration.

##### ​Decorator-based middleware

Quick and simple for single-hook middleware. Use decorators to wrap individual functions.

Available decorators:

Node-style:

- @before_agent - Runs before agent starts (once per invocation)
- @before_model - Runs before each model call
- @after_model - Runs after each model response
- @after_agent - Runs after agent completes (once per invocation)
Wrap-style:

- @wrap_model_call - Wraps each model call with custom logic
- @wrap_tool_call - Wraps each tool call with custom logic
Convenience:

- @dynamic_prompt - Generates dynamic system prompts
Example:

Copyfrom langchain.agents.middleware import (
    before_model,
    wrap_model_call,
    AgentState,
    ModelRequest,
    ModelResponse,
)
```python
from langchain.agents import create_agent
from langgraph.runtime import Runtime
from typing import Any, Callable

@before_model
def log_before_model(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    print(f"About to call model with {len(state['messages'])} messages")
    return None

@wrap_model_call
def retry_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    for attempt in range(3):
        try:
            return handler(request)
        except Exception as e:
            if attempt == 2:
                raise
            print(f"Retry {attempt + 1}/3 after error: {e}")

agent = create_agent(
    model="gpt-4o",
    middleware=[log_before_model, retry_model],
    tools=[...],
)

When to use decorators:

- Single hook needed
- No complex configuration
- Quick prototyping
```

##### ​Class-based middleware

More powerful for complex middleware with multiple hooks or configuration. Use classes when you need to define both sync and async implementations for the same hook, or when you want to combine multiple hooks in a single middleware.

Example:

Copyfrom langchain.agents.middleware import (
    AgentMiddleware,
    AgentState,
    ModelRequest,
    ModelResponse,
)
```python
from langgraph.runtime import Runtime
from typing import Any, Callable

class LoggingMiddleware(AgentMiddleware):
    def before_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        print(f"About to call model with {len(state['messages'])} messages")
        return None

    def after_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        print(f"Model returned: {state['messages'][-1].content}")
        return None

agent = create_agent(
    model="gpt-4o",
    middleware=[LoggingMiddleware()],
    tools=[...],
)

When to use classes:

- Defining both sync and async implementations for the same hook
- Multiple hooks needed in a single middleware
- Complex configuration required (e.g., configurable thresholds, custom models)
- Reuse across projects with init-time configuration
```

#### ​Custom state schema

Middleware can extend the agent’s state with custom properties. This enables middleware to:

- Track state across execution: Maintain counters, flags, or other values that persist throughout the agent’s execution lifecycle
- Share data between hooks: Pass information from before_model to after_model or between different middleware instances
- Implement cross-cutting concerns: Add functionality like rate limiting, usage tracking, user context, or audit logging without modifying the core agent logic
- Make conditional decisions: Use accumulated state to determine whether to continue execution, jump to different nodes, or modify behavior dynamically
Decorator ClassCopyfrom langchain.agents import create_agent
```python
from langchain.messages import HumanMessage
from langchain.agents.middleware import AgentState, before_model, after_model
from typing_extensions import NotRequired
from typing import Any
from langgraph.runtime import Runtime

class CustomState(AgentState):
    model_call_count: NotRequired[int]
    user_id: NotRequired[str]

@before_model(state_schema=CustomState, can_jump_to=["end"])
def check_call_limit(state: CustomState, runtime: Runtime) -> dict[str, Any] | None:
    count = state.get("model_call_count", 0)
    if count > 10:
        return {"jump_to": "end"}
    return None

@after_model(state_schema=CustomState)
def increment_counter(state: CustomState, runtime: Runtime) -> dict[str, Any] | None:
    return {"model_call_count": state.get("model_call_count", 0) + 1}

agent = create_agent(
    model="gpt-4o",
    middleware=[check_call_limit, increment_counter],
    tools=[],
)

# Invoke with custom state
result = agent.invoke({
    "messages": [HumanMessage("Hello")],
    "model_call_count": 0,
    "user_id": "user-123",
})
Copyfrom langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain.agents.middleware import AgentState, AgentMiddleware
from typing_extensions import NotRequired
from typing import Any

class CustomState(AgentState):
    model_call_count: NotRequired[int]
    user_id: NotRequired[str]

class CallCounterMiddleware(AgentMiddleware[CustomState]):
    state_schema = CustomState

    def before_model(self, state: CustomState, runtime) -> dict[str, Any] | None:
        count = state.get("model_call_count", 0)
        if count > 10:
            return {"jump_to": "end"}
        return None

    def after_model(self, state: CustomState, runtime) -> dict[str, Any] | None:
        return {"model_call_count": state.get("model_call_count", 0) + 1}

agent = create_agent(
    model="gpt-4o",
    middleware=[CallCounterMiddleware()],
    tools=[],
)

# Invoke with custom state
result = agent.invoke({
    "messages": [HumanMessage("Hello")],
    "model_call_count": 0,
    "user_id": "user-123",
})
```

#### ​Execution order

When using multiple middleware, understand how they execute:

Copyagent = create_agent(
    model="gpt-4o",
    middleware=[middleware1, middleware2, middleware3],
    tools=[...],
)

Execution flowBefore hooks run in order:
middleware1.before_agent()
middleware2.before_agent()
middleware3.before_agent()
Agent loop starts
middleware1.before_model()
middleware2.before_model()
middleware3.before_model()
Wrap hooks nest like function calls:
middleware1.wrap_model_call() → middleware2.wrap_model_call() → middleware3.wrap_model_call() → model
After hooks run in reverse order:
middleware3.after_model()
middleware2.after_model()
middleware1.after_model()
Agent loop ends
middleware3.after_agent()
middleware2.after_agent()
middleware1.after_agent()

Key rules:

- before_* hooks: First to last
- after_* hooks: Last to first (reverse)
- wrap_* hooks: Nested (first middleware wraps all others)

#### ​Agent jumps

To exit early from middleware, return a dictionary with jump_to:

Available jump targets:

- 'end': Jump to the end of the agent execution (or the first after_agent hook)
- 'tools': Jump to the tools node
- 'model': Jump to the model node (or the first before_model hook)
Decorator ClassCopyfrom langchain.agents.middleware import after_model, hook_config, AgentState
```python
from langchain.messages import AIMessage
from langgraph.runtime import Runtime
from typing import Any

@after_model
@hook_config(can_jump_to=["end"])
def check_for_blocked(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    last_message = state["messages"][-1]
    if "BLOCKED" in last_message.content:
        return {
            "messages": [AIMessage("I cannot respond to that request.")],
            "jump_to": "end"
        }
    return None
Copyfrom langchain.agents.middleware import AgentMiddleware, hook_config, AgentState
from langchain.messages import AIMessage
from langgraph.runtime import Runtime
from typing import Any

class BlockedContentMiddleware(AgentMiddleware):
    @hook_config(can_jump_to=["end"])
    def after_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        last_message = state["messages"][-1]
        if "BLOCKED" in last_message.content:
            return {
                "messages": [AIMessage("I cannot respond to that request.")],
                "jump_to": "end"
            }
        return None
```

#### ​Best practices

- Keep middleware focused - each should do one thing well
- Handle errors gracefully - don’t let middleware errors crash the agent
- Use appropriate hook types:

Node-style for sequential logic (logging, validation)
Wrap-style for control flow (retry, fallback, caching)
- Node-style for sequential logic (logging, validation)
- Wrap-style for control flow (retry, fallback, caching)
- Clearly document any custom state properties
- Unit test middleware independently before integrating
- Consider execution order - place critical middleware first in the list
- Use built-in middleware when possible

#### ​Examples

##### ​Dynamic model selection

Decorator ClassCopyfrom langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
```python
from langchain.chat_models import init_chat_model
from typing import Callable

complex_model = init_chat_model("gpt-4o")
simple_model = init_chat_model("gpt-4o-mini")

@wrap_model_call
def dynamic_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    # Use different model based on conversation length
    if len(request.messages) > 10:
        model = complex_model
    else:
        model = simple_model
    return handler(request.override(model=model))
Copyfrom langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.chat_models import init_chat_model
from typing import Callable

complex_model = init_chat_model("gpt-4o")
simple_model = init_chat_model("gpt-4o-mini")

class DynamicModelMiddleware(AgentMiddleware):
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        # Use different model based on conversation length
        if len(request.messages) > 10:
            model = complex_model
        else:
            model = simple_model
        return handler(request.override(model=model))
```

##### ​Tool call monitoring

Decorator ClassCopyfrom langchain.agents.middleware import wrap_tool_call
```python
from langchain.tools.tool_node import ToolCallRequest
from langchain.messages import ToolMessage
from langgraph.types import Command
from typing import Callable

@wrap_tool_call
def monitor_tool(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:
    print(f"Executing tool: {request.tool_call['name']}")
    print(f"Arguments: {request.tool_call['args']}")
    try:
        result = handler(request)
        print(f"Tool completed successfully")
        return result
    except Exception as e:
        print(f"Tool failed: {e}")
        raise
Copyfrom langchain.tools.tool_node import ToolCallRequest
from langchain.agents.middleware import AgentMiddleware
from langchain.messages import ToolMessage
from langgraph.types import Command
from typing import Callable

class ToolMonitoringMiddleware(AgentMiddleware):
    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
    ) -> ToolMessage | Command:
        print(f"Executing tool: {request.tool_call['name']}")
        print(f"Arguments: {request.tool_call['args']}")
        try:
            result = handler(request)
            print(f"Tool completed successfully")
            return result
        except Exception as e:
            print(f"Tool failed: {e}")
            raise
```

##### ​Dynamically selecting tools

Select relevant tools at runtime to improve performance and accuracy.

Benefits:

- Shorter prompts - Reduce complexity by exposing only relevant tools
- Better accuracy - Models choose correctly from fewer options
- Permission control - Dynamically filter tools based on user access
Decorator ClassCopyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

@wrap_model_call
def select_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """Middleware to select relevant tools based on state/context."""
    # Select a small, relevant subset of tools based on state/context
    relevant_tools = select_relevant_tools(request.state, request.runtime)
    return handler(request.override(tools=relevant_tools))

agent = create_agent(
    model="gpt-4o",
    tools=all_tools,  # All available tools need to be registered upfront
    middleware=[select_tools],
)
Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from typing import Callable

class ToolSelectorMiddleware(AgentMiddleware):
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Middleware to select relevant tools based on state/context."""
        # Select a small, relevant subset of tools based on state/context
        relevant_tools = select_relevant_tools(request.state, request.runtime)
        return handler(request.override(tools=relevant_tools))

agent = create_agent(
    model="gpt-4o",
    tools=all_tools,  # All available tools need to be registered upfront
    middleware=[ToolSelectorMiddleware()],
)
```

##### ​Working with system messages

Modify system messages in middleware using the system_message field on ModelRequest. The system_message field contains a SystemMessage object (even if the agent was created with a string system_prompt).

Example: Adding context to system message

Decorator ClassCopyfrom langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
```python
from langchain.messages import SystemMessage
from typing import Callable

@wrap_model_call
def add_context(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    # Always work with content blocks
    new_content = list(request.system_message.content_blocks) + [
        {"type": "text", "text": "Additional context."}
    ]
    new_system_message = SystemMessage(content=new_content)
    return handler(request.override(system_message=new_system_message))
Copyfrom langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.messages import SystemMessage
from typing import Callable

class ContextMiddleware(AgentMiddleware):
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        # Always work with content blocks
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": "Additional context."}
        ]
        new_system_message = SystemMessage(content=new_content)
        return handler(request.override(system_message=new_system_message))

Example: Working with cache control (Anthropic)

When working with Anthropic models, you can use structured content blocks with cache control directives to cache large system prompts:

Decorator ClassCopyfrom langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.messages import SystemMessage
from typing import Callable

@wrap_model_call
def add_cached_context(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    # Always work with content blocks
    new_content = list(request.system_message.content_blocks) + [
        {
            "type": "text",
            "text": "Here is a large document to analyze:\n\n<document>...</document>",
            # content up until this point is cached
            "cache_control": {"type": "ephemeral"}
        }
    ]

    new_system_message = SystemMessage(content=new_content)
    return handler(request.override(system_message=new_system_message))
Copyfrom langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.messages import SystemMessage
from typing import Callable

class CachedContextMiddleware(AgentMiddleware):
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        # Always work with content blocks
        new_content = list(request.system_message.content_blocks) + [
            {
                "type": "text",
                "text": "Here is a large document to analyze:\n\n<document>...</document>",
                "cache_control": {"type": "ephemeral"}  # This content will be cached
            }
        ]

        new_system_message = SystemMessage(content=new_content)
        return handler(request.override(system_message=new_system_message))

Notes:

- ModelRequest.system_message is always a SystemMessage object, even if the agent was created with system_prompt="string"
- Use SystemMessage.content_blocks to access content as a list of blocks, regardless of whether the original content was a string or list
- When modifying system messages, use content_blocks and append new blocks to preserve existing structure
- You can pass SystemMessage objects directly to create_agent’s system_prompt parameter for advanced use cases like cache control
```

#### ​Additional resources

- Middleware API reference
- Built-in middleware
- Testing agents
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Built-in middleware - Docs by LangChain {#doc-34}

**Source:** [https://docs.langchain.com/oss/python/langchain/middleware/built-in](https://docs.langchain.com/oss/python/langchain/middleware/built-in)

### Built-in middleware

Copy page

#### ​Provider-agnostic middleware

The following middleware work with any LLM provider:

MiddlewareDescriptionSummarizationAutomatically summarize conversation history when approaching token limits.Human-in-the-loopPause execution for human approval of tool calls.Model call limitLimit the number of model calls to prevent excessive costs.Tool call limitControl tool execution by limiting call counts.Model fallbackAutomatically fallback to alternative models when primary fails.PII detectionDetect and handle Personally Identifiable Information (PII).To-do listEquip agents with task planning and tracking capabilities.LLM tool selectorUse an LLM to select relevant tools before calling main model.Tool retryAutomatically retry failed tool calls with exponential backoff.Model retryAutomatically retry failed model calls with exponential backoff.LLM tool emulatorEmulate tool execution using an LLM for testing purposes.Context editingManage conversation context by trimming or clearing tool uses.Shell toolExpose a persistent shell session to agents for command execution.File searchProvide Glob and Grep search tools over filesystem files.

##### ​Summarization

Automatically summarize conversation history when approaching token limits, preserving recent messages while compressing older context. Summarization is useful for the following:

- Long-running conversations that exceed context windows.
- Multi-turn dialogues with extensive history.
- Applications where preserving full conversation context matters.
API reference: SummarizationMiddleware

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import SummarizationMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[your_weather_tool, your_calculator_tool],
    middleware=[
        SummarizationMiddleware(
            model="gpt-4o-mini",
            trigger=("tokens", 4000),
            keep=("messages", 20),
        ),
    ],
)

Configuration optionsThe fraction conditions for trigger and keep (shown below) rely on a chat model’s profile data if using langchain>=1.1. If data are not available, use another condition or specify manually:Copyfrom langchain.chat_models import init_chat_model

custom_profile = {
    "max_input_tokens": 100_000,
    # ...
}
model = init_chat_model("gpt-4o", profile=custom_profile)
​modelstring | BaseChatModelrequiredModel for generating summaries. Can be a model identifier string (e.g., 'openai:gpt-4o-mini') or a BaseChatModel instance. See init_chat_model for more information.​triggerContextSize | list[ContextSize] | NoneCondition(s) for triggering summarization. Can be:
A single ContextSize tuple (specified condition must be met)
A list of ContextSize tuples (any condition must be met - OR logic)
Condition should be one of the following:
fraction (float): Fraction of model’s context size (0-1)
tokens (int): Absolute token count
messages (int): Message count
At least one condition must be specified. If not provided, summarization will not trigger automatically.See the API reference for ContextSize for more information.​keepContextSizedefault:"('messages', 20)"How much context to preserve after summarization. Specify exactly one of:
fraction (float): Fraction of model’s context size to keep (0-1)
tokens (int): Absolute token count to keep
messages (int): Number of recent messages to keep
See the API reference for ContextSize for more information.​token_counterfunctionCustom token counting function. Defaults to character-based counting.​summary_promptstringCustom prompt template for summarization. Uses built-in template if not specified. The template should include {messages} placeholder where conversation history will be inserted.​trim_tokens_to_summarizenumberdefault:"4000"Maximum number of tokens to include when generating the summary. Messages will be trimmed to fit this limit before summarization.​summary_prefixstringPrefix to add to the summary message. If not provided, a default prefix is used.​max_tokens_before_summarynumberdeprecatedDeprecated: Use trigger: {"tokens": value} instead. Token threshold for triggering summarization.​messages_to_keepnumberdeprecatedDeprecated: Use keep: {"messages": value} instead. Recent messages to preserve.

Full exampleThe summarization middleware monitors message token counts and automatically summarizes older messages when thresholds are reached.Trigger conditions control when summarization runs:
Single condition object (specified must be met)
Array of conditions (any condition must be met - OR logic)
Each condition can use fraction (of model’s context size), tokens (absolute count), or messages (message count)
Keep condition control how much context to preserve (specify exactly one):
fraction - Fraction of model’s context size to keep
tokens - Absolute token count to keep
messages - Number of recent messages to keep
Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware

# Single condition: trigger if tokens >= 4000
agent = create_agent(
    model="gpt-4o",
    tools=[your_weather_tool, your_calculator_tool],
    middleware=[
        SummarizationMiddleware(
            model="gpt-4o-mini",
            trigger=("tokens", 4000),
            keep=("messages", 20),
        ),
    ],
)

# Multiple conditions: trigger if number of tokens >= 3000 OR messages >= 6
agent2 = create_agent(
    model="gpt-4o",
    tools=[your_weather_tool, your_calculator_tool],
    middleware=[
        SummarizationMiddleware(
            model="gpt-4o-mini",
            trigger=[
                ("tokens", 3000),
                ("messages", 6),
            ],
            keep=("messages", 20),
        ),
    ],
)

# Using fractional limits
agent3 = create_agent(
    model="gpt-4o",
    tools=[your_weather_tool, your_calculator_tool],
    middleware=[
        SummarizationMiddleware(
            model="gpt-4o-mini",
            trigger=("fraction", 0.8),
            keep=("fraction", 0.3),
        ),
    ],
)
```

##### ​Human-in-the-loop

Pause agent execution for human approval, editing, or rejection of tool calls before they execute. Human-in-the-loop is useful for the following:

- High-stakes operations requiring human approval (e.g. database writes, financial transactions).
- Compliance workflows where human oversight is mandatory.
- Long-running conversations where human feedback guides the agent.
API reference: HumanInTheLoopMiddleware

Human-in-the-loop middleware requires a checkpointer to maintain state across interruptions.

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver

def read_email_tool(email_id: str) -> str:
    """Mock function to read an email by its ID."""
    return f"Email content for ID: {email_id}"

def send_email_tool(recipient: str, subject: str, body: str) -> str:
    """Mock function to send an email."""
    return f"Email sent to {recipient} with subject '{subject}'"

agent = create_agent(
    model="gpt-4o",
    tools=[your_read_email_tool, your_send_email_tool],
    checkpointer=InMemorySaver(),
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                "your_send_email_tool": {
                    "allowed_decisions": ["approve", "edit", "reject"],
                },
                "your_read_email_tool": False,
            }
        ),
    ],
)

For complete examples, configuration options, and integration patterns, see the Human-in-the-loop documentation.

Watch this video guide demonstrating Human-in-the-loop middleware behavior.
```

##### ​Model call limit

Limit the number of model calls to prevent infinite loops or excessive costs. Model call limit is useful for the following:

- Preventing runaway agents from making too many API calls.
- Enforcing cost controls on production deployments.
- Testing agent behavior within specific call budgets.
API reference: ModelCallLimitMiddleware

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import ModelCallLimitMiddleware
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model="gpt-4o",
    checkpointer=InMemorySaver(),  # Required for thread limiting
    tools=[],
    middleware=[
        ModelCallLimitMiddleware(
            thread_limit=10,
            run_limit=5,
            exit_behavior="end",
        ),
    ],
)

Watch this video guide demonstrating Model Call Limit middleware behavior.

Configuration options​thread_limitnumberMaximum model calls across all runs in a thread. Defaults to no limit.​run_limitnumberMaximum model calls per single invocation. Defaults to no limit.​exit_behaviorstringdefault:"end"Behavior when limit is reached. Options: 'end' (graceful termination) or 'error' (raise exception)
```

##### ​Tool call limit

Control agent execution by limiting the number of tool calls, either globally across all tools or for specific tools. Tool call limits are useful for the following:

- Preventing excessive calls to expensive external APIs.
- Limiting web searches or database queries.
- Enforcing rate limits on specific tool usage.
- Protecting against runaway agent loops.
API reference: ToolCallLimitMiddleware

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import ToolCallLimitMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[search_tool, database_tool],
    middleware=[
        # Global limit
        ToolCallLimitMiddleware(thread_limit=20, run_limit=10),
        # Tool-specific limit
        ToolCallLimitMiddleware(
            tool_name="search",
            thread_limit=5,
            run_limit=3,
        ),
    ],
)

Watch this video guide demonstrating Tool Call Limit middleware behavior.

Configuration options​tool_namestringName of specific tool to limit. If not provided, limits apply to all tools globally.​thread_limitnumberMaximum tool calls across all runs in a thread (conversation). Persists across multiple invocations with the same thread ID. Requires a checkpointer to maintain state. None means no thread limit.​run_limitnumberMaximum tool calls per single invocation (one user message → response cycle). Resets with each new user message. None means no run limit.Note: At least one of thread_limit or run_limit must be specified.​exit_behaviorstringdefault:"continue"Behavior when limit is reached:
'continue' (default) - Block exceeded tool calls with error messages, let other tools and the model continue. The model decides when to end based on the error messages.
'error' - Raise a ToolCallLimitExceededError exception, stopping execution immediately
'end' - Stop execution immediately with a ToolMessage and AI message for the exceeded tool call. Only works when limiting a single tool; raises NotImplementedError if other tools have pending calls.

Full exampleSpecify limits with:
Thread limit - Max calls across all runs in a conversation (requires checkpointer)
Run limit - Max calls per single invocation (resets each turn)
Exit behaviors:
'continue' (default) - Block exceeded calls with error messages, agent continues
'error' - Raise exception immediately
'end' - Stop with ToolMessage + AI message (single-tool scenarios only)
Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware

global_limiter = ToolCallLimitMiddleware(thread_limit=20, run_limit=10)
search_limiter = ToolCallLimitMiddleware(tool_name="search", thread_limit=5, run_limit=3)
database_limiter = ToolCallLimitMiddleware(tool_name="query_database", thread_limit=10)
strict_limiter = ToolCallLimitMiddleware(tool_name="scrape_webpage", run_limit=2, exit_behavior="error")

agent = create_agent(
    model="gpt-4o",
    tools=[search_tool, database_tool, scraper_tool],
    middleware=[global_limiter, search_limiter, database_limiter, strict_limiter],
)
```

##### ​Model fallback

Automatically fallback to alternative models when the primary model fails. Model fallback is useful for the following:

- Building resilient agents that handle model outages.
- Cost optimization by falling back to cheaper models.
- Provider redundancy across OpenAI, Anthropic, etc.
API reference: ModelFallbackMiddleware

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import ModelFallbackMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[],
    middleware=[
        ModelFallbackMiddleware(
            "gpt-4o-mini",
            "claude-3-5-sonnet-20241022",
        ),
    ],
)

Watch this video guide demonstrating Model Fallback middleware behavior.

Configuration options​first_modelstring | BaseChatModelrequiredFirst fallback model to try when the primary model fails. Can be a model identifier string (e.g., 'openai:gpt-4o-mini') or a BaseChatModel instance.​*additional_modelsstring | BaseChatModelAdditional fallback models to try in order if previous models fail
```

##### ​PII detection

Detect and handle Personally Identifiable Information (PII) in conversations using configurable strategies. PII detection is useful for the following:

- Healthcare and financial applications with compliance requirements.
- Customer service agents that need to sanitize logs.
- Any application handling sensitive user data.
API reference: PIIMiddleware

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import PIIMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[],
    middleware=[
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
        PIIMiddleware("credit_card", strategy="mask", apply_to_input=True),
    ],
)
```

###### ​Custom PII types

You can create custom PII types by providing a detector parameter. This allows you to detect patterns specific to your use case beyond the built-in types.

Three ways to create custom detectors:

- Regex pattern string - Simple pattern matching
- Custom function - Complex detection logic with validation
Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import PIIMiddleware
import re

# Method 1: Regex pattern string
agent1 = create_agent(
    model="gpt-4o",
    tools=[],
    middleware=[
        PIIMiddleware(
            "api_key",
            detector=r"sk-[a-zA-Z0-9]{32}",
            strategy="block",
        ),
    ],
)

# Method 2: Compiled regex pattern
agent2 = create_agent(
    model="gpt-4o",
    tools=[],
    middleware=[
        PIIMiddleware(
            "phone_number",
            detector=re.compile(r"\+?\d{1,3}[\s.-]?\d{3,4}[\s.-]?\d{4}"),
            strategy="mask",
        ),
    ],
)

# Method 3: Custom detector function
def detect_ssn(content: str) -> list[dict[str, str | int]]:
    """Detect SSN with validation.

    Returns a list of dictionaries with 'text', 'start', and 'end' keys.
    """
    import re
    matches = []
    pattern = r"\d{3}-\d{2}-\d{4}"
    for match in re.finditer(pattern, content):
        ssn = match.group(0)
        # Validate: first 3 digits shouldn't be 000, 666, or 900-999
        first_three = int(ssn[:3])
        if first_three not in [0, 666] and not (900 <= first_three <= 999):
            matches.append({
                "text": ssn,
                "start": match.start(),
                "end": match.end(),
            })
    return matches

agent3 = create_agent(
    model="gpt-4o",
    tools=[],
    middleware=[
        PIIMiddleware(
            "ssn",
            detector=detect_ssn,
            strategy="hash",
        ),
    ],
)

Custom detector function signature:

The detector function must accept a string (content) and return matches:

Returns a list of dictionaries with text, start, and end keys:

Copydef detector(content: str) -> list[dict[str, str | int]]:
    return [
        {"text": "matched_text", "start": 0, "end": 12},
        # ... more matches
    ]

For custom detectors:
Use regex strings for simple patterns
Use RegExp objects when you need flags (e.g., case-insensitive matching)
Use custom functions when you need validation logic beyond pattern matching
Custom functions give you full control over detection logic and can implement complex validation rules

Configuration options​pii_typestringrequiredType of PII to detect. Can be a built-in type (email, credit_card, ip, mac_address, url) or a custom type name.​strategystringdefault:"redact"How to handle detected PII. Options:
'block' - Raise exception when detected
'redact' - Replace with [REDACTED_{PII_TYPE}]
'mask' - Partially mask (e.g., ****-****-****-1234)
'hash' - Replace with deterministic hash
​detectorfunction | regexCustom detector function or regex pattern. If not provided, uses built-in detector for the PII type.​apply_to_inputbooleandefault:"True"Check user messages before model call​apply_to_outputbooleandefault:"False"Check AI messages after model call​apply_to_tool_resultsbooleandefault:"False"Check tool result messages after execution
```

##### ​To-do list

Equip agents with task planning and tracking capabilities for complex multi-step tasks. To-do lists are useful for the following:

- Complex multi-step tasks requiring coordination across multiple tools.
- Long-running operations where progress visibility is important.
This middleware automatically provides agents with a write_todos tool and system prompts to guide effective task planning.

API reference: TodoListMiddleware

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import TodoListMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[read_file, write_file, run_tests],
    middleware=[TodoListMiddleware()],
)

Watch this video guide demonstrating To-do List middleware behavior.

Configuration options​system_promptstringCustom system prompt for guiding todo usage. Uses built-in prompt if not specified.​tool_descriptionstringCustom description for the write_todos tool. Uses built-in description if not specified.
```

##### ​LLM tool selector

Use an LLM to intelligently select relevant tools before calling the main model. LLM tool selectors are useful for the following:

- Agents with many tools (10+) where most aren’t relevant per query.
- Reducing token usage by filtering irrelevant tools.
- Improving model focus and accuracy.
This middleware uses structured output to ask an LLM which tools are most relevant for the current query. The structured output schema defines the available tool names and descriptions. Model providers often add this structured output information to the system prompt behind the scenes.

API reference: LLMToolSelectorMiddleware

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import LLMToolSelectorMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[tool1, tool2, tool3, tool4, tool5, ...],
    middleware=[
        LLMToolSelectorMiddleware(
            model="gpt-4o-mini",
            max_tools=3,
            always_include=["search"],
        ),
    ],
)

Configuration options​modelstring | BaseChatModelModel for tool selection. Can be a model identifier string (e.g., 'openai:gpt-4o-mini') or a BaseChatModel instance. See init_chat_model for more information.Defaults to the agent’s main model.​system_promptstringInstructions for the selection model. Uses built-in prompt if not specified.​max_toolsnumberMaximum number of tools to select. If the model selects more, only the first max_tools will be used. No limit if not specified.​always_includelist[string]Tool names to always include regardless of selection. These do not count against the max_tools limit.
```

##### ​Tool retry

Automatically retry failed tool calls with configurable exponential backoff. Tool retry is useful for the following:

- Handling transient failures in external API calls.
- Improving reliability of network-dependent tools.
- Building resilient agents that gracefully handle temporary errors.
API reference: ToolRetryMiddleware

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import ToolRetryMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[search_tool, database_tool],
    middleware=[
        ToolRetryMiddleware(
            max_retries=3,
            backoff_factor=2.0,
            initial_delay=1.0,
        ),
    ],
)

Configuration options​max_retriesnumberdefault:"2"Maximum number of retry attempts after the initial call (3 total attempts with default)​toolslist[BaseTool | str]Optional list of tools or tool names to apply retry logic to. If None, applies to all tools.​retry_ontuple[type[Exception], ...] | callabledefault:"(Exception,)"Either a tuple of exception types to retry on, or a callable that takes an exception and returns True if it should be retried.​on_failurestring | callabledefault:"return_message"Behavior when all retries are exhausted. Options:
'return_message' - Return a ToolMessage with error details (allows LLM to handle failure)
'raise' - Re-raise the exception (stops agent execution)
Custom callable - Function that takes the exception and returns a string for the ToolMessage content
​backoff_factornumberdefault:"2.0"Multiplier for exponential backoff. Each retry waits initial_delay * (backoff_factor ** retry_number) seconds. Set to 0.0 for constant delay.​initial_delaynumberdefault:"1.0"Initial delay in seconds before first retry​max_delaynumberdefault:"60.0"Maximum delay in seconds between retries (caps exponential backoff growth)​jitterbooleandefault:"true"Whether to add random jitter (±25%) to delay to avoid thundering herd

Full exampleThe middleware automatically retries failed tool calls with exponential backoff.Key configuration:
max_retries - Number of retry attempts (default: 2)
backoff_factor - Multiplier for exponential backoff (default: 2.0)
initial_delay - Starting delay in seconds (default: 1.0)
max_delay - Cap on delay growth (default: 60.0)
jitter - Add random variation (default: True)
Failure handling:
on_failure='return_message' - Return error message
on_failure='raise' - Re-raise exception
Custom function - Function returning error message
Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[search_tool, database_tool, api_tool],
    middleware=[
        ToolRetryMiddleware(
            max_retries=3,
            backoff_factor=2.0,
            initial_delay=1.0,
            max_delay=60.0,
            jitter=True,
            tools=["api_tool"],
            retry_on=(ConnectionError, TimeoutError),
            on_failure="continue",
        ),
    ],
)
```

##### ​Model retry

Automatically retry failed model calls with configurable exponential backoff. Model retry is useful for the following:

- Handling transient failures in model API calls.
- Improving reliability of network-dependent model requests.
- Building resilient agents that gracefully handle temporary model errors.
API reference: ModelRetryMiddleware

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import ModelRetryMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[search_tool, database_tool],
    middleware=[
        ModelRetryMiddleware(
            max_retries=3,
            backoff_factor=2.0,
            initial_delay=1.0,
        ),
    ],
)

Configuration options​max_retriesnumberdefault:"2"Maximum number of retry attempts after the initial call (3 total attempts with default)​retry_ontuple[type[Exception], ...] | callabledefault:"(Exception,)"Either a tuple of exception types to retry on, or a callable that takes an exception and returns True if it should be retried.​on_failurestring | callabledefault:"continue"Behavior when all retries are exhausted. Options:
'continue' (default) - Return an AIMessage with error details, allowing the agent to potentially handle the failure gracefully
'error' - Re-raise the exception (stops agent execution)
Custom callable - Function that takes the exception and returns a string for the AIMessage content
​backoff_factornumberdefault:"2.0"Multiplier for exponential backoff. Each retry waits initial_delay * (backoff_factor ** retry_number) seconds. Set to 0.0 for constant delay.​initial_delaynumberdefault:"1.0"Initial delay in seconds before first retry​max_delaynumberdefault:"60.0"Maximum delay in seconds between retries (caps exponential backoff growth)​jitterbooleandefault:"true"Whether to add random jitter (±25%) to delay to avoid thundering herd

Full exampleThe middleware automatically retries failed model calls with exponential backoff.Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import ModelRetryMiddleware

# Basic usage with default settings (2 retries, exponential backoff)
agent = create_agent(
    model="gpt-4o",
    tools=[search_tool],
    middleware=[ModelRetryMiddleware()],
)

# Custom exception filtering
class TimeoutError(Exception):
    """Custom exception for timeout errors."""
    pass

class ConnectionError(Exception):
    """Custom exception for connection errors."""
    pass

# Retry specific exceptions only
retry = ModelRetryMiddleware(
    max_retries=4,
    retry_on=(TimeoutError, ConnectionError),
    backoff_factor=1.5,
)

def should_retry(error: Exception) -> bool:
    # Only retry on rate limit errors
    if isinstance(error, TimeoutError):
        return True
    # Or check for specific HTTP status codes
    if hasattr(error, "status_code"):
        return error.status_code in (429, 503)
    return False

retry_with_filter = ModelRetryMiddleware(
    max_retries=3,
    retry_on=should_retry,
)

# Return error message instead of raising
retry_continue = ModelRetryMiddleware(
    max_retries=4,
    on_failure="continue",  # Return AIMessage with error instead of raising
)

# Custom error message formatting
def format_error(error: Exception) -> str:
    return f"Model call failed: {error}. Please try again later."

retry_with_formatter = ModelRetryMiddleware(
    max_retries=4,
    on_failure=format_error,
)

# Constant backoff (no exponential growth)
constant_backoff = ModelRetryMiddleware(
    max_retries=5,
    backoff_factor=0.0,  # No exponential growth
    initial_delay=2.0,  # Always wait 2 seconds
)

# Raise exception on failure
strict_retry = ModelRetryMiddleware(
    max_retries=2,
    on_failure="error",  # Re-raise exception instead of returning message
)
```

##### ​LLM tool emulator

Emulate tool execution using an LLM for testing purposes, replacing actual tool calls with AI-generated responses. LLM tool emulators are useful for the following:

- Testing agent behavior without executing real tools.
- Developing agents when external tools are unavailable or expensive.
- Prototyping agent workflows before implementing actual tools.
API reference: LLMToolEmulator

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import LLMToolEmulator

agent = create_agent(
    model="gpt-4o",
    tools=[get_weather, search_database, send_email],
    middleware=[
        LLMToolEmulator(),  # Emulate all tools
    ],
)

Configuration options​toolslist[str | BaseTool]List of tool names (str) or BaseTool instances to emulate. If None (default), ALL tools will be emulated. If empty list [], no tools will be emulated. If array with tool names/instances, only those tools will be emulated.​modelstring | BaseChatModelModel to use for generating emulated tool responses. Can be a model identifier string (e.g., 'anthropic:claude-sonnet-4-5-20250929') or a BaseChatModel instance. Defaults to the agent’s model if not specified. See init_chat_model for more information.

Full exampleThe middleware uses an LLM to generate plausible responses for tool calls instead of executing the actual tools.Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import LLMToolEmulator
from langchain.tools import tool

@tool
def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    return f"Weather in {location}"

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email."""
    return "Email sent"

# Emulate all tools (default behavior)
agent = create_agent(
    model="gpt-4o",
    tools=[get_weather, send_email],
    middleware=[LLMToolEmulator()],
)

# Emulate specific tools only
agent2 = create_agent(
    model="gpt-4o",
    tools=[get_weather, send_email],
    middleware=[LLMToolEmulator(tools=["get_weather"])],
)

# Use custom model for emulation
agent4 = create_agent(
    model="gpt-4o",
    tools=[get_weather, send_email],
    middleware=[LLMToolEmulator(model="claude-sonnet-4-5-20250929")],
)
```

##### ​Context editing

Manage conversation context by clearing older tool call outputs when token limits are reached, while preserving recent results. This helps keep context windows manageable in long conversations with many tool calls. Context editing is useful for the following:

- Long conversations with many tool calls that exceed token limits
- Reducing token costs by removing older tool outputs that are no longer relevant
- Maintaining only the most recent N tool results in context
API reference: ContextEditingMiddleware, ClearToolUsesEdit

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import ContextEditingMiddleware, ClearToolUsesEdit

agent = create_agent(
    model="gpt-4o",
    tools=[],
    middleware=[
        ContextEditingMiddleware(
            edits=[
                ClearToolUsesEdit(
                    trigger=100000,
                    keep=3,
                ),
            ],
        ),
    ],
)

Configuration options​editslist[ContextEdit]default:"[ClearToolUsesEdit()]"List of ContextEdit strategies to apply​token_count_methodstringdefault:"approximate"Token counting method. Options: 'approximate' or 'model'ClearToolUsesEdit options:​triggernumberdefault:"100000"Token count that triggers the edit. When the conversation exceeds this token count, older tool outputs will be cleared.​clear_at_leastnumberdefault:"0"Minimum number of tokens to reclaim when the edit runs. If set to 0, clears as much as needed.​keepnumberdefault:"3"Number of most recent tool results that must be preserved. These will never be cleared.​clear_tool_inputsbooleandefault:"False"Whether to clear the originating tool call parameters on the AI message. When True, tool call arguments are replaced with empty objects.​exclude_toolslist[string]default:"()"List of tool names to exclude from clearing. These tools will never have their outputs cleared.​placeholderstringdefault:"[cleared]"Placeholder text inserted for cleared tool outputs. This replaces the original tool message content.

Full exampleThe middleware applies context editing strategies when token limits are reached. The most common strategy is ClearToolUsesEdit, which clears older tool results while preserving recent ones.How it works:
Monitor token count in conversation
When threshold is reached, clear older tool outputs
Keep most recent N tool results
Optionally preserve tool call arguments for context
Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import ContextEditingMiddleware, ClearToolUsesEdit

agent = create_agent(
    model="gpt-4o",
    tools=[search_tool, your_calculator_tool, database_tool],
    middleware=[
        ContextEditingMiddleware(
            edits=[
                ClearToolUsesEdit(
                    trigger=2000,
                    keep=3,
                    clear_tool_inputs=False,
                    exclude_tools=[],
                    placeholder="[cleared]",
                ),
            ],
        ),
    ],
)
```

##### ​Shell tool

Expose a persistent shell session to agents for command execution. Shell tool middleware is useful for the following:

- Agents that need to execute system commands
- Development and deployment automation tasks
- Testing and validation workflows
- File system operations and script execution
Security consideration: Use appropriate execution policies (HostExecutionPolicy, DockerExecutionPolicy, or CodexSandboxExecutionPolicy) to match your deployment’s security requirements.

Limitation: Persistent shell sessions do not currently work with interrupts (human-in-the-loop). We anticipate adding support for this in the future.

API reference: ShellToolMiddleware

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import (
    ShellToolMiddleware,
    HostExecutionPolicy,
)

agent = create_agent(
    model="gpt-4o",
    tools=[search_tool],
    middleware=[
        ShellToolMiddleware(
            workspace_root="/workspace",
            execution_policy=HostExecutionPolicy(),
        ),
    ],
)

Configuration options​workspace_rootstr | Path | NoneBase directory for the shell session. If omitted, a temporary directory is created when the agent starts and removed when it ends.​startup_commandstuple[str, ...] | list[str] | str | NoneOptional commands executed sequentially after the session starts​shutdown_commandstuple[str, ...] | list[str] | str | NoneOptional commands executed before the session shuts down​execution_policyBaseExecutionPolicy | NoneExecution policy controlling timeouts, output limits, and resource configuration. Options:
HostExecutionPolicy - Full host access (default); best for trusted environments where the agent already runs inside a container or VM
DockerExecutionPolicy - Launches a separate Docker container for each agent run, providing harder isolation
CodexSandboxExecutionPolicy - Reuses the Codex CLI sandbox for additional syscall/filesystem restrictions
​redaction_rulestuple[RedactionRule, ...] | list[RedactionRule] | NoneOptional redaction rules to sanitize command output before returning it to the model​tool_descriptionstr | NoneOptional override for the registered shell tool description​shell_commandSequence[str] | str | NoneOptional shell executable (string) or argument sequence used to launch the persistent session. Defaults to /bin/bash.​envMapping[str, Any] | NoneOptional environment variables to supply to the shell session. Values are coerced to strings before command execution.

Full exampleThe middleware provides a single persistent shell session that agents can use to execute commands sequentially.Execution policies:
HostExecutionPolicy (default) - Native execution with full host access
DockerExecutionPolicy - Isolated Docker container execution
CodexSandboxExecutionPolicy - Sandboxed execution via Codex CLI
Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import (
    ShellToolMiddleware,
    HostExecutionPolicy,
    DockerExecutionPolicy,
    RedactionRule,
)

# Basic shell tool with host execution
agent = create_agent(
    model="gpt-4o",
    tools=[search_tool],
    middleware=[
        ShellToolMiddleware(
            workspace_root="/workspace",
            execution_policy=HostExecutionPolicy(),
        ),
    ],
)

# Docker isolation with startup commands
agent_docker = create_agent(
    model="gpt-4o",
    tools=[],
    middleware=[
        ShellToolMiddleware(
            workspace_root="/workspace",
            startup_commands=["pip install requests", "export PYTHONPATH=/workspace"],
            execution_policy=DockerExecutionPolicy(
                image="python:3.11-slim",
                command_timeout=60.0,
            ),
        ),
    ],
)

# With output redaction
agent_redacted = create_agent(
    model="gpt-4o",
    tools=[],
    middleware=[
        ShellToolMiddleware(
            workspace_root="/workspace",
            redaction_rules=[
                RedactionRule(pii_type="api_key", detector=r"sk-[a-zA-Z0-9]{32}"),
            ],
        ),
    ],
)
```

##### ​File search

Provide Glob and Grep search tools over a filesystem. File search middleware is useful for the following:

- Code exploration and analysis
- Finding files by name patterns
- Searching code content with regex
- Large codebases where file discovery is needed
API reference: FilesystemFileSearchMiddleware

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import FilesystemFileSearchMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[],
    middleware=[
        FilesystemFileSearchMiddleware(
            root_path="/workspace",
            use_ripgrep=True,
        ),
    ],
)

Configuration options​root_pathstrrequiredRoot directory to search. All file operations are relative to this path.​use_ripgrepbooldefault:"True"Whether to use ripgrep for search. Falls back to Python regex if ripgrep is unavailable.​max_file_size_mbintdefault:"10"Maximum file size to search in MB. Files larger than this are skipped.

Full exampleThe middleware adds two search tools to agents:Glob tool - Fast file pattern matching:
Supports patterns like **/*.py, src/**/*.ts
Returns matching file paths sorted by modification time
Grep tool - Content search with regex:
Full regex syntax support
Filter by file patterns with include parameter
Three output modes: files_with_matches, content, count
Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import FilesystemFileSearchMiddleware
from langchain.messages import HumanMessage

agent = create_agent(
    model="gpt-4o",
    tools=[],
    middleware=[
        FilesystemFileSearchMiddleware(
            root_path="/workspace",
            use_ripgrep=True,
            max_file_size_mb=10,
        ),
    ],
)

# Agent can now use glob_search and grep_search tools
result = agent.invoke({
    "messages": [HumanMessage("Find all Python files containing 'async def'")]
})

# The agent will use:
# 1. glob_search(pattern="**/*.py") to find Python files
# 2. grep_search(pattern="async def", include="*.py") to find async functions
```

#### ​Provider-specific middleware

These middleware are optimized for specific LLM providers. See each provider’s documentation for full details and examples.

AnthropicPrompt caching, bash tool, text editor, memory, and file search middleware for Claude models.OpenAIContent moderation middleware for OpenAI models.

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.

#### Anthropic

Prompt caching, bash tool, text editor, memory, and file search middleware for Claude models.

#### OpenAI

Content moderation middleware for OpenAI models.


---

## Overview - Docs by LangChain {#doc-35}

**Source:** [https://docs.langchain.com/oss/python/langchain/middleware/overview](https://docs.langchain.com/oss/python/langchain/middleware/overview)

### Overview

Copy page

#### ​The agent loop

The core agent loop involves calling a model, letting it choose tools to execute, and then finishing when it calls no more tools:

Middleware exposes hooks before and after each of those steps:

#### ​Additional resources

Built-in middlewareExplore built-in middleware for common use cases.Custom middlewareBuild your own middleware with hooks and decorators.Middleware API referenceComplete API reference for middleware.Testing agentsTest your agents with LangSmith.

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.

#### Built-in middleware

Explore built-in middleware for common use cases.

#### Custom middleware

Build your own middleware with hooks and decorators.

#### Middleware API reference

Complete API reference for middleware.

#### Testing agents

Test your agents with LangSmith.


---

## Structured output - Docs by LangChain {#doc-36}

**Source:** [https://docs.langchain.com/oss/python/langchain/structured-output](https://docs.langchain.com/oss/python/langchain/structured-output)

### Structured output

Copy page

#### ​Response Format

Controls how the agent returns structured data:

- ToolStrategy[StructuredResponseT]: Uses tool calling for structured output
- ProviderStrategy[StructuredResponseT]: Uses provider-native structured output
- type[StructuredResponseT]: Schema type - automatically selects best strategy based on model capabilities
- None: No structured output
When a schema type is provided directly, LangChain automatically chooses:

- ProviderStrategy for models supporting native structured output (e.g. OpenAI, Anthropic, or Grok).
- ToolStrategy for all other models.
```
Support for native structured output features is read dynamically from the model’s profile data if using langchain>=1.1. If data are not available, use another condition or specify manually:Copycustom_profile = {
    "structured_output": True,
    # ...
}
model = init_chat_model("...", profile=custom_profile)
If tools are specified, the model must support simultaneous use of tools and structured output.

The structured response is returned in the structured_response key of the agent’s final state.
```

#### ​Provider strategy

Some model providers support structured output natively through their APIs (e.g. OpenAI, Grok, Gemini). This is the most reliable method when available.

To use this strategy, configure a ProviderStrategy:

Copyclass ProviderStrategy(Generic[SchemaT]):
    schema: type[SchemaT]
    strict: bool | None = None

The strict param requires langchain>=1.2.

​schemarequiredThe schema defining the structured output format. Supports:
Pydantic models: BaseModel subclasses with field validation
Dataclasses: Python dataclasses with type annotations
TypedDict: Typed dictionary classes
JSON Schema: Dictionary with JSON schema specification

​strictOptional boolean parameter to enable strict schema adherence. Supported by some providers (e.g., OpenAI and xAI). Defaults to None (disabled).

LangChain automatically uses ProviderStrategy when you pass a schema type directly to create_agent.response_format and the model supports native structured output:

Pydantic ModelDataclassTypedDictJSON SchemaCopyfrom pydantic import BaseModel, Field
```python
from langchain.agents import create_agent

class ContactInfo(BaseModel):
    """Contact information for a person."""
    name: str = Field(description="The name of the person")
    email: str = Field(description="The email address of the person")
    phone: str = Field(description="The phone number of the person")

agent = create_agent(
    model="gpt-5",
    response_format=ContactInfo  # Auto-selects ProviderStrategy
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Extract contact info from: John Doe, john@example.com, (555) 123-4567"}]
})

print(result["structured_response"])
# ContactInfo(name='John Doe', email='john@example.com', phone='(555) 123-4567')

Provider-native structured output provides high reliability and strict validation because the model provider enforces the schema. Use it when available.

If the provider natively supports structured output for your model choice, it is functionally equivalent to write response_format=ProductReview instead of response_format=ProviderStrategy(ProductReview). In either case, if structured output is not supported, the agent will fall back to a tool calling strategy.
```

#### ​Tool calling strategy

For models that don’t support native structured output, LangChain uses tool calling to achieve the same result. This works with all models that support tool calling, which is most modern models.

To use this strategy, configure a ToolStrategy:

Copyclass ToolStrategy(Generic[SchemaT]):
    schema: type[SchemaT]
    tool_message_content: str | None
    handle_errors: Union[
        bool,
        str,
        type[Exception],
        tuple[type[Exception], ...],
        Callable[[Exception], str],
    ]

​schemarequiredThe schema defining the structured output format. Supports:
Pydantic models: BaseModel subclasses with field validation
Dataclasses: Python dataclasses with type annotations
TypedDict: Typed dictionary classes
JSON Schema: Dictionary with JSON schema specification
Union types: Multiple schema options. The model will choose the most appropriate schema based on the context.

​tool_message_contentCustom content for the tool message returned when structured output is generated.
If not provided, defaults to a message showing the structured response data.

​handle_errorsError handling strategy for structured output validation failures. Defaults to True.
True: Catch all errors with default error template
str: Catch all errors with this custom message
type[Exception]: Only catch this exception type with default message
tuple[type[Exception], ...]: Only catch these exception types with default message
Callable[[Exception], str]: Custom function that returns error message
False: No retry, let exceptions propagate

Pydantic ModelDataclassTypedDictJSON SchemaUnion TypesCopyfrom pydantic import BaseModel, Field
```python
from typing import Literal
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

class ProductReview(BaseModel):
    """Analysis of a product review."""
    rating: int | None = Field(description="The rating of the product", ge=1, le=5)
    sentiment: Literal["positive", "negative"] = Field(description="The sentiment of the review")
    key_points: list[str] = Field(description="The key points of the review. Lowercase, 1-3 words each.")

agent = create_agent(
    model="gpt-5",
    tools=tools,
    response_format=ToolStrategy(ProductReview)
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Analyze this review: 'Great product: 5 out of 5 stars. Fast shipping, but expensive'"}]
})
result["structured_response"]
# ProductReview(rating=5, sentiment='positive', key_points=['fast shipping', 'expensive'])
```

##### ​Custom tool message content

The tool_message_content parameter allows you to customize the message that appears in the conversation history when structured output is generated:

Copyfrom pydantic import BaseModel, Field
```python
from typing import Literal
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

class MeetingAction(BaseModel):
    """Action items extracted from a meeting transcript."""
    task: str = Field(description="The specific task to be completed")
    assignee: str = Field(description="Person responsible for the task")
    priority: Literal["low", "medium", "high"] = Field(description="Priority level")

agent = create_agent(
    model="gpt-5",
    tools=[],
    response_format=ToolStrategy(
        schema=MeetingAction,
        tool_message_content="Action item captured and added to meeting notes!"
    )
)

agent.invoke({
    "messages": [{"role": "user", "content": "From our meeting: Sarah needs to update the project timeline as soon as possible"}]
})

Copy================================ Human Message =================================

From our meeting: Sarah needs to update the project timeline as soon as possible
================================== Ai Message ==================================
Tool Calls:
  MeetingAction (call_1)
 Call ID: call_1
  Args:
    task: Update the project timeline
    assignee: Sarah
    priority: high
================================= Tool Message =================================
Name: MeetingAction

Action item captured and added to meeting notes!

Without tool_message_content, our final ToolMessage would be:

Copy================================= Tool Message =================================
Name: MeetingAction

Returning structured response: {'task': 'update the project timeline', 'assignee': 'Sarah', 'priority': 'high'}
```

##### ​Error handling

Models can make mistakes when generating structured output via tool calling. LangChain provides intelligent retry mechanisms to handle these errors automatically.

###### ​Multiple structured outputs error

When a model incorrectly calls multiple structured output tools, the agent provides error feedback in a ToolMessage and prompts the model to retry:

Copyfrom pydantic import BaseModel, Field
```python
from typing import Union
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

class ContactInfo(BaseModel):
    name: str = Field(description="Person's name")
    email: str = Field(description="Email address")

class EventDetails(BaseModel):
    event_name: str = Field(description="Name of the event")
    date: str = Field(description="Event date")

agent = create_agent(
    model="gpt-5",
    tools=[],
    response_format=ToolStrategy(Union[ContactInfo, EventDetails])  # Default: handle_errors=True
)

agent.invoke({
    "messages": [{"role": "user", "content": "Extract info: John Doe (john@email.com) is organizing Tech Conference on March 15th"}]
})

Copy================================ Human Message =================================

Extract info: John Doe (john@email.com) is organizing Tech Conference on March 15th
None
================================== Ai Message ==================================
Tool Calls:
  ContactInfo (call_1)
 Call ID: call_1
  Args:
    name: John Doe
    email: john@email.com
  EventDetails (call_2)
 Call ID: call_2
  Args:
    event_name: Tech Conference
    date: March 15th
================================= Tool Message =================================
Name: ContactInfo

Error: Model incorrectly returned multiple structured responses (ContactInfo, EventDetails) when only one is expected.
 Please fix your mistakes.
================================= Tool Message =================================
Name: EventDetails

Error: Model incorrectly returned multiple structured responses (ContactInfo, EventDetails) when only one is expected.
 Please fix your mistakes.
================================== Ai Message ==================================
Tool Calls:
  ContactInfo (call_3)
 Call ID: call_3
  Args:
    name: John Doe
    email: john@email.com
================================= Tool Message =================================
Name: ContactInfo

Returning structured response: {'name': 'John Doe', 'email': 'john@email.com'}
```

###### ​Schema validation error

When structured output doesn’t match the expected schema, the agent provides specific error feedback:

Copyfrom pydantic import BaseModel, Field
```python
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

class ProductRating(BaseModel):
    rating: int | None = Field(description="Rating from 1-5", ge=1, le=5)
    comment: str = Field(description="Review comment")

agent = create_agent(
    model="gpt-5",
    tools=[],
    response_format=ToolStrategy(ProductRating),  # Default: handle_errors=True
    system_prompt="You are a helpful assistant that parses product reviews. Do not make any field or value up."
)

agent.invoke({
    "messages": [{"role": "user", "content": "Parse this: Amazing product, 10/10!"}]
})

Copy================================ Human Message =================================

Parse this: Amazing product, 10/10!
================================== Ai Message ==================================
Tool Calls:
  ProductRating (call_1)
 Call ID: call_1
  Args:
    rating: 10
    comment: Amazing product
================================= Tool Message =================================
Name: ProductRating

Error: Failed to parse structured output for tool 'ProductRating': 1 validation error for ProductRating.rating
  Input should be less than or equal to 5 [type=less_than_equal, input_value=10, input_type=int].
 Please fix your mistakes.
================================== Ai Message ==================================
Tool Calls:
  ProductRating (call_2)
 Call ID: call_2
  Args:
    rating: 5
    comment: Amazing product
================================= Tool Message =================================
Name: ProductRating

Returning structured response: {'rating': 5, 'comment': 'Amazing product'}
```

###### ​Error handling strategies

You can customize how errors are handled using the handle_errors parameter:

Custom error message:

CopyToolStrategy(
    schema=ProductRating,
    handle_errors="Please provide a valid rating between 1-5 and include a comment."
)

If handle_errors is a string, the agent will always prompt the model to re-try with a fixed tool message:

Copy================================= Tool Message =================================
Name: ProductRating

Please provide a valid rating between 1-5 and include a comment.

Handle specific exceptions only:

CopyToolStrategy(
    schema=ProductRating,
    handle_errors=ValueError  # Only retry on ValueError, raise others
)

If handle_errors is an exception type, the agent will only retry (using the default error message) if the exception raised is the specified type. In all other cases, the exception will be raised.

Handle multiple exception types:

CopyToolStrategy(
    schema=ProductRating,
    handle_errors=(ValueError, TypeError)  # Retry on ValueError and TypeError
)

If handle_errors is a tuple of exceptions, the agent will only retry (using the default error message) if the exception raised is one of the specified types. In all other cases, the exception will be raised.

Custom error handler function:

Copy
```python
from langchain.agents.structured_output import StructuredOutputValidationError
from langchain.agents.structured_output import MultipleStructuredOutputsError

def custom_error_handler(error: Exception) -> str:
    if isinstance(error, StructuredOutputValidationError):
        return "There was an issue with the format. Try again."
    elif isinstance(error, MultipleStructuredOutputsError):
        return "Multiple structured outputs were returned. Pick the most relevant one."
    else:
        return f"Error: {str(error)}"

agent = create_agent(
    model="gpt-5",
    tools=[],
    response_format=ToolStrategy(
                        schema=Union[ContactInfo, EventDetails],
                        handle_errors=custom_error_handler
                    )  # Default: handle_errors=True
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Extract info: John Doe (john@email.com) is organizing Tech Conference on March 15th"}]
})

for msg in result['messages']:
    # If message is actually a ToolMessage object (not a dict), check its class name
    if type(msg).__name__ == "ToolMessage":
        print(msg.content)
    # If message is a dictionary or you want a fallback
    elif isinstance(msg, dict) and msg.get('tool_call_id'):
        print(msg['content'])

On StructuredOutputValidationError:

Copy================================= Tool Message =================================
Name: ToolStrategy

There was an issue with the format. Try again.

On MultipleStructuredOutputsError:

Copy================================= Tool Message =================================
Name: ToolStrategy

Multiple structured outputs were returned. Pick the most relevant one.

On other errors:

Copy================================= Tool Message =================================
Name: ToolStrategy

Error: <error message>

No error handling:

Copyresponse_format = ToolStrategy(
    schema=ProductRating,
    handle_errors=False  # All errors raised
)

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```


---

## Short-term memory - Docs by LangChain {#doc-37}

**Source:** [https://docs.langchain.com/oss/python/langchain/short-term-memory](https://docs.langchain.com/oss/python/langchain/short-term-memory)

### Short-term memory

Copy page

#### ​Overview

Memory is a system that remembers information about previous interactions. For AI agents, memory is crucial because it lets them remember previous interactions, learn from feedback, and adapt to user preferences. As agents tackle more complex tasks with numerous user interactions, this capability becomes essential for both efficiency and user satisfaction.

Short term memory lets your application remember previous interactions within a single thread or conversation.

A thread organizes multiple interactions in a session, similar to the way email groups messages in a single conversation.

Conversation history is the most common form of short-term memory. Long conversations pose a challenge to today’s LLMs; a full history may not fit inside an LLM’s context window, resulting in an context loss or errors.

Even if your model supports the full context length, most LLMs still perform poorly over long contexts. They get “distracted” by stale or off-topic content, all while suffering from slower response times and higher costs.

Chat models accept context using messages, which include instructions (a system message) and inputs (human messages). In chat applications, messages alternate between human inputs and model responses, resulting in a list of messages that grows longer over time. Because context windows are limited, many applications can benefit from using techniques to remove or “forget” stale information.

#### ​Usage

To add short-term memory (thread-level persistence) to an agent, you need to specify a checkpointer when creating an agent.

LangChain’s agent manages short-term memory as a part of your agent’s state.By storing these in the graph’s state, the agent can access the full context for a given conversation while maintaining separation between different threads.State is persisted to a database (or memory) using a checkpointer so the thread can be resumed at any time.Short-term memory updates when the agent is invoked or a step (like a tool call) is completed, and the state is read at the start of each step.

Copyfrom langchain.agents import create_agent
```python
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    "gpt-5",
    tools=[get_user_info],
    checkpointer=InMemorySaver(),
)

agent.invoke(
    {"messages": [{"role": "user", "content": "Hi! My name is Bob."}]},
    {"configurable": {"thread_id": "1"}},
)
```

##### ​In production

In production, use a checkpointer backed by a database:

Copypip install langgraph-checkpoint-postgres

Copyfrom langchain.agents import create_agent

```python
from langgraph.checkpoint.postgres import PostgresSaver

DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup() # auto create tables in PostgresSql
    agent = create_agent(
        "gpt-5",
        tools=[get_user_info],
        checkpointer=checkpointer,
    )
```

#### ​Customizing agent memory

By default, agents use AgentState to manage short term memory, specifically the conversation history via a messages key.

You can extend AgentState to add additional fields. Custom state schemas are passed to create_agent using the state_schema parameter.

Copyfrom langchain.agents import create_agent, AgentState
```python
from langgraph.checkpoint.memory import InMemorySaver

class CustomAgentState(AgentState):
    user_id: str
    preferences: dict

agent = create_agent(
    "gpt-5",
    tools=[get_user_info],
    state_schema=CustomAgentState,
    checkpointer=InMemorySaver(),
)

# Custom state can be passed in invoke
result = agent.invoke(
    {
        "messages": [{"role": "user", "content": "Hello"}],
        "user_id": "user_123",
        "preferences": {"theme": "dark"}
    },
    {"configurable": {"thread_id": "1"}})
```

#### ​Common patterns

With short-term memory enabled, long conversations can exceed the LLM’s context window. Common solutions are:

Trim messagesRemove first or last N messages (before calling LLM)Delete messagesDelete messages from LangGraph state permanentlySummarize messagesSummarize earlier messages in the history and replace them with a summaryCustom strategiesCustom strategies (e.g., message filtering, etc.)

This allows the agent to keep track of the conversation without exceeding the LLM’s context window.

​Trim messages

Most LLMs have a maximum supported context window (denominated in tokens).

One way to decide when to truncate messages is to count the tokens in the message history and truncate whenever it approaches that limit. If you’re using LangChain, you can use the trim messages utility and specify the number of tokens to keep from the list, as well as the strategy (e.g., keep the last max_tokens) to use for handling the boundary.

To trim message history in an agent, use the @before_model middleware decorator:

Copyfrom langchain.messages import RemoveMessage
```python
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import before_model
from langgraph.runtime import Runtime
from langchain_core.runnables import RunnableConfig
from typing import Any

@before_model
def trim_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Keep only the last few messages to fit context window."""
    messages = state["messages"]

    if len(messages) <= 3:
        return None  # No changes needed

    first_msg = messages[0]
    recent_messages = messages[-3:] if len(messages) % 2 == 0 else messages[-4:]
    new_messages = [first_msg] + recent_messages

    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *new_messages
        ]
    }

agent = create_agent(
    your_model_here,
    tools=your_tools_here,
    middleware=[trim_messages],
    checkpointer=InMemorySaver(),
)

config: RunnableConfig = {"configurable": {"thread_id": "1"}}

agent.invoke({"messages": "hi, my name is bob"}, config)
agent.invoke({"messages": "write a short poem about cats"}, config)
agent.invoke({"messages": "now do the same but for dogs"}, config)
final_response = agent.invoke({"messages": "what's my name?"}, config)

final_response["messages"][-1].pretty_print()
"""
================================== Ai Message ==================================

Your name is Bob. You told me that earlier.
If you'd like me to call you a nickname or use a different name, just say the word.
"""

​Delete messages

You can delete messages from the graph state to manage the message history.

This is useful when you want to remove specific messages or clear the entire message history.

To delete messages from the graph state, you can use the RemoveMessage.

For RemoveMessage to work, you need to use a state key with add_messages reducer.

The default AgentState provides this.

To remove specific messages:

Copyfrom langchain.messages import RemoveMessage

def delete_messages(state):
    messages = state["messages"]
    if len(messages) > 2:
        # remove the earliest two messages
        return {"messages": [RemoveMessage(id=m.id) for m in messages[:2]]}

To remove all messages:

Copyfrom langgraph.graph.message import REMOVE_ALL_MESSAGES

def delete_messages(state):
    return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)]}

When deleting messages, make sure that the resulting message history is valid. Check the limitations of the LLM provider you’re using. For example:
Some providers expect message history to start with a user message
Most providers require assistant messages with tool calls to be followed by corresponding tool result messages.

Copyfrom langchain.messages import RemoveMessage
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import after_model
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.runtime import Runtime
from langchain_core.runnables import RunnableConfig

@after_model
def delete_old_messages(state: AgentState, runtime: Runtime) -> dict | None:
    """Remove old messages to keep conversation manageable."""
    messages = state["messages"]
    if len(messages) > 2:
        # remove the earliest two messages
        return {"messages": [RemoveMessage(id=m.id) for m in messages[:2]]}
    return None

agent = create_agent(
    "gpt-5-nano",
    tools=[],
    system_prompt="Please be concise and to the point.",
    middleware=[delete_old_messages],
    checkpointer=InMemorySaver(),
)

config: RunnableConfig = {"configurable": {"thread_id": "1"}}

for event in agent.stream(
    {"messages": [{"role": "user", "content": "hi! I'm bob"}]},
    config,
    stream_mode="values",
):
    print([(message.type, message.content) for message in event["messages"]])

for event in agent.stream(
    {"messages": [{"role": "user", "content": "what's my name?"}]},
    config,
    stream_mode="values",
):
    print([(message.type, message.content) for message in event["messages"]])

Copy[('human', "hi! I'm bob")]
[('human', "hi! I'm bob"), ('ai', 'Hi Bob! Nice to meet you. How can I help you today? I can answer questions, brainstorm ideas, draft text, explain things, or help with code.')]
[('human', "hi! I'm bob"), ('ai', 'Hi Bob! Nice to meet you. How can I help you today? I can answer questions, brainstorm ideas, draft text, explain things, or help with code.'), ('human', "what's my name?")]
[('human', "hi! I'm bob"), ('ai', 'Hi Bob! Nice to meet you. How can I help you today? I can answer questions, brainstorm ideas, draft text, explain things, or help with code.'), ('human', "what's my name?"), ('ai', 'Your name is Bob. How can I help you today, Bob?')]
[('human', "what's my name?"), ('ai', 'Your name is Bob. How can I help you today, Bob?')]

​Summarize messages

The problem with trimming or removing messages, as shown above, is that you may lose information from culling of the message queue.
Because of this, some applications benefit from a more sophisticated approach of summarizing the message history using a chat model.

To summarize message history in an agent, use the built-in SummarizationMiddleware:

Copyfrom langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig

checkpointer = InMemorySaver()

agent = create_agent(
    model="gpt-4o",
    tools=[],
    middleware=[
        SummarizationMiddleware(
            model="gpt-4o-mini",
            trigger=("tokens", 4000),
            keep=("messages", 20)
        )
    ],
    checkpointer=checkpointer,
)

config: RunnableConfig = {"configurable": {"thread_id": "1"}}
agent.invoke({"messages": "hi, my name is bob"}, config)
agent.invoke({"messages": "write a short poem about cats"}, config)
agent.invoke({"messages": "now do the same but for dogs"}, config)
final_response = agent.invoke({"messages": "what's my name?"}, config)

final_response["messages"][-1].pretty_print()
"""
================================== Ai Message ==================================

Your name is Bob!
"""

See SummarizationMiddleware for more configuration options.

​Access memory

You can access and modify the short-term memory (state) of an agent in several ways:

​Tools

​Read short-term memory in a tool

Access short term memory (state) in a tool using the ToolRuntime parameter.

The tool_runtime parameter is hidden from the tool signature (so the model doesn’t see it), but the tool can access the state through it.

Copyfrom langchain.agents import create_agent, AgentState
from langchain.tools import tool, ToolRuntime

class CustomState(AgentState):
    user_id: str

@tool
def get_user_info(
    runtime: ToolRuntime
) -> str:
    """Look up user info."""
    user_id = runtime.state["user_id"]
    return "User is John Smith" if user_id == "user_123" else "Unknown user"

agent = create_agent(
    model="gpt-5-nano",
    tools=[get_user_info],
    state_schema=CustomState,
)

result = agent.invoke({
    "messages": "look up user information",
    "user_id": "user_123"
})
print(result["messages"][-1].content)
# > User is John Smith.

​Write short-term memory from tools

To modify the agent’s short-term memory (state) during execution, you can return state updates directly from the tools.

This is useful for persisting intermediate results or making information accessible to subsequent tools or prompts.

Copyfrom langchain.tools import tool, ToolRuntime
from langchain_core.runnables import RunnableConfig
from langchain.messages import ToolMessage
from langchain.agents import create_agent, AgentState
from langgraph.types import Command
from pydantic import BaseModel

class CustomState(AgentState):
    user_name: str

class CustomContext(BaseModel):
    user_id: str

@tool
def update_user_info(
    runtime: ToolRuntime[CustomContext, CustomState],
) -> Command:
    """Look up and update user info."""
    user_id = runtime.context.user_id
    name = "John Smith" if user_id == "user_123" else "Unknown user"
    return Command(update={
        "user_name": name,
        # update the message history
        "messages": [
            ToolMessage(
                "Successfully looked up user information",
                tool_call_id=runtime.tool_call_id
            )
        ]
    })

@tool
def greet(
    runtime: ToolRuntime[CustomContext, CustomState]
) -> str | Command:
    """Use this to greet the user once you found their info."""
    user_name = runtime.state.get("user_name", None)
    if user_name is None:
       return Command(update={
            "messages": [
                ToolMessage(
                    "Please call the 'update_user_info' tool it will get and update the user's name.",
                    tool_call_id=runtime.tool_call_id
                )
            ]
        })
    return f"Hello {user_name}!"

agent = create_agent(
    model="gpt-5-nano",
    tools=[update_user_info, greet],
    state_schema=CustomState,
    context_schema=CustomContext,
)

agent.invoke(
    {"messages": [{"role": "user", "content": "greet the user"}]},
    context=CustomContext(user_id="user_123"),
)

​Prompt

Access short term memory (state) in middleware to create dynamic prompts based on conversation history or custom state fields.

Copyfrom langchain.agents import create_agent
from typing import TypedDict
from langchain.agents.middleware import dynamic_prompt, ModelRequest

class CustomContext(TypedDict):
    user_name: str

def get_weather(city: str) -> str:
    """Get the weather in a city."""
    return f"The weather in {city} is always sunny!"

@dynamic_prompt
def dynamic_system_prompt(request: ModelRequest) -> str:
    user_name = request.runtime.context["user_name"]
    system_prompt = f"You are a helpful assistant. Address the user as {user_name}."
    return system_prompt

agent = create_agent(
    model="gpt-5-nano",
    tools=[get_weather],
    middleware=[dynamic_system_prompt],
    context_schema=CustomContext,
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
    context=CustomContext(user_name="John Smith"),
)
for msg in result["messages"]:
    msg.pretty_print()

OutputCopy================================ Human Message =================================

What is the weather in SF?
================================== Ai Message ==================================
Tool Calls:
  get_weather (call_WFQlOGn4b2yoJrv7cih342FG)
 Call ID: call_WFQlOGn4b2yoJrv7cih342FG
  Args:
    city: San Francisco
================================= Tool Message =================================
Name: get_weather

The weather in San Francisco is always sunny!
================================== Ai Message ==================================

Hi John Smith, the weather in San Francisco is always sunny!

​Before model

Access short term memory (state) in @before_model middleware to process messages before model calls.

Copyfrom langchain.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import before_model
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from typing import Any

@before_model
def trim_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Keep only the last few messages to fit context window."""
    messages = state["messages"]

    if len(messages) <= 3:
        return None  # No changes needed

    first_msg = messages[0]
    recent_messages = messages[-3:] if len(messages) % 2 == 0 else messages[-4:]
    new_messages = [first_msg] + recent_messages

    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *new_messages
        ]
    }

agent = create_agent(
    "gpt-5-nano",
    tools=[],
    middleware=[trim_messages],
    checkpointer=InMemorySaver()
)

config: RunnableConfig = {"configurable": {"thread_id": "1"}}

agent.invoke({"messages": "hi, my name is bob"}, config)
agent.invoke({"messages": "write a short poem about cats"}, config)
agent.invoke({"messages": "now do the same but for dogs"}, config)
final_response = agent.invoke({"messages": "what's my name?"}, config)

final_response["messages"][-1].pretty_print()
"""
================================== Ai Message ==================================

Your name is Bob. You told me that earlier.
If you'd like me to call you a nickname or use a different name, just say the word.
"""

​After model

Access short term memory (state) in @after_model middleware to process messages after model calls.

Copyfrom langchain.messages import RemoveMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import after_model
from langgraph.runtime import Runtime

@after_model
def validate_response(state: AgentState, runtime: Runtime) -> dict | None:
    """Remove messages containing sensitive words."""
    STOP_WORDS = ["password", "secret"]
    last_message = state["messages"][-1]
    if any(word in last_message.content for word in STOP_WORDS):
        return {"messages": [RemoveMessage(id=last_message.id)]}
    return None

agent = create_agent(
    model="gpt-5-nano",
    tools=[],
    middleware=[validate_response],
    checkpointer=InMemorySaver(),
)

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```

#### Trim messages

Remove first or last N messages (before calling LLM)

#### Delete messages

Delete messages from LangGraph state permanently

#### Summarize messages

Summarize earlier messages in the history and replace them with a summary

#### Custom strategies

Custom strategies (e.g., message filtering, etc.)

##### ​Trim messages

Most LLMs have a maximum supported context window (denominated in tokens).

One way to decide when to truncate messages is to count the tokens in the message history and truncate whenever it approaches that limit. If you’re using LangChain, you can use the trim messages utility and specify the number of tokens to keep from the list, as well as the strategy (e.g., keep the last max_tokens) to use for handling the boundary.

To trim message history in an agent, use the @before_model middleware decorator:

Copyfrom langchain.messages import RemoveMessage
```python
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import before_model
from langgraph.runtime import Runtime
from langchain_core.runnables import RunnableConfig
from typing import Any

@before_model
def trim_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Keep only the last few messages to fit context window."""
    messages = state["messages"]

    if len(messages) <= 3:
        return None  # No changes needed

    first_msg = messages[0]
    recent_messages = messages[-3:] if len(messages) % 2 == 0 else messages[-4:]
    new_messages = [first_msg] + recent_messages

    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *new_messages
        ]
    }

agent = create_agent(
    your_model_here,
    tools=your_tools_here,
    middleware=[trim_messages],
    checkpointer=InMemorySaver(),
)

config: RunnableConfig = {"configurable": {"thread_id": "1"}}

agent.invoke({"messages": "hi, my name is bob"}, config)
agent.invoke({"messages": "write a short poem about cats"}, config)
agent.invoke({"messages": "now do the same but for dogs"}, config)
final_response = agent.invoke({"messages": "what's my name?"}, config)

final_response["messages"][-1].pretty_print()
"""
================================== Ai Message ==================================

Your name is Bob. You told me that earlier.
If you'd like me to call you a nickname or use a different name, just say the word.
"""
```

##### ​Delete messages

You can delete messages from the graph state to manage the message history.

This is useful when you want to remove specific messages or clear the entire message history.

To delete messages from the graph state, you can use the RemoveMessage.

For RemoveMessage to work, you need to use a state key with add_messages reducer.

The default AgentState provides this.

To remove specific messages:

Copyfrom langchain.messages import RemoveMessage

```python
def delete_messages(state):
    messages = state["messages"]
    if len(messages) > 2:
        # remove the earliest two messages
        return {"messages": [RemoveMessage(id=m.id) for m in messages[:2]]}

To remove all messages:

Copyfrom langgraph.graph.message import REMOVE_ALL_MESSAGES

def delete_messages(state):
    return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)]}

When deleting messages, make sure that the resulting message history is valid. Check the limitations of the LLM provider you’re using. For example:
Some providers expect message history to start with a user message
Most providers require assistant messages with tool calls to be followed by corresponding tool result messages.

Copyfrom langchain.messages import RemoveMessage
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import after_model
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.runtime import Runtime
from langchain_core.runnables import RunnableConfig

@after_model
def delete_old_messages(state: AgentState, runtime: Runtime) -> dict | None:
    """Remove old messages to keep conversation manageable."""
    messages = state["messages"]
    if len(messages) > 2:
        # remove the earliest two messages
        return {"messages": [RemoveMessage(id=m.id) for m in messages[:2]]}
    return None

agent = create_agent(
    "gpt-5-nano",
    tools=[],
    system_prompt="Please be concise and to the point.",
    middleware=[delete_old_messages],
    checkpointer=InMemorySaver(),
)

config: RunnableConfig = {"configurable": {"thread_id": "1"}}

for event in agent.stream(
    {"messages": [{"role": "user", "content": "hi! I'm bob"}]},
    config,
    stream_mode="values",
):
    print([(message.type, message.content) for message in event["messages"]])

for event in agent.stream(
    {"messages": [{"role": "user", "content": "what's my name?"}]},
    config,
    stream_mode="values",
):
    print([(message.type, message.content) for message in event["messages"]])

Copy[('human', "hi! I'm bob")]
[('human', "hi! I'm bob"), ('ai', 'Hi Bob! Nice to meet you. How can I help you today? I can answer questions, brainstorm ideas, draft text, explain things, or help with code.')]
[('human', "hi! I'm bob"), ('ai', 'Hi Bob! Nice to meet you. How can I help you today? I can answer questions, brainstorm ideas, draft text, explain things, or help with code.'), ('human', "what's my name?")]
[('human', "hi! I'm bob"), ('ai', 'Hi Bob! Nice to meet you. How can I help you today? I can answer questions, brainstorm ideas, draft text, explain things, or help with code.'), ('human', "what's my name?"), ('ai', 'Your name is Bob. How can I help you today, Bob?')]
[('human', "what's my name?"), ('ai', 'Your name is Bob. How can I help you today, Bob?')]
```

##### ​Summarize messages

The problem with trimming or removing messages, as shown above, is that you may lose information from culling of the message queue.
Because of this, some applications benefit from a more sophisticated approach of summarizing the message history using a chat model.

To summarize message history in an agent, use the built-in SummarizationMiddleware:

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig

checkpointer = InMemorySaver()

agent = create_agent(
    model="gpt-4o",
    tools=[],
    middleware=[
        SummarizationMiddleware(
            model="gpt-4o-mini",
            trigger=("tokens", 4000),
            keep=("messages", 20)
        )
    ],
    checkpointer=checkpointer,
)

config: RunnableConfig = {"configurable": {"thread_id": "1"}}
agent.invoke({"messages": "hi, my name is bob"}, config)
agent.invoke({"messages": "write a short poem about cats"}, config)
agent.invoke({"messages": "now do the same but for dogs"}, config)
final_response = agent.invoke({"messages": "what's my name?"}, config)

final_response["messages"][-1].pretty_print()
"""
================================== Ai Message ==================================

Your name is Bob!
"""

See SummarizationMiddleware for more configuration options.
```

#### ​Access memory

You can access and modify the short-term memory (state) of an agent in several ways:

##### ​Tools

###### ​Read short-term memory in a tool

Access short term memory (state) in a tool using the ToolRuntime parameter.

The tool_runtime parameter is hidden from the tool signature (so the model doesn’t see it), but the tool can access the state through it.

Copyfrom langchain.agents import create_agent, AgentState
```python
from langchain.tools import tool, ToolRuntime

class CustomState(AgentState):
    user_id: str

@tool
def get_user_info(
    runtime: ToolRuntime
) -> str:
    """Look up user info."""
    user_id = runtime.state["user_id"]
    return "User is John Smith" if user_id == "user_123" else "Unknown user"

agent = create_agent(
    model="gpt-5-nano",
    tools=[get_user_info],
    state_schema=CustomState,
)

result = agent.invoke({
    "messages": "look up user information",
    "user_id": "user_123"
})
print(result["messages"][-1].content)
# > User is John Smith.
```

###### ​Write short-term memory from tools

To modify the agent’s short-term memory (state) during execution, you can return state updates directly from the tools.

This is useful for persisting intermediate results or making information accessible to subsequent tools or prompts.

Copyfrom langchain.tools import tool, ToolRuntime
```python
from langchain_core.runnables import RunnableConfig
from langchain.messages import ToolMessage
from langchain.agents import create_agent, AgentState
from langgraph.types import Command
from pydantic import BaseModel

class CustomState(AgentState):
    user_name: str

class CustomContext(BaseModel):
    user_id: str

@tool
def update_user_info(
    runtime: ToolRuntime[CustomContext, CustomState],
) -> Command:
    """Look up and update user info."""
    user_id = runtime.context.user_id
    name = "John Smith" if user_id == "user_123" else "Unknown user"
    return Command(update={
        "user_name": name,
        # update the message history
        "messages": [
            ToolMessage(
                "Successfully looked up user information",
                tool_call_id=runtime.tool_call_id
            )
        ]
    })

@tool
def greet(
    runtime: ToolRuntime[CustomContext, CustomState]
) -> str | Command:
    """Use this to greet the user once you found their info."""
    user_name = runtime.state.get("user_name", None)
    if user_name is None:
       return Command(update={
            "messages": [
                ToolMessage(
                    "Please call the 'update_user_info' tool it will get and update the user's name.",
                    tool_call_id=runtime.tool_call_id
                )
            ]
        })
    return f"Hello {user_name}!"

agent = create_agent(
    model="gpt-5-nano",
    tools=[update_user_info, greet],
    state_schema=CustomState,
    context_schema=CustomContext,
)

agent.invoke(
    {"messages": [{"role": "user", "content": "greet the user"}]},
    context=CustomContext(user_id="user_123"),
)
```

##### ​Prompt

Access short term memory (state) in middleware to create dynamic prompts based on conversation history or custom state fields.

Copyfrom langchain.agents import create_agent
```python
from typing import TypedDict
from langchain.agents.middleware import dynamic_prompt, ModelRequest

class CustomContext(TypedDict):
    user_name: str

def get_weather(city: str) -> str:
    """Get the weather in a city."""
    return f"The weather in {city} is always sunny!"

@dynamic_prompt
def dynamic_system_prompt(request: ModelRequest) -> str:
    user_name = request.runtime.context["user_name"]
    system_prompt = f"You are a helpful assistant. Address the user as {user_name}."
    return system_prompt

agent = create_agent(
    model="gpt-5-nano",
    tools=[get_weather],
    middleware=[dynamic_system_prompt],
    context_schema=CustomContext,
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
    context=CustomContext(user_name="John Smith"),
)
for msg in result["messages"]:
    msg.pretty_print()

OutputCopy================================ Human Message =================================

What is the weather in SF?
================================== Ai Message ==================================
Tool Calls:
  get_weather (call_WFQlOGn4b2yoJrv7cih342FG)
 Call ID: call_WFQlOGn4b2yoJrv7cih342FG
  Args:
    city: San Francisco
================================= Tool Message =================================
Name: get_weather

The weather in San Francisco is always sunny!
================================== Ai Message ==================================

Hi John Smith, the weather in San Francisco is always sunny!
```

##### ​Before model

Access short term memory (state) in @before_model middleware to process messages before model calls.

Copyfrom langchain.messages import RemoveMessage
```python
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import before_model
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from typing import Any

@before_model
def trim_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Keep only the last few messages to fit context window."""
    messages = state["messages"]

    if len(messages) <= 3:
        return None  # No changes needed

    first_msg = messages[0]
    recent_messages = messages[-3:] if len(messages) % 2 == 0 else messages[-4:]
    new_messages = [first_msg] + recent_messages

    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *new_messages
        ]
    }

agent = create_agent(
    "gpt-5-nano",
    tools=[],
    middleware=[trim_messages],
    checkpointer=InMemorySaver()
)

config: RunnableConfig = {"configurable": {"thread_id": "1"}}

agent.invoke({"messages": "hi, my name is bob"}, config)
agent.invoke({"messages": "write a short poem about cats"}, config)
agent.invoke({"messages": "now do the same but for dogs"}, config)
final_response = agent.invoke({"messages": "what's my name?"}, config)

final_response["messages"][-1].pretty_print()
"""
================================== Ai Message ==================================

Your name is Bob. You told me that earlier.
If you'd like me to call you a nickname or use a different name, just say the word.
"""
```

##### ​After model

Access short term memory (state) in @after_model middleware to process messages after model calls.

Copyfrom langchain.messages import RemoveMessage
```python
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import after_model
from langgraph.runtime import Runtime

@after_model
def validate_response(state: AgentState, runtime: Runtime) -> dict | None:
    """Remove messages containing sensitive words."""
    STOP_WORDS = ["password", "secret"]
    last_message = state["messages"][-1]
    if any(word in last_message.content for word in STOP_WORDS):
        return {"messages": [RemoveMessage(id=last_message.id)]}
    return None

agent = create_agent(
    model="gpt-5-nano",
    tools=[],
    middleware=[validate_response],
    checkpointer=InMemorySaver(),
)

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```


---

## Tools - Docs by LangChain {#doc-38}

**Source:** [https://docs.langchain.com/oss/python/langchain/tools](https://docs.langchain.com/oss/python/langchain/tools)

### Tools

Copy page

#### ​Create tools

##### ​Basic tool definition

The simplest way to create a tool is with the @tool decorator. By default, the function’s docstring becomes the tool’s description that helps the model understand when to use it:

Copyfrom langchain.tools import tool

```python
@tool
def search_database(query: str, limit: int = 10) -> str:
    """Search the customer database for records matching the query.

    Args:
        query: Search terms to look for
        limit: Maximum number of results to return
    """
    return f"Found {limit} results for '{query}'"

Type hints are required as they define the tool’s input schema. The docstring should be informative and concise to help the model understand the tool’s purpose.

Server-side tool useSome chat models (e.g., OpenAI, Anthropic, and Gemini) feature built-in tools that are executed server-side, such as web search and code interpreters. Refer to the provider overview to learn how to access these tools with your specific chat model.
```

##### ​Customize tool properties

###### ​Custom tool name

By default, the tool name comes from the function name. Override it when you need something more descriptive:

Copy@tool("web_search")  # Custom name
```python
def search(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

print(search.name)  # web_search
```

###### ​Custom tool description

Override the auto-generated tool description for clearer model guidance:

Copy@tool("calculator", description="Performs arithmetic calculations. Use this for any math problems.")
```python
def calc(expression: str) -> str:
    """Evaluate mathematical expressions."""
    return str(eval(expression))
```

##### ​Advanced schema definition

Define complex inputs with Pydantic models or JSON schemas:

Pydantic modelJSON SchemaCopyfrom pydantic import BaseModel, Field
```python
from typing import Literal

class WeatherInput(BaseModel):
    """Input for weather queries."""
    location: str = Field(description="City name or coordinates")
    units: Literal["celsius", "fahrenheit"] = Field(
        default="celsius",
        description="Temperature unit preference"
    )
    include_forecast: bool = Field(
        default=False,
        description="Include 5-day forecast"
    )

@tool(args_schema=WeatherInput)
def get_weather(location: str, units: str = "celsius", include_forecast: bool = False) -> str:
    """Get current weather and optional forecast."""
    temp = 22 if units == "celsius" else 72
    result = f"Current weather in {location}: {temp} degrees {units[0].upper()}"
    if include_forecast:
        result += "\nNext 5 days: Sunny"
    return result
```

##### ​Reserved argument names

The following parameter names are reserved and cannot be used as tool arguments. Using these names will cause runtime errors.

Parameter namePurposeconfigReserved for passing RunnableConfig to tools internallyruntimeReserved for ToolRuntime parameter (accessing state, context, store)

To access runtime information, use the ToolRuntime parameter instead of naming your own arguments config or runtime.

#### ​Accessing Context

Why this matters: Tools are most powerful when they can access agent state, runtime context, and long-term memory. This enables tools to make context-aware decisions, personalize responses, and maintain information across conversations.Runtime context provides a way to inject dependencies (like database connections, user IDs, or configuration) into your tools at runtime, making them more testable and reusable.

Tools can access runtime information through the ToolRuntime parameter, which provides:

- State - Mutable data that flows through execution (e.g., messages, counters, custom fields)
- Context - Immutable configuration like user IDs, session details, or application-specific configuration
- Store - Persistent long-term memory across conversations
- Stream Writer - Stream custom updates as tools execute
- Config - RunnableConfig for the execution
- Tool Call ID - ID of the current tool call

##### ​ToolRuntime

Use ToolRuntime to access all runtime information in a single parameter. Simply add runtime: ToolRuntime to your tool signature, and it will be automatically injected without being exposed to the LLM.

ToolRuntime: A unified parameter that provides tools access to state, context, store, streaming, config, and tool call ID. This replaces the older pattern of using separate InjectedState, InjectedStore, get_runtime, and InjectedToolCallId annotations.The runtime automatically provides these capabilities to your tool functions without you having to pass them explicitly or use global state.

Accessing state:

Tools can access the current graph state using ToolRuntime:

Copyfrom langchain.tools import tool, ToolRuntime

# Access the current conversation state
```python
@tool
def summarize_conversation(
    runtime: ToolRuntime
) -> str:
    """Summarize the conversation so far."""
    messages = runtime.state["messages"]

    human_msgs = sum(1 for m in messages if m.__class__.__name__ == "HumanMessage")
    ai_msgs = sum(1 for m in messages if m.__class__.__name__ == "AIMessage")
    tool_msgs = sum(1 for m in messages if m.__class__.__name__ == "ToolMessage")

    return f"Conversation has {human_msgs} user messages, {ai_msgs} AI responses, and {tool_msgs} tool results"

# Access custom state fields
@tool
def get_user_preference(
    pref_name: str,
    runtime: ToolRuntime  # ToolRuntime parameter is not visible to the model
) -> str:
    """Get a user preference value."""
    preferences = runtime.state.get("user_preferences", {})
    return preferences.get(pref_name, "Not set")

The runtime parameter is hidden from the model. For the example above, the model only sees pref_name in the tool schema - runtime is not included in the request.

Updating state:

Use Command to update the agent’s state or control the graph’s execution flow:

Copyfrom langgraph.types import Command
from langchain.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langchain.tools import tool, ToolRuntime

# Update the conversation history by removing all messages
@tool
def clear_conversation() -> Command:
    """Clear the conversation history."""

    return Command(
        update={
            "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)],
        }
    )

# Update the user_name in the agent state
@tool
def update_user_name(
    new_name: str,
    runtime: ToolRuntime
) -> Command:
    """Update the user's name."""
    return Command(update={"user_name": new_name})
```

###### ​Context

Access immutable configuration and contextual data like user IDs, session details, or application-specific configuration through runtime.context.

Tools can access runtime context through ToolRuntime:

Copyfrom dataclasses import dataclass
```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime

USER_DATABASE = {
    "user123": {
        "name": "Alice Johnson",
        "account_type": "Premium",
        "balance": 5000,
        "email": "alice@example.com"
    },
    "user456": {
        "name": "Bob Smith",
        "account_type": "Standard",
        "balance": 1200,
        "email": "bob@example.com"
    }
}

@dataclass
class UserContext:
    user_id: str

@tool
def get_account_info(runtime: ToolRuntime[UserContext]) -> str:
    """Get the current user's account information."""
    user_id = runtime.context.user_id

    if user_id in USER_DATABASE:
        user = USER_DATABASE[user_id]
        return f"Account holder: {user['name']}\nType: {user['account_type']}\nBalance: ${user['balance']}"
    return "User not found"

model = ChatOpenAI(model="gpt-4o")
agent = create_agent(
    model,
    tools=[get_account_info],
    context_schema=UserContext,
    system_prompt="You are a financial assistant."
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's my current balance?"}]},
    context=UserContext(user_id="user123")
)
```

###### ​Memory (Store)

Access persistent data across conversations using the store. The store is accessed via runtime.store and allows you to save and retrieve user-specific or application-specific data.

Tools can access and update the store through ToolRuntime:

Copyfrom typing import Any
```python
from langgraph.store.memory import InMemoryStore
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime

# Access memory
@tool
def get_user_info(user_id: str, runtime: ToolRuntime) -> str:
    """Look up user info."""
    store = runtime.store
    user_info = store.get(("users",), user_id)
    return str(user_info.value) if user_info else "Unknown user"

# Update memory
@tool
def save_user_info(user_id: str, user_info: dict[str, Any], runtime: ToolRuntime) -> str:
    """Save user info."""
    store = runtime.store
    store.put(("users",), user_id, user_info)
    return "Successfully saved user info."

store = InMemoryStore()
agent = create_agent(
    model,
    tools=[get_user_info, save_user_info],
    store=store
)

# First session: save user info
agent.invoke({
    "messages": [{"role": "user", "content": "Save the following user: userid: abc123, name: Foo, age: 25, email: foo@langchain.dev"}]
})

# Second session: get user info
agent.invoke({
    "messages": [{"role": "user", "content": "Get user info for user with id 'abc123'"}]
})
# Here is the user info for user with ID "abc123":
# - Name: Foo
# - Age: 25
# - Email: foo@langchain.dev
See all 42 lines
```

###### ​Stream Writer

Stream custom updates from tools as they execute using runtime.stream_writer. This is useful for providing real-time feedback to users about what a tool is doing.

Copyfrom langchain.tools import tool, ToolRuntime

```python
@tool
def get_weather(city: str, runtime: ToolRuntime) -> str:
    """Get weather for a given city."""
    writer = runtime.stream_writer

    # Stream custom updates as the tool executes
    writer(f"Looking up data for city: {city}")
    writer(f"Acquired data for city: {city}")

    return f"It's always sunny in {city}!"

If you use runtime.stream_writer inside your tool, the tool must be invoked within a LangGraph execution context. See Streaming for more details.

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```


---

## Messages - Docs by LangChain {#doc-39}

**Source:** [https://docs.langchain.com/oss/python/langchain/messages](https://docs.langchain.com/oss/python/langchain/messages)

### Messages

Copy page

#### ​Basic usage

The simplest way to use messages is to create message objects and pass them to a model when invoking.

Copyfrom langchain.chat_models import init_chat_model
```python
from langchain.messages import HumanMessage, AIMessage, SystemMessage

model = init_chat_model("gpt-5-nano")

system_msg = SystemMessage("You are a helpful assistant.")
human_msg = HumanMessage("Hello, how are you?")

# Use with chat models
messages = [system_msg, human_msg]
response = model.invoke(messages)  # Returns AIMessage
```

##### ​Text prompts

Text prompts are strings - ideal for straightforward generation tasks where you don’t need to retain conversation history.

Copyresponse = model.invoke("Write a haiku about spring")

Use text prompts when:

- You have a single, standalone request
- You don’t need conversation history
- You want minimal code complexity

##### ​Message prompts

Alternatively, you can pass in a list of messages to the model by providing a list of message objects.

Copyfrom langchain.messages import SystemMessage, HumanMessage, AIMessage

messages = [
    SystemMessage("You are a poetry expert"),
    HumanMessage("Write a haiku about spring"),
    AIMessage("Cherry blossoms bloom...")
]
response = model.invoke(messages)

Use message prompts when:

- Managing multi-turn conversations
- Working with multimodal content (images, audio, files)
- Including system instructions

##### ​Dictionary format

You can also specify messages directly in OpenAI chat completions format.

Copymessages = [
    {"role": "system", "content": "You are a poetry expert"},
    {"role": "user", "content": "Write a haiku about spring"},
    {"role": "assistant", "content": "Cherry blossoms bloom..."}
]
response = model.invoke(messages)

#### ​Message types

- System message - Tells the model how to behave and provide context for interactions
- Human message - Represents user input and interactions with the model
- AI message - Responses generated by the model, including text content, tool calls, and metadata
- Tool message - Represents the outputs of tool calls

##### ​System Message

A SystemMessage represent an initial set of instructions that primes the model’s behavior. You can use a system message to set the tone, define the model’s role, and establish guidelines for responses.

Basic instructionsCopysystem_msg = SystemMessage("You are a helpful coding assistant.")

messages = [
    system_msg,
    HumanMessage("How do I create a REST API?")
]
response = model.invoke(messages)

Detailed personaCopyfrom langchain.messages import SystemMessage, HumanMessage

system_msg = SystemMessage("""
You are a senior Python developer with expertise in web frameworks.
Always provide code examples and explain your reasoning.
Be concise but thorough in your explanations.
""")

messages = [
    system_msg,
    HumanMessage("How do I create a REST API?")
]
response = model.invoke(messages)

##### ​Human Message

A HumanMessage represents user input and interactions. They can contain text, images, audio, files, and any other amount of multimodal content.

###### ​Text content

Message objectString shortcutCopyresponse = model.invoke([
  HumanMessage("What is machine learning?")
])

###### ​Message metadata

Add metadataCopyhuman_msg = HumanMessage(
    content="Hello!",
    name="alice",  # Optional: identify different users
    id="msg_123",  # Optional: unique identifier for tracing
)

The name field behavior varies by provider – some use it for user identification, others ignore it. To check, refer to the model provider’s reference.

##### ​AI Message

An AIMessage represents the output of a model invocation. They can include multimodal data, tool calls, and provider-specific metadata that you can later access.

Copyresponse = model.invoke("Explain AI")
print(type(response))  # <class 'langchain.messages.AIMessage'>

AIMessage objects are returned by the model when calling it, which contains all of the associated metadata in the response.

Providers weigh/contextualize types of messages differently, which means it is sometimes helpful to manually create a new AIMessage object and insert it into the message history as if it came from the model.

Copyfrom langchain.messages import AIMessage, SystemMessage, HumanMessage

# Create an AI message manually (e.g., for conversation history)
ai_msg = AIMessage("I'd be happy to help you with that question!")

# Add to conversation history
messages = [
    SystemMessage("You are a helpful assistant"),
    HumanMessage("Can you help me?"),
    ai_msg,  # Insert as if it came from the model
    HumanMessage("Great! What's 2+2?")
]

response = model.invoke(messages)

Attributes​textstringThe text content of the message.​contentstring | dict[]The raw content of the message.​content_blocksContentBlock[]The standardized content blocks of the message.​tool_callsdict[] | NoneThe tool calls made by the model.Empty if no tools are called.​idstringA unique identifier for the message (either automatically generated by LangChain or returned in the provider response)​usage_metadatadict | NoneThe usage metadata of the message, which can contain token counts when available.​response_metadataResponseMetadata | NoneThe response metadata of the message.

###### ​Tool calls

When models make tool calls, they’re included in the AIMessage:

Copyfrom langchain.chat_models import init_chat_model

model = init_chat_model("gpt-5-nano")

```python
def get_weather(location: str) -> str:
    """Get the weather at a location."""
    ...

model_with_tools = model.bind_tools([get_weather])
response = model_with_tools.invoke("What's the weather in Paris?")

for tool_call in response.tool_calls:
    print(f"Tool: {tool_call['name']}")
    print(f"Args: {tool_call['args']}")
    print(f"ID: {tool_call['id']}")

Other structured data, such as reasoning or citations, can also appear in message content.
```

###### ​Token usage

An AIMessage can hold token counts and other usage metadata in its usage_metadata field:

Copyfrom langchain.chat_models import init_chat_model

model = init_chat_model("gpt-5-nano")

response = model.invoke("Hello!")
response.usage_metadata

```
Copy{'input_tokens': 8,
 'output_tokens': 304,
 'total_tokens': 312,
 'input_token_details': {'audio': 0, 'cache_read': 0},
 'output_token_details': {'audio': 0, 'reasoning': 256}}

See UsageMetadata for details.
```

###### ​Streaming and chunks

During streaming, you’ll receive AIMessageChunk objects that can be combined into a full message object:

Copychunks = []
full_message = None
for chunk in model.stream("Hi"):
    chunks.append(chunk)
    print(chunk.text)
    full_message = chunk if full_message is None else full_message + chunk

Learn more:
Streaming tokens from chat models
Streaming tokens and/or steps from agents

##### ​Tool Message

For models that support tool calling, AI messages can contain tool calls. Tool messages are used to pass the results of a single tool execution back to the model.

Tools can generate ToolMessage objects directly. Below, we show a simple example. Read more in the tools guide.

Copyfrom langchain.messages import AIMessage
```python
from langchain.messages import ToolMessage

# After a model makes a tool call
# (Here, we demonstrate manually creating the messages for brevity)
ai_message = AIMessage(
    content=[],
    tool_calls=[{
        "name": "get_weather",
        "args": {"location": "San Francisco"},
        "id": "call_123"
    }]
)

# Execute tool and create result message
weather_result = "Sunny, 72°F"
tool_message = ToolMessage(
    content=weather_result,
    tool_call_id="call_123"  # Must match the call ID
)

# Continue conversation
messages = [
    HumanMessage("What's the weather in San Francisco?"),
    ai_message,  # Model's tool call
    tool_message,  # Tool execution result
]
response = model.invoke(messages)  # Model processes the result

Attributes​contentstringrequiredThe stringified output of the tool call.​tool_call_idstringrequiredThe ID of the tool call that this message is responding to. Must match the ID of the tool call in the AIMessage.​namestringrequiredThe name of the tool that was called.​artifactdictAdditional data not sent to the model but can be accessed programmatically.

The artifact field stores supplementary data that won’t be sent to the model but can be accessed programmatically. This is useful for storing raw results, debugging information, or data for downstream processing without cluttering the model’s context.Example: Using artifact for retrieval metadataFor example, a retrieval tool could retrieve a passage from a document for reference by a model. Where message content contains text that the model will reference, an artifact can contain document identifiers or other metadata that an application can use (e.g., to render a page). See example below:Copyfrom langchain.messages import ToolMessage

# Sent to model
message_content = "It was the best of times, it was the worst of times."

# Artifact available downstream
artifact = {"document_id": "doc_123", "page": 0}

tool_message = ToolMessage(
    content=message_content,
    tool_call_id="call_123",
    name="search_books",
    artifact=artifact,
)
See the RAG tutorial for an end-to-end example of building retrieval agents with LangChain.
```

#### ​Message content

You can think of a message’s content as the payload of data that gets sent to the model. Messages have a content attribute that is loosely-typed, supporting strings and lists of untyped objects (e.g., dictionaries). This allows support for provider-native structures directly in LangChain chat models, such as multimodal content and other data.

Separately, LangChain provides dedicated content types for text, reasoning, citations, multi-modal data, server-side tool calls, and other message content. See content blocks below.

LangChain chat models accept message content in the content attribute.

This may contain either:

- A string
- A list of content blocks in a provider-native format
- A list of LangChain’s standard content blocks
See below for an example using multimodal inputs:

Copyfrom langchain.messages import HumanMessage

# String content
human_message = HumanMessage("Hello, how are you?")

# Provider-native format (e.g., OpenAI)
human_message = HumanMessage(content=[
    {"type": "text", "text": "Hello, how are you?"},
    {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
])

# List of standard content blocks
human_message = HumanMessage(content_blocks=[
    {"type": "text", "text": "Hello, how are you?"},
    {"type": "image", "url": "https://example.com/image.jpg"},
])

Specifying content_blocks when initializing a message will still populate message
content, but provides a type-safe interface for doing so.

##### ​Standard content blocks

LangChain provides a standard representation for message content that works across providers.

Message objects implement a content_blocks property that will lazily parse the content attribute into a standard, type-safe representation. For example, messages generated from ChatAnthropic or ChatOpenAI will include thinking or reasoning blocks in the format of the respective provider, but can be lazily parsed into a consistent ReasoningContentBlock representation:

Anthropic OpenAICopyfrom langchain.messages import AIMessage

message = AIMessage(
    content=[
        {"type": "thinking", "thinking": "...", "signature": "WaUjzkyp..."},
        {"type": "text", "text": "..."},
    ],
    response_metadata={"model_provider": "anthropic"}
)
message.content_blocks
```
Copy[{'type': 'reasoning',
  'reasoning': '...',
  'extras': {'signature': 'WaUjzkyp...'}},
 {'type': 'text', 'text': '...'}]
Copyfrom langchain.messages import AIMessage

message = AIMessage(
    content=[
        {
            "type": "reasoning",
            "id": "rs_abc123",
            "summary": [
                {"type": "summary_text", "text": "summary 1"},
                {"type": "summary_text", "text": "summary 2"},
            ],
        },
        {"type": "text", "text": "...", "id": "msg_abc123"},
    ],
    response_metadata={"model_provider": "openai"}
)
message.content_blocks
Copy[{'type': 'reasoning', 'id': 'rs_abc123', 'reasoning': 'summary 1'},
 {'type': 'reasoning', 'id': 'rs_abc123', 'reasoning': 'summary 2'},
 {'type': 'text', 'text': '...', 'id': 'msg_abc123'}]

See the integrations guides to get started with the
inference provider of your choice.

Serializing standard contentIf an application outside of LangChain needs access to the standard content block
representation, you can opt-in to storing content blocks in message content.To do this, you can set the LC_OUTPUT_VERSION environment variable to v1. Or,
initialize any chat model with output_version="v1":Copyfrom langchain.chat_models import init_chat_model

model = init_chat_model("gpt-5-nano", output_version="v1")
```

##### ​Multimodal

Multimodality refers to the ability to work with data that comes in different
forms, such as text, audio, images, and video. LangChain includes standard types
for these data that can be used across providers.

Chat models can accept multimodal data as input and generate
it as output. Below we show short examples of input messages featuring multimodal data.

Extra keys can be included top-level in the content block or nested in "extras": {"key": value}.OpenAI and AWS Bedrock Converse,
for example, require a filename for PDFs. See the provider page
for your chosen model for specifics.

Image inputPDF document inputAudio inputVideo inputCopy# From URL
```
message = {
    "role": "user",
    "content": [
        {"type": "text", "text": "Describe the content of this image."},
        {"type": "image", "url": "https://example.com/path/to/image.jpg"},
    ]
}

# From base64 data
message = {
    "role": "user",
    "content": [
        {"type": "text", "text": "Describe the content of this image."},
        {
            "type": "image",
            "base64": "AAAAIGZ0eXBtcDQyAAAAAGlzb21tcDQyAAACAGlzb2...",
            "mime_type": "image/jpeg",
        },
    ]
}

# From provider-managed File ID
message = {
    "role": "user",
    "content": [
        {"type": "text", "text": "Describe the content of this image."},
        {"type": "image", "file_id": "file-abc123"},
    ]
}

Not all models support all file types. Check the model provider’s reference for supported formats and size limits.
```

##### ​Content block reference

Content blocks are represented (either when creating a message or accessing the content_blocks property) as a list of typed dictionaries. Each item in the list must adhere to one of the following block types:

```
CoreTextContentBlockPurpose: Standard text output​typestringrequiredAlways "text"​textstringrequiredThe text content​annotationsobject[]List of annotations for the text​extrasobjectAdditional provider-specific dataExample:Copy{
    "type": "text",
    "text": "Hello world",
    "annotations": []
}
ReasoningContentBlockPurpose: Model reasoning steps​typestringrequiredAlways "reasoning"​reasoningstringThe reasoning content​extrasobjectAdditional provider-specific dataExample:Copy{
    "type": "reasoning",
    "reasoning": "The user is asking about...",
    "extras": {"signature": "abc123"},
}
MultimodalImageContentBlockPurpose: Image data​typestringrequiredAlways "image"​urlstringURL pointing to the image location.​base64stringBase64-encoded image data.​idstringUnique identifier for this content block (either generated by the provider or by LangChain).​mime_typestringImage MIME type (e.g., image/jpeg, image/png). Required for base64 data.AudioContentBlockPurpose: Audio data​typestringrequiredAlways "audio"​urlstringURL pointing to the audio location.​base64stringBase64-encoded audio data.​idstringUnique identifier for this content block (either generated by the provider or by LangChain).​mime_typestringAudio MIME type (e.g., audio/mpeg, audio/wav). Required for base64 data.VideoContentBlockPurpose: Video data​typestringrequiredAlways "video"​urlstringURL pointing to the video location.​base64stringBase64-encoded video data.​idstringUnique identifier for this content block (either generated by the provider or by LangChain).​mime_typestringVideo MIME type (e.g., video/mp4, video/webm). Required for base64 data.FileContentBlockPurpose: Generic files (PDF, etc)​typestringrequiredAlways "file"​urlstringURL pointing to the file location.​base64stringBase64-encoded file data.​idstringUnique identifier for this content block (either generated by the provider or by LangChain).​mime_typestringFile MIME type (e.g., application/pdf). Required for base64 data.PlainTextContentBlockPurpose: Document text (.txt, .md)​typestringrequiredAlways "text-plain"​textstringThe text content​mime_typestringMIME type of the text (e.g., text/plain, text/markdown)Tool CallingToolCallPurpose: Function calls​typestringrequiredAlways "tool_call"​namestringrequiredName of the tool to call​argsobjectrequiredArguments to pass to the tool​idstringrequiredUnique identifier for this tool callExample:Copy{
    "type": "tool_call",
    "name": "search",
    "args": {"query": "weather"},
    "id": "call_123"
}
ToolCallChunkPurpose: Streaming tool call fragments​typestringrequiredAlways "tool_call_chunk"​namestringName of the tool being called​argsstringPartial tool arguments (may be incomplete JSON)​idstringTool call identifier​indexnumber | stringPosition of this chunk in the streamInvalidToolCallPurpose: Malformed calls, intended to catch JSON parsing errors.​typestringrequiredAlways "invalid_tool_call"​namestringName of the tool that failed to be called​argsobjectArguments to pass to the tool​errorstringDescription of what went wrongServer-Side Tool ExecutionServerToolCallPurpose: Tool call that is executed server-side.​typestringrequiredAlways "server_tool_call"​idstringrequiredAn identifier associated with the tool call.​namestringrequiredThe name of the tool to be called.​argsstringrequiredPartial tool arguments (may be incomplete JSON)ServerToolCallChunkPurpose: Streaming server-side tool call fragments​typestringrequiredAlways "server_tool_call_chunk"​idstringAn identifier associated with the tool call.​namestringName of the tool being called​argsstringPartial tool arguments (may be incomplete JSON)​indexnumber | stringPosition of this chunk in the streamServerToolResultPurpose: Search results​typestringrequiredAlways "server_tool_result"​tool_call_idstringrequiredIdentifier of the corresponding server tool call.​idstringIdentifier associated with the server tool result.​statusstringrequiredExecution status of the server-side tool. "success" or "error".​outputOutput of the executed tool.Provider-Specific BlocksNonStandardContentBlockPurpose: Provider-specific escape hatch​typestringrequiredAlways "non_standard"​valueobjectrequiredProvider-specific data structureUsage: For experimental or provider-unique featuresAdditional provider-specific content types may be found within the reference documentation of each model provider.

View the canonical type definitions in the API reference.

Content blocks were introduced as a new property on messages in LangChain v1 to standardize content formats across providers while maintaining backward compatibility with existing code.Content blocks are not a replacement for the content property, but rather a new property that can be used to access the content of a message in a standardized format.
```

#### ​Use with chat models

Chat models accept a sequence of message objects as input and return an AIMessage as output. Interactions are often stateless, so that a simple conversational loop involves invoking a model with a growing list of messages.

Refer to the below guides to learn more:

- Built-in features for persisting and managing conversation histories
- Strategies for managing context windows, including trimming and summarizing messages
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Models - Docs by LangChain {#doc-40}

**Source:** [https://docs.langchain.com/oss/python/langchain/models](https://docs.langchain.com/oss/python/langchain/models)

### Models

Copy page

#### ​Basic usage

Models can be utilized in two ways:

- With agents - Models can be dynamically specified when creating an agent.
- Standalone - Models can be called directly (outside of the agent loop) for tasks like text generation, classification, or extraction without the need for an agent framework.
The same model interface works in both contexts, which gives you the flexibility to start simple and scale up to more complex agent-based workflows as needed.

##### ​Initialize a model

The easiest way to get started with a standalone model in LangChain is to use init_chat_model to initialize one from a chat model provider of your choice (examples below):

OpenAI Anthropic Azure Google Gemini AWS Bedrock HuggingFace👉 Read the OpenAI chat model integration docsCopypip install -U "langchain[openai]"
init_chat_modelModel ClassCopyimport os
```python
from langchain.chat_models import init_chat_model

os.environ["OPENAI_API_KEY"] = "sk-..."

model = init_chat_model("gpt-4.1")
👉 Read the Anthropic chat model integration docsCopypip install -U "langchain[anthropic]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["ANTHROPIC_API_KEY"] = "sk-..."

model = init_chat_model("claude-sonnet-4-5-20250929")
👉 Read the Azure chat model integration docsCopypip install -U "langchain[openai]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["AZURE_OPENAI_API_KEY"] = "..."
os.environ["AZURE_OPENAI_ENDPOINT"] = "..."
os.environ["OPENAI_API_VERSION"] = "2025-03-01-preview"

model = init_chat_model(
    "azure_openai:gpt-4.1",
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
)
👉 Read the Google GenAI chat model integration docsCopypip install -U "langchain[google-genai]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["GOOGLE_API_KEY"] = "..."

model = init_chat_model("google_genai:gemini-2.5-flash-lite")
👉 Read the AWS Bedrock chat model integration docsCopypip install -U "langchain[aws]"
init_chat_modelModel ClassCopyfrom langchain.chat_models import init_chat_model

# Follow the steps here to configure your credentials:
# https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html

model = init_chat_model(
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
    model_provider="bedrock_converse",
)
👉 Read the HuggingFace chat model integration docsCopypip install -U "langchain[huggingface]"
init_chat_modelModel ClassCopyimport os
from langchain.chat_models import init_chat_model

os.environ["HUGGINGFACEHUB_API_TOKEN"] = "hf_..."

model = init_chat_model(
    "microsoft/Phi-3-mini-4k-instruct",
    model_provider="huggingface",
    temperature=0.7,
    max_tokens=1024,
)

Copyresponse = model.invoke("Why do parrots talk?")

See init_chat_model for more detail, including information on how to pass model parameters.
```

##### ​Key methods

InvokeThe model takes messages as input and outputs messages after generating a complete response.

StreamInvoke the model, but stream the output as it is generated in real-time.

BatchSend multiple requests to a model in a batch for more efficient processing.

In addition to chat models, LangChain provides support for other adjacent technologies, such as embedding models and vector stores. See the integrations page for details.

​Parameters

A chat model takes parameters that can be used to configure its behavior. The full set of supported parameters varies by model and provider, but standard ones include:

​modelstringrequiredThe name or identifier of the specific model you want to use with a provider. You can also specify both the model and its provider in a single argument using the ’:’ format, for example, ‘openai:o1’.

​api_keystringThe key required for authenticating with the model’s provider. This is usually issued when you sign up for access to the model. Often accessed by setting an environment variable.

​temperaturenumberControls the randomness of the model’s output. A higher number makes responses more creative; lower ones make them more deterministic.

​max_tokensnumberLimits the total number of tokens in the response, effectively controlling how long the output can be.

​timeoutnumberThe maximum time (in seconds) to wait for a response from the model before canceling the request.

​max_retriesnumberThe maximum number of attempts the system will make to resend a request if it fails due to issues like network timeouts or rate limits.

Using init_chat_model, pass these parameters as inline **kwargs:

Initialize using model parametersCopymodel = init_chat_model(
    "claude-sonnet-4-5-20250929",
    # Kwargs passed to the model:
    temperature=0.7,
    timeout=30,
    max_tokens=1000,
)

Each chat model integration may have additional params used to control provider-specific functionality.For example, ChatOpenAI has use_responses_api to dictate whether to use the OpenAI Responses or Completions API.To find all the parameters supported by a given chat model, head to the chat model integrations page.

​Invocation

A chat model must be invoked to generate an output. There are three primary invocation methods, each suited to different use cases.

​Invoke

The most straightforward way to call a model is to use invoke() with a single message or a list of messages.

Single messageCopyresponse = model.invoke("Why do parrots have colorful feathers?")
print(response)

A list of messages can be provided to a chat model to represent conversation history. Each message has a role that models use to indicate who sent the message in the conversation.

See the messages guide for more detail on roles, types, and content.

Dictionary formatCopyconversation = [
    {"role": "system", "content": "You are a helpful assistant that translates English to French."},
    {"role": "user", "content": "Translate: I love programming."},
    {"role": "assistant", "content": "J'adore la programmation."},
    {"role": "user", "content": "Translate: I love building applications."}
]

response = model.invoke(conversation)
print(response)  # AIMessage("J'adore créer des applications.")

Message objectsCopyfrom langchain.messages import HumanMessage, AIMessage, SystemMessage

conversation = [
    SystemMessage("You are a helpful assistant that translates English to French."),
    HumanMessage("Translate: I love programming."),
    AIMessage("J'adore la programmation."),
    HumanMessage("Translate: I love building applications.")
]

response = model.invoke(conversation)
print(response)  # AIMessage("J'adore créer des applications.")

If the return type of your invocation is a string, ensure that you are using a chat model as opposed to a LLM. Legacy, text-completion LLMs return strings directly. LangChain chat models are prefixed with “Chat”, e.g., ChatOpenAI(/oss/integrations/chat/openai).

​Stream

Most models can stream their output content while it is being generated. By displaying output progressively, streaming significantly improves user experience, particularly for longer responses.

Calling stream() returns an iterator that yields output chunks as they are produced. You can use a loop to process each chunk in real-time:

Basic text streamingStream tool calls, reasoning, and other contentCopyfor chunk in model.stream("Why do parrots have colorful feathers?"):
    print(chunk.text, end="|", flush=True)

As opposed to invoke(), which returns a single AIMessage after the model has finished generating its full response, stream() returns multiple AIMessageChunk objects, each containing a portion of the output text. Importantly, each chunk in a stream is designed to be gathered into a full message via summation:

Construct an AIMessageCopyfull = None  # None | AIMessageChunk
for chunk in model.stream("What color is the sky?"):
    full = chunk if full is None else full + chunk
    print(full.text)

# The
# The sky
# The sky is
# The sky is typically
# The sky is typically blue
# ...

print(full.content_blocks)
# [{"type": "text", "text": "The sky is typically blue..."}]

The resulting message can be treated the same as a message that was generated with invoke() – for example, it can be aggregated into a message history and passed back to the model as conversational context.

Streaming only works if all steps in the program know how to process a stream of chunks. For instance, an application that isn’t streaming-capable would be one that needs to store the entire output in memory before it can be processed.

Advanced streaming topicsStreaming eventsLangChain chat models can also stream semantic events using astream_events().This simplifies filtering based on event types and other metadata, and will aggregate the full message in the background. See below for an example.Copyasync for event in model.astream_events("Hello"):

    if event["event"] == "on_chat_model_start":
        print(f"Input: {event['data']['input']}")

    elif event["event"] == "on_chat_model_stream":
        print(f"Token: {event['data']['chunk'].text}")

    elif event["event"] == "on_chat_model_end":
        print(f"Full message: {event['data']['output'].text}")

    else:
        pass
CopyInput: Hello
Token: Hi
Token:  there
Token: !
Token:  How
Token:  can
Token:  I
...
Full message: Hi there! How can I help today?
See the astream_events() reference for event types and other details."Auto-streaming" chat modelsLangChain simplifies streaming from chat models by automatically enabling streaming mode in certain cases, even when you’re not explicitly calling the streaming methods. This is particularly useful when you use the non-streaming invoke method but still want to stream the entire application, including intermediate results from the chat model.In LangGraph agents, for example, you can call model.invoke() within nodes, but LangChain will automatically delegate to streaming if running in a streaming mode.​How it worksWhen you invoke() a chat model, LangChain will automatically switch to an internal streaming mode if it detects that you are trying to stream the overall application. The result of the invocation will be the same as far as the code that was using invoke is concerned; however, while the chat model is being streamed, LangChain will take care of invoking on_llm_new_token events in LangChain’s callback system.Callback events allow LangGraph stream() and astream_events() to surface the chat model’s output in real-time.

​Batch

Batching a collection of independent requests to a model can significantly improve performance and reduce costs, as the processing can be done in parallel:

BatchCopyresponses = model.batch([
    "Why do parrots have colorful feathers?",
    "How do airplanes fly?",
    "What is quantum computing?"
])
for response in responses:
    print(response)

This section describes a chat model method batch(), which parallelizes model calls client-side.It is distinct from batch APIs supported by inference providers, such as OpenAI or Anthropic.

By default, batch() will only return the final output for the entire batch. If you want to receive the output for each individual input as it finishes generating, you can stream results with batch_as_completed():

Yield batch responses upon completionCopyfor response in model.batch_as_completed([
    "Why do parrots have colorful feathers?",
    "How do airplanes fly?",
    "What is quantum computing?"
]):
    print(response)

When using batch_as_completed(), results may arrive out of order. Each includes the input index for matching to reconstruct the original order as needed.

When processing a large number of inputs using batch() or batch_as_completed(), you may want to control the maximum number of parallel calls. This can be done by setting the max_concurrency attribute in the RunnableConfig dictionary.Batch with max concurrencyCopymodel.batch(
    list_of_inputs,
```
    config={
        'max_concurrency': 5,  # Limit to 5 parallel calls
    }
)
See the RunnableConfig reference for a full list of supported attributes.

For more details on batching, see the reference.

​Tool calling

Models can request to call tools that perform tasks such as fetching data from a database, searching the web, or running code. Tools are pairings of:

- A schema, including the name of the tool, a description, and/or argument definitions (often a JSON schema)
- A function or coroutine to execute.
You may hear the term “function calling”. We use this interchangeably with “tool calling”.

Here’s the basic tool calling flow between a user and a model:

To make tools that you have defined available for use by a model, you must bind them using bind_tools. In subsequent invocations, the model can choose to call any of the bound tools as needed.

Some model providers offer built-in tools that can be enabled via model or invocation parameters (e.g. ChatOpenAI, ChatAnthropic). Check the respective provider reference for details.

See the tools guide for details and other options for creating tools.

Binding user toolsCopyfrom langchain.tools import tool

@tool
def get_weather(location: str) -> str:
    """Get the weather at a location."""
    return f"It's sunny in {location}."

model_with_tools = model.bind_tools([get_weather])

response = model_with_tools.invoke("What's the weather like in Boston?")
for tool_call in response.tool_calls:
    # View tool calls made by the model
    print(f"Tool: {tool_call['name']}")
    print(f"Args: {tool_call['args']}")

When binding user-defined tools, the model’s response includes a request to execute a tool. When using a model separately from an agent, it is up to you to execute the requested tool and return the result back to the model for use in subsequent reasoning. When using an agent, the agent loop will handle the tool execution loop for you.

Below, we show some common ways you can use tool calling.

Tool execution loopWhen a model returns tool calls, you need to execute the tools and pass the results back to the model. This creates a conversation loop where the model can use tool results to generate its final response. LangChain includes agent abstractions that handle this orchestration for you.Here’s a simple example of how to do this:Tool execution loopCopy# Bind (potentially multiple) tools to the model
model_with_tools = model.bind_tools([get_weather])

# Step 1: Model generates tool calls
messages = [{"role": "user", "content": "What's the weather in Boston?"}]
ai_msg = model_with_tools.invoke(messages)
messages.append(ai_msg)

# Step 2: Execute tools and collect results
for tool_call in ai_msg.tool_calls:
    # Execute the tool with the generated arguments
    tool_result = get_weather.invoke(tool_call)
    messages.append(tool_result)

# Step 3: Pass results back to model for final response
final_response = model_with_tools.invoke(messages)
print(final_response.text)
# "The current weather in Boston is 72°F and sunny."
Each ToolMessage returned by the tool includes a tool_call_id that matches the original tool call, helping the model correlate results with requests.Forcing tool callsBy default, the model has the freedom to choose which bound tool to use based on the user’s input. However, you might want to force choosing a tool, ensuring the model uses either a particular tool or any tool from a given list:Force use of any toolForce use of specific toolsCopymodel_with_tools = model.bind_tools([tool_1], tool_choice="any")
Parallel tool callsMany models support calling multiple tools in parallel when appropriate. This allows the model to gather information from different sources simultaneously.Parallel tool callsCopymodel_with_tools = model.bind_tools([get_weather])

response = model_with_tools.invoke(
    "What's the weather in Boston and Tokyo?"
)

# The model may generate multiple tool calls
print(response.tool_calls)
# [
#   {'name': 'get_weather', 'args': {'location': 'Boston'}, 'id': 'call_1'},
#   {'name': 'get_weather', 'args': {'location': 'Tokyo'}, 'id': 'call_2'},
# ]

# Execute all tools (can be done in parallel with async)
results = []
for tool_call in response.tool_calls:
    if tool_call['name'] == 'get_weather':
        result = get_weather.invoke(tool_call)
    ...
    results.append(result)
The model intelligently determines when parallel execution is appropriate based on the independence of the requested operations.Most models supporting tool calling enable parallel tool calls by default. Some (including OpenAI and Anthropic) allow you to disable this feature. To do this, set parallel_tool_calls=False:Copymodel.bind_tools([get_weather], parallel_tool_calls=False)
Streaming tool callsWhen streaming responses, tool calls are progressively built through ToolCallChunk. This allows you to see tool calls as they’re being generated rather than waiting for the complete response.Streaming tool callsCopyfor chunk in model_with_tools.stream(
    "What's the weather in Boston and Tokyo?"
):
    # Tool call chunks arrive progressively
    for tool_chunk in chunk.tool_call_chunks:
        if name := tool_chunk.get("name"):
            print(f"Tool: {name}")
        if id_ := tool_chunk.get("id"):
            print(f"ID: {id_}")
        if args := tool_chunk.get("args"):
            print(f"Args: {args}")

# Output:
# Tool: get_weather
# ID: call_SvMlU1TVIZugrFLckFE2ceRE
# Args: {"lo
# Args: catio
# Args: n": "B
# Args: osto
# Args: n"}
# Tool: get_weather
# ID: call_QMZdy6qInx13oWKE7KhuhOLR
# Args: {"lo
# Args: catio
# Args: n": "T
# Args: okyo
# Args: "}
You can accumulate chunks to build complete tool calls:Accumulate tool callsCopygathered = None
for chunk in model_with_tools.stream("What's the weather in Boston?"):
    gathered = chunk if gathered is None else gathered + chunk
    print(gathered.tool_calls)

​Structured output

Models can be requested to provide their response in a format matching a given schema. This is useful for ensuring the output can be easily parsed and used in subsequent processing. LangChain supports multiple schema types and methods for enforcing structured output.

Pydantic TypedDict JSON SchemaPydantic models provide the richest feature set with field validation, descriptions, and nested structures.Copyfrom pydantic import BaseModel, Field

class Movie(BaseModel):
    """A movie with details."""
    title: str = Field(..., description="The title of the movie")
    year: int = Field(..., description="The year the movie was released")
    director: str = Field(..., description="The director of the movie")
    rating: float = Field(..., description="The movie's rating out of 10")

model_with_structure = model.with_structured_output(Movie)
response = model_with_structure.invoke("Provide details about the movie Inception")
print(response)  # Movie(title="Inception", year=2010, director="Christopher Nolan", rating=8.8)
TypedDict provides a simpler alternative using Python’s built-in typing, ideal when you don’t need runtime validation.Copyfrom typing_extensions import TypedDict, Annotated

class MovieDict(TypedDict):
    """A movie with details."""
    title: Annotated[str, ..., "The title of the movie"]
    year: Annotated[int, ..., "The year the movie was released"]
    director: Annotated[str, ..., "The director of the movie"]
    rating: Annotated[float, ..., "The movie's rating out of 10"]

model_with_structure = model.with_structured_output(MovieDict)
response = model_with_structure.invoke("Provide details about the movie Inception")
print(response)  # {'title': 'Inception', 'year': 2010, 'director': 'Christopher Nolan', 'rating': 8.8}
For maximum control or interoperability, you can provide a raw JSON Schema.Copyimport json

json_schema = {
    "title": "Movie",
    "description": "A movie with details",
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "The title of the movie"
        },
        "year": {
            "type": "integer",
            "description": "The year the movie was released"
        },
        "director": {
            "type": "string",
            "description": "The director of the movie"
        },
        "rating": {
            "type": "number",
            "description": "The movie's rating out of 10"
        }
    },
    "required": ["title", "year", "director", "rating"]
}

model_with_structure = model.with_structured_output(
    json_schema,
    method="json_schema",
)
response = model_with_structure.invoke("Provide details about the movie Inception")
print(response)  # {'title': 'Inception', 'year': 2010, ...}

Key considerations for structured output:
Method parameter: Some providers support different methods ('json_schema', 'function_calling', 'json_mode')

'json_schema' typically refers to dedicated structured output features offered by a provider
'function_calling' derives structured output by forcing a tool call following the given schema
'json_mode' is a precursor to 'json_schema' offered by some providers - it generates valid json, but the schema must be described in the prompt

Include raw: Use include_raw=True to get both the parsed output and the raw AI message
Validation: Pydantic models provide automatic validation, while TypedDict and JSON Schema require manual validation

Example: Message output alongside parsed structureIt can be useful to return the raw AIMessage object alongside the parsed representation to access response metadata such as token counts. To do this, set include_raw=True when calling with_structured_output:Copyfrom pydantic import BaseModel, Field

class Movie(BaseModel):
    """A movie with details."""
    title: str = Field(..., description="The title of the movie")
    year: int = Field(..., description="The year the movie was released")
    director: str = Field(..., description="The director of the movie")
    rating: float = Field(..., description="The movie's rating out of 10")

model_with_structure = model.with_structured_output(Movie, include_raw=True)
response = model_with_structure.invoke("Provide details about the movie Inception")
response
# {
#     "raw": AIMessage(...),
#     "parsed": Movie(title=..., year=..., ...),
#     "parsing_error": None,
# }

Example: Nested structuresSchemas can be nested:Pydantic BaseModelTypedDictCopyfrom pydantic import BaseModel, Field

class Actor(BaseModel):
    name: str
    role: str

class MovieDetails(BaseModel):
    title: str
    year: int
    cast: list[Actor]
    genres: list[str]
    budget: float | None = Field(None, description="Budget in millions USD")

model_with_structure = model.with_structured_output(MovieDetails)

​Supported models

LangChain supports all major model providers, including OpenAI, Anthropic, Google, Azure, AWS Bedrock, and more. Each provider offers a variety of models with different capabilities. For a full list of supported models in LangChain, see the integrations page.

​Advanced topics

​Model profiles

This is a beta feature. The format of model profiles is subject to change.

Model profiles require langchain>=1.1.

LangChain chat models can expose a dictionary of supported features and capabilities through a .profile attribute:

Copymodel.profile
# {
#   "max_input_tokens": 400000,
#   "image_inputs": True,
#   "reasoning_output": True,
#   "tool_calling": True,
#   ...
# }

Refer to the full set of fields in the API reference.

Much of the model profile data is powered by the models.dev project, an open source initiative that provides model capability data. These data are augmented with additional fields for purposes of use with LangChain. These augmentations are kept aligned with the upstream project as it evolves.

Model profile data allow applications to work around model capabilities dynamically. For example:

- Summarization middleware can trigger summarization based on a model’s context window size.
- Structured output strategies in create_agent can be inferred automatically (e.g., by checking support for native structured output features).
- Model inputs can be gated based on supported modalities and maximum input tokens.
Updating or overwriting profile dataModel profile data can be changed if it is missing, stale, or incorrect.Option 1 (quick fix)You can instantiate a chat model with any valid profile:Copycustom_profile = {
    "max_input_tokens": 100_000,
    "tool_calling": True,
    "structured_output": True,
    # ...
}
model = init_chat_model("...", profile=custom_profile)
The profile is also a regular dict and can be updated in place. If the model instance is shared, consider using model_copy to avoid mutating shared state.Copynew_profile = model.profile | {"key": "value"}
model.model_copy(update={"profile": new_profile})
Option 2 (fix data upstream)The primary source for the data is the models.dev project. This data is merged with additional fields and overrides in LangChain integration packages and are shipped with those packages.Model profile data can be updated through the following process:
(If needed) update the source data at models.dev through a pull request to its repository on GitHub.
(If needed) update additional fields and overrides in langchain_<package>/data/profile_augmentations.toml through a pull request to the LangChain integration package`.
Use the langchain-model-profiles CLI tool to pull the latest data from models.dev, merge in the augmentations and update the profile data:
Copypip install langchain-model-profiles
Copylangchain-profiles refresh --provider <provider> --data-dir <data_dir>
This command:
Downloads the latest data for <provider> from models.dev
Merges augmentations from profile_augmentations.toml in <data_dir>
Writes merged profiles to profiles.py in <data_dir>
For example: from libs/partners/anthropic in the LangChain monorepo:Copyuv run --with langchain-model-profiles --provider anthropic --data-dir langchain_anthropic/data

​Multimodal

Certain models can process and return non-textual data such as images, audio, and video. You can pass non-textual data to a model by providing content blocks.

All LangChain chat models with underlying multimodal capabilities support:
Data in the cross-provider standard format (see our messages guide)
OpenAI chat completions format
Any format that is native to that specific provider (e.g., Anthropic models accept Anthropic native format)

See the multimodal section of the messages guide for details.

Some models can return multimodal data as part of their response. If invoked to do so, the resulting AIMessage will have content blocks with multimodal types.

Multimodal outputCopyresponse = model.invoke("Create a picture of a cat")
print(response.content_blocks)
# [
#     {"type": "text", "text": "Here's a picture of a cat"},
#     {"type": "image", "base64": "...", "mime_type": "image/jpeg"},
# ]

See the integrations page for details on specific providers.

​Reasoning

Many models are capable of performing multi-step reasoning to arrive at a conclusion. This involves breaking down complex problems into smaller, more manageable steps.

If supported by the underlying model, you can surface this reasoning process to better understand how the model arrived at its final answer.

Stream reasoning outputComplete reasoning outputCopyfor chunk in model.stream("Why do parrots have colorful feathers?"):
    reasoning_steps = [r for r in chunk.content_blocks if r["type"] == "reasoning"]
    print(reasoning_steps if reasoning_steps else chunk.text)

Depending on the model, you can sometimes specify the level of effort it should put into reasoning. Similarly, you can request that the model turn off reasoning entirely. This may take the form of categorical “tiers” of reasoning (e.g., 'low' or 'high') or integer token budgets.

For details, see the integrations page or reference for your respective chat model.

​Local models

LangChain supports running models locally on your own hardware. This is useful for scenarios where either data privacy is critical, you want to invoke a custom model, or when you want to avoid the costs incurred when using a cloud-based model.

Ollama is one of the easiest ways to run models locally. See the full list of local integrations on the integrations page.

​Prompt caching

Many providers offer prompt caching features to reduce latency and cost on repeat processing of the same tokens. These features can be implicit or explicit:

- Implicit prompt caching: providers will automatically pass on cost savings if a request hits a cache. Examples: OpenAI and Gemini.
- Explicit caching: providers allow you to manually indicate cache points for greater control or to guarantee cost savings. Examples:

ChatOpenAI (via prompt_cache_key)
Anthropic’s AnthropicPromptCachingMiddleware
Gemini.
AWS Bedrock
- ChatOpenAI (via prompt_cache_key)
- Anthropic’s AnthropicPromptCachingMiddleware
- Gemini.
- AWS Bedrock
Prompt caching is often only engaged above a minimum input token threshold. See provider pages for details.

Cache usage will be reflected in the usage metadata of the model response.

​Server-side tool use

Some providers support server-side tool-calling loops: models can interact with web search, code interpreters, and other tools and analyze the results in a single conversational turn.

If a model invokes a tool server-side, the content of the response message will include content representing the invocation and result of the tool. Accessing the content blocks of the response will return the server-side tool calls and results in a provider-agnostic format:

Invoke with server-side tool useCopyfrom langchain.chat_models import init_chat_model

model = init_chat_model("gpt-4.1-mini")

tool = {"type": "web_search"}
model_with_tools = model.bind_tools([tool])

response = model_with_tools.invoke("What was a positive news story from today?")
response.content_blocks

ResultCopy[
    {
        "type": "server_tool_call",
        "name": "web_search",
        "args": {
            "query": "positive news stories today",
            "type": "search"
        },
        "id": "ws_abc123"
    },
    {
        "type": "server_tool_result",
        "tool_call_id": "ws_abc123",
        "status": "success"
    },
    {
        "type": "text",
        "text": "Here are some positive news stories from today...",
        "annotations": [
            {
                "end_index": 410,
                "start_index": 337,
                "title": "article title",
                "type": "citation",
                "url": "..."
            }
        ]
    }
]
See all 29 lines

This represents a single conversational turn; there are no associated ToolMessage objects that need to be passed in as in client-side tool-calling.

See the integration page for your given provider for available tools and usage details.

​Rate limiting

Many chat model providers impose a limit on the number of invocations that can be made in a given time period. If you hit a rate limit, you will typically receive a rate limit error response from the provider, and will need to wait before making more requests.

To help manage rate limits, chat model integrations accept a rate_limiter parameter that can be provided during initialization to control the rate at which requests are made.

Initialize and use a rate limiterLangChain in comes with (an optional) built-in InMemoryRateLimiter. This limiter is thread safe and can be shared by multiple threads in the same process.Define a rate limiterCopyfrom langchain_core.rate_limiters import InMemoryRateLimiter

rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.1,  # 1 request every 10s
    check_every_n_seconds=0.1,  # Check every 100ms whether allowed to make a request
    max_bucket_size=10,  # Controls the maximum burst size.
)

model = init_chat_model(
    model="gpt-5",
    model_provider="openai",
    rate_limiter=rate_limiter
)
The provided rate limiter can only limit the number of requests per unit time. It will not help if you need to also limit based on the size of the requests.

​Base URL or proxy

For many chat model integrations, you can configure the base URL for API requests, which allows you to use model providers that have OpenAI-compatible APIs or to use a proxy server.

Base URLMany model providers offer OpenAI-compatible APIs (e.g., Together AI, vLLM). You can use init_chat_model with these providers by specifying the appropriate base_url parameter:Copymodel = init_chat_model(
    model="MODEL_NAME",
    model_provider="openai",
    base_url="BASE_URL",
    api_key="YOUR_API_KEY",
)
When using direct chat model class instantiation, the parameter name may vary by provider. Check the respective reference for details.

Proxy configurationFor deployments requiring HTTP proxies, some model integrations support proxy configuration:Copyfrom langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="gpt-4o",
    openai_proxy="http://proxy.example.com:8080"
)
Proxy support varies by integration. Check the specific model provider’s reference for proxy configuration options.

​Log probabilities

Certain models can be configured to return token-level log probabilities representing the likelihood of a given token by setting the logprobs parameter when initializing the model:

Copymodel = init_chat_model(
    model="gpt-4o",
    model_provider="openai"
).bind(logprobs=True)

response = model.invoke("Why do parrots talk?")
print(response.response_metadata["logprobs"])

​Token usage

A number of model providers return token usage information as part of the invocation response. When available, this information will be included on the AIMessage objects produced by the corresponding model. For more details, see the messages guide.

Some provider APIs, notably OpenAI and Azure OpenAI chat completions, require users opt-in to receiving token usage data in streaming contexts. See the streaming usage metadata section of the integration guide for details.

You can track aggregate token counts across models in an application using either a callback or context manager, as shown below:

Callback handler Context managerCopyfrom langchain.chat_models import init_chat_model
from langchain_core.callbacks import UsageMetadataCallbackHandler

model_1 = init_chat_model(model="gpt-4o-mini")
model_2 = init_chat_model(model="claude-haiku-4-5-20251001")

callback = UsageMetadataCallbackHandler()
result_1 = model_1.invoke("Hello", config={"callbacks": [callback]})
result_2 = model_2.invoke("Hello", config={"callbacks": [callback]})
callback.usage_metadata
Copy{
    'gpt-4o-mini-2024-07-18': {
        'input_tokens': 8,
        'output_tokens': 10,
        'total_tokens': 18,
        'input_token_details': {'audio': 0, 'cache_read': 0},
        'output_token_details': {'audio': 0, 'reasoning': 0}
    },
    'claude-haiku-4-5-20251001': {
        'input_tokens': 8,
        'output_tokens': 21,
        'total_tokens': 29,
        'input_token_details': {'cache_read': 0, 'cache_creation': 0}
    }
}
Copyfrom langchain.chat_models import init_chat_model
from langchain_core.callbacks import get_usage_metadata_callback

model_1 = init_chat_model(model="gpt-4o-mini")
model_2 = init_chat_model(model="claude-haiku-4-5-20251001")

with get_usage_metadata_callback() as cb:
    model_1.invoke("Hello")
    model_2.invoke("Hello")
    print(cb.usage_metadata)
Copy{
    'gpt-4o-mini-2024-07-18': {
        'input_tokens': 8,
        'output_tokens': 10,
        'total_tokens': 18,
        'input_token_details': {'audio': 0, 'cache_read': 0},
        'output_token_details': {'audio': 0, 'reasoning': 0}
    },
    'claude-haiku-4-5-20251001': {
        'input_tokens': 8,
        'output_tokens': 21,
        'total_tokens': 29,
        'input_token_details': {'cache_read': 0, 'cache_creation': 0}
    }
}

​Invocation config

When invoking a model, you can pass additional configuration through the config parameter using a RunnableConfig dictionary. This provides run-time control over execution behavior, callbacks, and metadata tracking.

Common configuration options include:

Invocation with configCopyresponse = model.invoke(
    "Tell me a joke",
    config={
        "run_name": "joke_generation",      # Custom name for this run
        "tags": ["humor", "demo"],          # Tags for categorization
        "metadata": {"user_id": "123"},     # Custom metadata
        "callbacks": [my_callback_handler], # Callback handlers
    }
)

These configuration values are particularly useful when:

- Debugging with LangSmith tracing
- Implementing custom logging or monitoring
- Controlling resource usage in production
- Tracking invocations across complex pipelines
Key configuration attributes​run_namestringIdentifies this specific invocation in logs and traces. Not inherited by sub-calls.​tagsstring[]Labels inherited by all sub-calls for filtering and organization in debugging tools.​metadataobjectCustom key-value pairs for tracking additional context, inherited by all sub-calls.​max_concurrencynumberControls the maximum number of parallel calls when using batch() or batch_as_completed().​callbacksarrayHandlers for monitoring and responding to events during execution.​recursion_limitnumberMaximum recursion depth for chains to prevent infinite loops in complex pipelines.

See full RunnableConfig reference for all supported attributes.

​Configurable models

You can also create a runtime-configurable model by specifying configurable_fields. If you don’t specify a model value, then 'model' and 'model_provider' will be configurable by default.

Copyfrom langchain.chat_models import init_chat_model

configurable_model = init_chat_model(temperature=0)

configurable_model.invoke(
    "what's your name",
    config={"configurable": {"model": "gpt-5-nano"}},  # Run with GPT-5-Nano
)
configurable_model.invoke(
    "what's your name",
    config={"configurable": {"model": "claude-sonnet-4-5-20250929"}},  # Run with Claude
)

Configurable model with default valuesWe can create a configurable model with default model values, specify which parameters are configurable, and add prefixes to configurable params:Copyfirst_model = init_chat_model(
        model="gpt-4.1-mini",
        temperature=0,
        configurable_fields=("model", "model_provider", "temperature", "max_tokens"),
        config_prefix="first",  # Useful when you have a chain with multiple models
)

first_model.invoke("what's your name")
Copyfirst_model.invoke(
    "what's your name",
    config={
        "configurable": {
            "first_model": "claude-sonnet-4-5-20250929",
            "first_temperature": 0.5,
            "first_max_tokens": 100,
        }
    },
)
See the init_chat_model reference for more details on configurable_fields and config_prefix.

Using a configurable model declarativelyWe can call declarative operations like bind_tools, with_structured_output, with_configurable, etc. on a configurable model and chain a configurable model in the same way that we would a regularly instantiated chat model object.Copyfrom pydantic import BaseModel, Field

class GetWeather(BaseModel):
    """Get the current weather in a given location"""

        location: str = Field(..., description="The city and state, e.g. San Francisco, CA")

class GetPopulation(BaseModel):
    """Get the current population in a given location"""

        location: str = Field(..., description="The city and state, e.g. San Francisco, CA")

model = init_chat_model(temperature=0)
model_with_tools = model.bind_tools([GetWeather, GetPopulation])

model_with_tools.invoke(
    "what's bigger in 2024 LA or NYC", config={"configurable": {"model": "gpt-4.1-mini"}}
).tool_calls
Copy[
    {
        'name': 'GetPopulation',
        'args': {'location': 'Los Angeles, CA'},
        'id': 'call_Ga9m8FAArItEjItHmztPYA22',
        'type': 'tool_call'
    },
    {
        'name': 'GetPopulation',
        'args': {'location': 'New York, NY'},
        'id': 'call_jh2dEvBaAHRaw5JUDthOs7rt',
        'type': 'tool_call'
    }
]
Copymodel_with_tools.invoke(
    "what's bigger in 2024 LA or NYC",
    config={"configurable": {"model": "claude-sonnet-4-5-20250929"}},
).tool_calls
Copy[
    {
        'name': 'GetPopulation',
        'args': {'location': 'Los Angeles, CA'},
        'id': 'toolu_01JMufPf4F4t2zLj7miFeqXp',
        'type': 'tool_call'
    },
    {
        'name': 'GetPopulation',
        'args': {'location': 'New York City, NY'},
        'id': 'toolu_01RQBHcE8kEEbYTuuS8WqY1u',
        'type': 'tool_call'
    }
]

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```

#### Invoke

The model takes messages as input and outputs messages after generating a complete response.

#### Stream

Invoke the model, but stream the output as it is generated in real-time.

#### Batch

Send multiple requests to a model in a batch for more efficient processing.

#### ​Parameters

A chat model takes parameters that can be used to configure its behavior. The full set of supported parameters varies by model and provider, but standard ones include:

​modelstringrequiredThe name or identifier of the specific model you want to use with a provider. You can also specify both the model and its provider in a single argument using the ’:’ format, for example, ‘openai:o1’.

​api_keystringThe key required for authenticating with the model’s provider. This is usually issued when you sign up for access to the model. Often accessed by setting an environment variable.

​temperaturenumberControls the randomness of the model’s output. A higher number makes responses more creative; lower ones make them more deterministic.

​max_tokensnumberLimits the total number of tokens in the response, effectively controlling how long the output can be.

​timeoutnumberThe maximum time (in seconds) to wait for a response from the model before canceling the request.

​max_retriesnumberThe maximum number of attempts the system will make to resend a request if it fails due to issues like network timeouts or rate limits.

Using init_chat_model, pass these parameters as inline **kwargs:

Initialize using model parametersCopymodel = init_chat_model(
    "claude-sonnet-4-5-20250929",
    # Kwargs passed to the model:
    temperature=0.7,
    timeout=30,
    max_tokens=1000,
)

Each chat model integration may have additional params used to control provider-specific functionality.For example, ChatOpenAI has use_responses_api to dictate whether to use the OpenAI Responses or Completions API.To find all the parameters supported by a given chat model, head to the chat model integrations page.

#### ​Invocation

A chat model must be invoked to generate an output. There are three primary invocation methods, each suited to different use cases.

##### ​Invoke

The most straightforward way to call a model is to use invoke() with a single message or a list of messages.

Single messageCopyresponse = model.invoke("Why do parrots have colorful feathers?")
print(response)

A list of messages can be provided to a chat model to represent conversation history. Each message has a role that models use to indicate who sent the message in the conversation.

See the messages guide for more detail on roles, types, and content.

Dictionary formatCopyconversation = [
    {"role": "system", "content": "You are a helpful assistant that translates English to French."},
    {"role": "user", "content": "Translate: I love programming."},
    {"role": "assistant", "content": "J'adore la programmation."},
    {"role": "user", "content": "Translate: I love building applications."}
]

response = model.invoke(conversation)
print(response)  # AIMessage("J'adore créer des applications.")

Message objectsCopyfrom langchain.messages import HumanMessage, AIMessage, SystemMessage

conversation = [
    SystemMessage("You are a helpful assistant that translates English to French."),
    HumanMessage("Translate: I love programming."),
    AIMessage("J'adore la programmation."),
    HumanMessage("Translate: I love building applications.")
]

response = model.invoke(conversation)
print(response)  # AIMessage("J'adore créer des applications.")

If the return type of your invocation is a string, ensure that you are using a chat model as opposed to a LLM. Legacy, text-completion LLMs return strings directly. LangChain chat models are prefixed with “Chat”, e.g., ChatOpenAI(/oss/integrations/chat/openai).

##### ​Stream

Most models can stream their output content while it is being generated. By displaying output progressively, streaming significantly improves user experience, particularly for longer responses.

Calling stream() returns an iterator that yields output chunks as they are produced. You can use a loop to process each chunk in real-time:

Basic text streamingStream tool calls, reasoning, and other contentCopyfor chunk in model.stream("Why do parrots have colorful feathers?"):
    print(chunk.text, end="|", flush=True)

As opposed to invoke(), which returns a single AIMessage after the model has finished generating its full response, stream() returns multiple AIMessageChunk objects, each containing a portion of the output text. Importantly, each chunk in a stream is designed to be gathered into a full message via summation:

Construct an AIMessageCopyfull = None  # None | AIMessageChunk
for chunk in model.stream("What color is the sky?"):
    full = chunk if full is None else full + chunk
    print(full.text)

# The
# The sky
# The sky is
# The sky is typically
# The sky is typically blue
# ...

print(full.content_blocks)
# [{"type": "text", "text": "The sky is typically blue..."}]

The resulting message can be treated the same as a message that was generated with invoke() – for example, it can be aggregated into a message history and passed back to the model as conversational context.

Streaming only works if all steps in the program know how to process a stream of chunks. For instance, an application that isn’t streaming-capable would be one that needs to store the entire output in memory before it can be processed.

Advanced streaming topicsStreaming eventsLangChain chat models can also stream semantic events using astream_events().This simplifies filtering based on event types and other metadata, and will aggregate the full message in the background. See below for an example.Copyasync for event in model.astream_events("Hello"):

    if event["event"] == "on_chat_model_start":
        print(f"Input: {event['data']['input']}")

    elif event["event"] == "on_chat_model_stream":
        print(f"Token: {event['data']['chunk'].text}")

    elif event["event"] == "on_chat_model_end":
        print(f"Full message: {event['data']['output'].text}")

    else:
        pass
CopyInput: Hello
Token: Hi
Token:  there
Token: !
Token:  How
Token:  can
Token:  I
...
Full message: Hi there! How can I help today?
See the astream_events() reference for event types and other details."Auto-streaming" chat modelsLangChain simplifies streaming from chat models by automatically enabling streaming mode in certain cases, even when you’re not explicitly calling the streaming methods. This is particularly useful when you use the non-streaming invoke method but still want to stream the entire application, including intermediate results from the chat model.In LangGraph agents, for example, you can call model.invoke() within nodes, but LangChain will automatically delegate to streaming if running in a streaming mode.​How it worksWhen you invoke() a chat model, LangChain will automatically switch to an internal streaming mode if it detects that you are trying to stream the overall application. The result of the invocation will be the same as far as the code that was using invoke is concerned; however, while the chat model is being streamed, LangChain will take care of invoking on_llm_new_token events in LangChain’s callback system.Callback events allow LangGraph stream() and astream_events() to surface the chat model’s output in real-time.

​Batch

Batching a collection of independent requests to a model can significantly improve performance and reduce costs, as the processing can be done in parallel:

BatchCopyresponses = model.batch([
    "Why do parrots have colorful feathers?",
    "How do airplanes fly?",
    "What is quantum computing?"
])
for response in responses:
    print(response)

This section describes a chat model method batch(), which parallelizes model calls client-side.It is distinct from batch APIs supported by inference providers, such as OpenAI or Anthropic.

By default, batch() will only return the final output for the entire batch. If you want to receive the output for each individual input as it finishes generating, you can stream results with batch_as_completed():

Yield batch responses upon completionCopyfor response in model.batch_as_completed([
    "Why do parrots have colorful feathers?",
    "How do airplanes fly?",
    "What is quantum computing?"
]):
    print(response)

When using batch_as_completed(), results may arrive out of order. Each includes the input index for matching to reconstruct the original order as needed.

When processing a large number of inputs using batch() or batch_as_completed(), you may want to control the maximum number of parallel calls. This can be done by setting the max_concurrency attribute in the RunnableConfig dictionary.Batch with max concurrencyCopymodel.batch(
    list_of_inputs,
```
    config={
        'max_concurrency': 5,  # Limit to 5 parallel calls
    }
)
See the RunnableConfig reference for a full list of supported attributes.

For more details on batching, see the reference.

​Tool calling

Models can request to call tools that perform tasks such as fetching data from a database, searching the web, or running code. Tools are pairings of:

- A schema, including the name of the tool, a description, and/or argument definitions (often a JSON schema)
- A function or coroutine to execute.
You may hear the term “function calling”. We use this interchangeably with “tool calling”.

Here’s the basic tool calling flow between a user and a model:

To make tools that you have defined available for use by a model, you must bind them using bind_tools. In subsequent invocations, the model can choose to call any of the bound tools as needed.

Some model providers offer built-in tools that can be enabled via model or invocation parameters (e.g. ChatOpenAI, ChatAnthropic). Check the respective provider reference for details.

See the tools guide for details and other options for creating tools.

Binding user toolsCopyfrom langchain.tools import tool

@tool
def get_weather(location: str) -> str:
    """Get the weather at a location."""
    return f"It's sunny in {location}."

model_with_tools = model.bind_tools([get_weather])

response = model_with_tools.invoke("What's the weather like in Boston?")
for tool_call in response.tool_calls:
    # View tool calls made by the model
    print(f"Tool: {tool_call['name']}")
    print(f"Args: {tool_call['args']}")

When binding user-defined tools, the model’s response includes a request to execute a tool. When using a model separately from an agent, it is up to you to execute the requested tool and return the result back to the model for use in subsequent reasoning. When using an agent, the agent loop will handle the tool execution loop for you.

Below, we show some common ways you can use tool calling.

Tool execution loopWhen a model returns tool calls, you need to execute the tools and pass the results back to the model. This creates a conversation loop where the model can use tool results to generate its final response. LangChain includes agent abstractions that handle this orchestration for you.Here’s a simple example of how to do this:Tool execution loopCopy# Bind (potentially multiple) tools to the model
model_with_tools = model.bind_tools([get_weather])

# Step 1: Model generates tool calls
messages = [{"role": "user", "content": "What's the weather in Boston?"}]
ai_msg = model_with_tools.invoke(messages)
messages.append(ai_msg)

# Step 2: Execute tools and collect results
for tool_call in ai_msg.tool_calls:
    # Execute the tool with the generated arguments
    tool_result = get_weather.invoke(tool_call)
    messages.append(tool_result)

# Step 3: Pass results back to model for final response
final_response = model_with_tools.invoke(messages)
print(final_response.text)
# "The current weather in Boston is 72°F and sunny."
Each ToolMessage returned by the tool includes a tool_call_id that matches the original tool call, helping the model correlate results with requests.Forcing tool callsBy default, the model has the freedom to choose which bound tool to use based on the user’s input. However, you might want to force choosing a tool, ensuring the model uses either a particular tool or any tool from a given list:Force use of any toolForce use of specific toolsCopymodel_with_tools = model.bind_tools([tool_1], tool_choice="any")
Parallel tool callsMany models support calling multiple tools in parallel when appropriate. This allows the model to gather information from different sources simultaneously.Parallel tool callsCopymodel_with_tools = model.bind_tools([get_weather])

response = model_with_tools.invoke(
    "What's the weather in Boston and Tokyo?"
)

# The model may generate multiple tool calls
print(response.tool_calls)
# [
#   {'name': 'get_weather', 'args': {'location': 'Boston'}, 'id': 'call_1'},
#   {'name': 'get_weather', 'args': {'location': 'Tokyo'}, 'id': 'call_2'},
# ]

# Execute all tools (can be done in parallel with async)
results = []
for tool_call in response.tool_calls:
    if tool_call['name'] == 'get_weather':
        result = get_weather.invoke(tool_call)
    ...
    results.append(result)
The model intelligently determines when parallel execution is appropriate based on the independence of the requested operations.Most models supporting tool calling enable parallel tool calls by default. Some (including OpenAI and Anthropic) allow you to disable this feature. To do this, set parallel_tool_calls=False:Copymodel.bind_tools([get_weather], parallel_tool_calls=False)
Streaming tool callsWhen streaming responses, tool calls are progressively built through ToolCallChunk. This allows you to see tool calls as they’re being generated rather than waiting for the complete response.Streaming tool callsCopyfor chunk in model_with_tools.stream(
    "What's the weather in Boston and Tokyo?"
):
    # Tool call chunks arrive progressively
    for tool_chunk in chunk.tool_call_chunks:
        if name := tool_chunk.get("name"):
            print(f"Tool: {name}")
        if id_ := tool_chunk.get("id"):
            print(f"ID: {id_}")
        if args := tool_chunk.get("args"):
            print(f"Args: {args}")

# Output:
# Tool: get_weather
# ID: call_SvMlU1TVIZugrFLckFE2ceRE
# Args: {"lo
# Args: catio
# Args: n": "B
# Args: osto
# Args: n"}
# Tool: get_weather
# ID: call_QMZdy6qInx13oWKE7KhuhOLR
# Args: {"lo
# Args: catio
# Args: n": "T
# Args: okyo
# Args: "}
You can accumulate chunks to build complete tool calls:Accumulate tool callsCopygathered = None
for chunk in model_with_tools.stream("What's the weather in Boston?"):
    gathered = chunk if gathered is None else gathered + chunk
    print(gathered.tool_calls)

​Structured output

Models can be requested to provide their response in a format matching a given schema. This is useful for ensuring the output can be easily parsed and used in subsequent processing. LangChain supports multiple schema types and methods for enforcing structured output.

Pydantic TypedDict JSON SchemaPydantic models provide the richest feature set with field validation, descriptions, and nested structures.Copyfrom pydantic import BaseModel, Field

class Movie(BaseModel):
    """A movie with details."""
    title: str = Field(..., description="The title of the movie")
    year: int = Field(..., description="The year the movie was released")
    director: str = Field(..., description="The director of the movie")
    rating: float = Field(..., description="The movie's rating out of 10")

model_with_structure = model.with_structured_output(Movie)
response = model_with_structure.invoke("Provide details about the movie Inception")
print(response)  # Movie(title="Inception", year=2010, director="Christopher Nolan", rating=8.8)
TypedDict provides a simpler alternative using Python’s built-in typing, ideal when you don’t need runtime validation.Copyfrom typing_extensions import TypedDict, Annotated

class MovieDict(TypedDict):
    """A movie with details."""
    title: Annotated[str, ..., "The title of the movie"]
    year: Annotated[int, ..., "The year the movie was released"]
    director: Annotated[str, ..., "The director of the movie"]
    rating: Annotated[float, ..., "The movie's rating out of 10"]

model_with_structure = model.with_structured_output(MovieDict)
response = model_with_structure.invoke("Provide details about the movie Inception")
print(response)  # {'title': 'Inception', 'year': 2010, 'director': 'Christopher Nolan', 'rating': 8.8}
For maximum control or interoperability, you can provide a raw JSON Schema.Copyimport json

json_schema = {
    "title": "Movie",
    "description": "A movie with details",
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "The title of the movie"
        },
        "year": {
            "type": "integer",
            "description": "The year the movie was released"
        },
        "director": {
            "type": "string",
            "description": "The director of the movie"
        },
        "rating": {
            "type": "number",
            "description": "The movie's rating out of 10"
        }
    },
    "required": ["title", "year", "director", "rating"]
}

model_with_structure = model.with_structured_output(
    json_schema,
    method="json_schema",
)
response = model_with_structure.invoke("Provide details about the movie Inception")
print(response)  # {'title': 'Inception', 'year': 2010, ...}

Key considerations for structured output:
Method parameter: Some providers support different methods ('json_schema', 'function_calling', 'json_mode')

'json_schema' typically refers to dedicated structured output features offered by a provider
'function_calling' derives structured output by forcing a tool call following the given schema
'json_mode' is a precursor to 'json_schema' offered by some providers - it generates valid json, but the schema must be described in the prompt

Include raw: Use include_raw=True to get both the parsed output and the raw AI message
Validation: Pydantic models provide automatic validation, while TypedDict and JSON Schema require manual validation

Example: Message output alongside parsed structureIt can be useful to return the raw AIMessage object alongside the parsed representation to access response metadata such as token counts. To do this, set include_raw=True when calling with_structured_output:Copyfrom pydantic import BaseModel, Field

class Movie(BaseModel):
    """A movie with details."""
    title: str = Field(..., description="The title of the movie")
    year: int = Field(..., description="The year the movie was released")
    director: str = Field(..., description="The director of the movie")
    rating: float = Field(..., description="The movie's rating out of 10")

model_with_structure = model.with_structured_output(Movie, include_raw=True)
response = model_with_structure.invoke("Provide details about the movie Inception")
response
# {
#     "raw": AIMessage(...),
#     "parsed": Movie(title=..., year=..., ...),
#     "parsing_error": None,
# }

Example: Nested structuresSchemas can be nested:Pydantic BaseModelTypedDictCopyfrom pydantic import BaseModel, Field

class Actor(BaseModel):
    name: str
    role: str

class MovieDetails(BaseModel):
    title: str
    year: int
    cast: list[Actor]
    genres: list[str]
    budget: float | None = Field(None, description="Budget in millions USD")

model_with_structure = model.with_structured_output(MovieDetails)

​Supported models

LangChain supports all major model providers, including OpenAI, Anthropic, Google, Azure, AWS Bedrock, and more. Each provider offers a variety of models with different capabilities. For a full list of supported models in LangChain, see the integrations page.

​Advanced topics

​Model profiles

This is a beta feature. The format of model profiles is subject to change.

Model profiles require langchain>=1.1.

LangChain chat models can expose a dictionary of supported features and capabilities through a .profile attribute:

Copymodel.profile
# {
#   "max_input_tokens": 400000,
#   "image_inputs": True,
#   "reasoning_output": True,
#   "tool_calling": True,
#   ...
# }

Refer to the full set of fields in the API reference.

Much of the model profile data is powered by the models.dev project, an open source initiative that provides model capability data. These data are augmented with additional fields for purposes of use with LangChain. These augmentations are kept aligned with the upstream project as it evolves.

Model profile data allow applications to work around model capabilities dynamically. For example:

- Summarization middleware can trigger summarization based on a model’s context window size.
- Structured output strategies in create_agent can be inferred automatically (e.g., by checking support for native structured output features).
- Model inputs can be gated based on supported modalities and maximum input tokens.
Updating or overwriting profile dataModel profile data can be changed if it is missing, stale, or incorrect.Option 1 (quick fix)You can instantiate a chat model with any valid profile:Copycustom_profile = {
    "max_input_tokens": 100_000,
    "tool_calling": True,
    "structured_output": True,
    # ...
}
model = init_chat_model("...", profile=custom_profile)
The profile is also a regular dict and can be updated in place. If the model instance is shared, consider using model_copy to avoid mutating shared state.Copynew_profile = model.profile | {"key": "value"}
model.model_copy(update={"profile": new_profile})
Option 2 (fix data upstream)The primary source for the data is the models.dev project. This data is merged with additional fields and overrides in LangChain integration packages and are shipped with those packages.Model profile data can be updated through the following process:
(If needed) update the source data at models.dev through a pull request to its repository on GitHub.
(If needed) update additional fields and overrides in langchain_<package>/data/profile_augmentations.toml through a pull request to the LangChain integration package`.
Use the langchain-model-profiles CLI tool to pull the latest data from models.dev, merge in the augmentations and update the profile data:
Copypip install langchain-model-profiles
Copylangchain-profiles refresh --provider <provider> --data-dir <data_dir>
This command:
Downloads the latest data for <provider> from models.dev
Merges augmentations from profile_augmentations.toml in <data_dir>
Writes merged profiles to profiles.py in <data_dir>
For example: from libs/partners/anthropic in the LangChain monorepo:Copyuv run --with langchain-model-profiles --provider anthropic --data-dir langchain_anthropic/data

​Multimodal

Certain models can process and return non-textual data such as images, audio, and video. You can pass non-textual data to a model by providing content blocks.

All LangChain chat models with underlying multimodal capabilities support:
Data in the cross-provider standard format (see our messages guide)
OpenAI chat completions format
Any format that is native to that specific provider (e.g., Anthropic models accept Anthropic native format)

See the multimodal section of the messages guide for details.

Some models can return multimodal data as part of their response. If invoked to do so, the resulting AIMessage will have content blocks with multimodal types.

Multimodal outputCopyresponse = model.invoke("Create a picture of a cat")
print(response.content_blocks)
# [
#     {"type": "text", "text": "Here's a picture of a cat"},
#     {"type": "image", "base64": "...", "mime_type": "image/jpeg"},
# ]

See the integrations page for details on specific providers.

​Reasoning

Many models are capable of performing multi-step reasoning to arrive at a conclusion. This involves breaking down complex problems into smaller, more manageable steps.

If supported by the underlying model, you can surface this reasoning process to better understand how the model arrived at its final answer.

Stream reasoning outputComplete reasoning outputCopyfor chunk in model.stream("Why do parrots have colorful feathers?"):
    reasoning_steps = [r for r in chunk.content_blocks if r["type"] == "reasoning"]
    print(reasoning_steps if reasoning_steps else chunk.text)

Depending on the model, you can sometimes specify the level of effort it should put into reasoning. Similarly, you can request that the model turn off reasoning entirely. This may take the form of categorical “tiers” of reasoning (e.g., 'low' or 'high') or integer token budgets.

For details, see the integrations page or reference for your respective chat model.

​Local models

LangChain supports running models locally on your own hardware. This is useful for scenarios where either data privacy is critical, you want to invoke a custom model, or when you want to avoid the costs incurred when using a cloud-based model.

Ollama is one of the easiest ways to run models locally. See the full list of local integrations on the integrations page.

​Prompt caching

Many providers offer prompt caching features to reduce latency and cost on repeat processing of the same tokens. These features can be implicit or explicit:

- Implicit prompt caching: providers will automatically pass on cost savings if a request hits a cache. Examples: OpenAI and Gemini.
- Explicit caching: providers allow you to manually indicate cache points for greater control or to guarantee cost savings. Examples:

ChatOpenAI (via prompt_cache_key)
Anthropic’s AnthropicPromptCachingMiddleware
Gemini.
AWS Bedrock
- ChatOpenAI (via prompt_cache_key)
- Anthropic’s AnthropicPromptCachingMiddleware
- Gemini.
- AWS Bedrock
Prompt caching is often only engaged above a minimum input token threshold. See provider pages for details.

Cache usage will be reflected in the usage metadata of the model response.

​Server-side tool use

Some providers support server-side tool-calling loops: models can interact with web search, code interpreters, and other tools and analyze the results in a single conversational turn.

If a model invokes a tool server-side, the content of the response message will include content representing the invocation and result of the tool. Accessing the content blocks of the response will return the server-side tool calls and results in a provider-agnostic format:

Invoke with server-side tool useCopyfrom langchain.chat_models import init_chat_model

model = init_chat_model("gpt-4.1-mini")

tool = {"type": "web_search"}
model_with_tools = model.bind_tools([tool])

response = model_with_tools.invoke("What was a positive news story from today?")
response.content_blocks

ResultCopy[
    {
        "type": "server_tool_call",
        "name": "web_search",
        "args": {
            "query": "positive news stories today",
            "type": "search"
        },
        "id": "ws_abc123"
    },
    {
        "type": "server_tool_result",
        "tool_call_id": "ws_abc123",
        "status": "success"
    },
    {
        "type": "text",
        "text": "Here are some positive news stories from today...",
        "annotations": [
            {
                "end_index": 410,
                "start_index": 337,
                "title": "article title",
                "type": "citation",
                "url": "..."
            }
        ]
    }
]
See all 29 lines

This represents a single conversational turn; there are no associated ToolMessage objects that need to be passed in as in client-side tool-calling.

See the integration page for your given provider for available tools and usage details.

​Rate limiting

Many chat model providers impose a limit on the number of invocations that can be made in a given time period. If you hit a rate limit, you will typically receive a rate limit error response from the provider, and will need to wait before making more requests.

To help manage rate limits, chat model integrations accept a rate_limiter parameter that can be provided during initialization to control the rate at which requests are made.

Initialize and use a rate limiterLangChain in comes with (an optional) built-in InMemoryRateLimiter. This limiter is thread safe and can be shared by multiple threads in the same process.Define a rate limiterCopyfrom langchain_core.rate_limiters import InMemoryRateLimiter

rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.1,  # 1 request every 10s
    check_every_n_seconds=0.1,  # Check every 100ms whether allowed to make a request
    max_bucket_size=10,  # Controls the maximum burst size.
)

model = init_chat_model(
    model="gpt-5",
    model_provider="openai",
    rate_limiter=rate_limiter
)
The provided rate limiter can only limit the number of requests per unit time. It will not help if you need to also limit based on the size of the requests.

​Base URL or proxy

For many chat model integrations, you can configure the base URL for API requests, which allows you to use model providers that have OpenAI-compatible APIs or to use a proxy server.

Base URLMany model providers offer OpenAI-compatible APIs (e.g., Together AI, vLLM). You can use init_chat_model with these providers by specifying the appropriate base_url parameter:Copymodel = init_chat_model(
    model="MODEL_NAME",
    model_provider="openai",
    base_url="BASE_URL",
    api_key="YOUR_API_KEY",
)
When using direct chat model class instantiation, the parameter name may vary by provider. Check the respective reference for details.

Proxy configurationFor deployments requiring HTTP proxies, some model integrations support proxy configuration:Copyfrom langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="gpt-4o",
    openai_proxy="http://proxy.example.com:8080"
)
Proxy support varies by integration. Check the specific model provider’s reference for proxy configuration options.

​Log probabilities

Certain models can be configured to return token-level log probabilities representing the likelihood of a given token by setting the logprobs parameter when initializing the model:

Copymodel = init_chat_model(
    model="gpt-4o",
    model_provider="openai"
).bind(logprobs=True)

response = model.invoke("Why do parrots talk?")
print(response.response_metadata["logprobs"])

​Token usage

A number of model providers return token usage information as part of the invocation response. When available, this information will be included on the AIMessage objects produced by the corresponding model. For more details, see the messages guide.

Some provider APIs, notably OpenAI and Azure OpenAI chat completions, require users opt-in to receiving token usage data in streaming contexts. See the streaming usage metadata section of the integration guide for details.

You can track aggregate token counts across models in an application using either a callback or context manager, as shown below:

Callback handler Context managerCopyfrom langchain.chat_models import init_chat_model
from langchain_core.callbacks import UsageMetadataCallbackHandler

model_1 = init_chat_model(model="gpt-4o-mini")
model_2 = init_chat_model(model="claude-haiku-4-5-20251001")

callback = UsageMetadataCallbackHandler()
result_1 = model_1.invoke("Hello", config={"callbacks": [callback]})
result_2 = model_2.invoke("Hello", config={"callbacks": [callback]})
callback.usage_metadata
Copy{
    'gpt-4o-mini-2024-07-18': {
        'input_tokens': 8,
        'output_tokens': 10,
        'total_tokens': 18,
        'input_token_details': {'audio': 0, 'cache_read': 0},
        'output_token_details': {'audio': 0, 'reasoning': 0}
    },
    'claude-haiku-4-5-20251001': {
        'input_tokens': 8,
        'output_tokens': 21,
        'total_tokens': 29,
        'input_token_details': {'cache_read': 0, 'cache_creation': 0}
    }
}
Copyfrom langchain.chat_models import init_chat_model
from langchain_core.callbacks import get_usage_metadata_callback

model_1 = init_chat_model(model="gpt-4o-mini")
model_2 = init_chat_model(model="claude-haiku-4-5-20251001")

with get_usage_metadata_callback() as cb:
    model_1.invoke("Hello")
    model_2.invoke("Hello")
    print(cb.usage_metadata)
Copy{
    'gpt-4o-mini-2024-07-18': {
        'input_tokens': 8,
        'output_tokens': 10,
        'total_tokens': 18,
        'input_token_details': {'audio': 0, 'cache_read': 0},
        'output_token_details': {'audio': 0, 'reasoning': 0}
    },
    'claude-haiku-4-5-20251001': {
        'input_tokens': 8,
        'output_tokens': 21,
        'total_tokens': 29,
        'input_token_details': {'cache_read': 0, 'cache_creation': 0}
    }
}

​Invocation config

When invoking a model, you can pass additional configuration through the config parameter using a RunnableConfig dictionary. This provides run-time control over execution behavior, callbacks, and metadata tracking.

Common configuration options include:

Invocation with configCopyresponse = model.invoke(
    "Tell me a joke",
    config={
        "run_name": "joke_generation",      # Custom name for this run
        "tags": ["humor", "demo"],          # Tags for categorization
        "metadata": {"user_id": "123"},     # Custom metadata
        "callbacks": [my_callback_handler], # Callback handlers
    }
)

These configuration values are particularly useful when:

- Debugging with LangSmith tracing
- Implementing custom logging or monitoring
- Controlling resource usage in production
- Tracking invocations across complex pipelines
Key configuration attributes​run_namestringIdentifies this specific invocation in logs and traces. Not inherited by sub-calls.​tagsstring[]Labels inherited by all sub-calls for filtering and organization in debugging tools.​metadataobjectCustom key-value pairs for tracking additional context, inherited by all sub-calls.​max_concurrencynumberControls the maximum number of parallel calls when using batch() or batch_as_completed().​callbacksarrayHandlers for monitoring and responding to events during execution.​recursion_limitnumberMaximum recursion depth for chains to prevent infinite loops in complex pipelines.

See full RunnableConfig reference for all supported attributes.

​Configurable models

You can also create a runtime-configurable model by specifying configurable_fields. If you don’t specify a model value, then 'model' and 'model_provider' will be configurable by default.

Copyfrom langchain.chat_models import init_chat_model

configurable_model = init_chat_model(temperature=0)

configurable_model.invoke(
    "what's your name",
    config={"configurable": {"model": "gpt-5-nano"}},  # Run with GPT-5-Nano
)
configurable_model.invoke(
    "what's your name",
    config={"configurable": {"model": "claude-sonnet-4-5-20250929"}},  # Run with Claude
)

Configurable model with default valuesWe can create a configurable model with default model values, specify which parameters are configurable, and add prefixes to configurable params:Copyfirst_model = init_chat_model(
        model="gpt-4.1-mini",
        temperature=0,
        configurable_fields=("model", "model_provider", "temperature", "max_tokens"),
        config_prefix="first",  # Useful when you have a chain with multiple models
)

first_model.invoke("what's your name")
Copyfirst_model.invoke(
    "what's your name",
    config={
        "configurable": {
            "first_model": "claude-sonnet-4-5-20250929",
            "first_temperature": 0.5,
            "first_max_tokens": 100,
        }
    },
)
See the init_chat_model reference for more details on configurable_fields and config_prefix.

Using a configurable model declarativelyWe can call declarative operations like bind_tools, with_structured_output, with_configurable, etc. on a configurable model and chain a configurable model in the same way that we would a regularly instantiated chat model object.Copyfrom pydantic import BaseModel, Field

class GetWeather(BaseModel):
    """Get the current weather in a given location"""

        location: str = Field(..., description="The city and state, e.g. San Francisco, CA")

class GetPopulation(BaseModel):
    """Get the current population in a given location"""

        location: str = Field(..., description="The city and state, e.g. San Francisco, CA")

model = init_chat_model(temperature=0)
model_with_tools = model.bind_tools([GetWeather, GetPopulation])

model_with_tools.invoke(
    "what's bigger in 2024 LA or NYC", config={"configurable": {"model": "gpt-4.1-mini"}}
).tool_calls
Copy[
    {
        'name': 'GetPopulation',
        'args': {'location': 'Los Angeles, CA'},
        'id': 'call_Ga9m8FAArItEjItHmztPYA22',
        'type': 'tool_call'
    },
    {
        'name': 'GetPopulation',
        'args': {'location': 'New York, NY'},
        'id': 'call_jh2dEvBaAHRaw5JUDthOs7rt',
        'type': 'tool_call'
    }
]
Copymodel_with_tools.invoke(
    "what's bigger in 2024 LA or NYC",
    config={"configurable": {"model": "claude-sonnet-4-5-20250929"}},
).tool_calls
Copy[
    {
        'name': 'GetPopulation',
        'args': {'location': 'Los Angeles, CA'},
        'id': 'toolu_01JMufPf4F4t2zLj7miFeqXp',
        'type': 'tool_call'
    },
    {
        'name': 'GetPopulation',
        'args': {'location': 'New York City, NY'},
        'id': 'toolu_01RQBHcE8kEEbYTuuS8WqY1u',
        'type': 'tool_call'
    }
]

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```

###### ​How it works

When you invoke() a chat model, LangChain will automatically switch to an internal streaming mode if it detects that you are trying to stream the overall application. The result of the invocation will be the same as far as the code that was using invoke is concerned; however, while the chat model is being streamed, LangChain will take care of invoking on_llm_new_token events in LangChain’s callback system.

Callback events allow LangGraph stream() and astream_events() to surface the chat model’s output in real-time.

##### ​Batch

Batching a collection of independent requests to a model can significantly improve performance and reduce costs, as the processing can be done in parallel:

BatchCopyresponses = model.batch([
    "Why do parrots have colorful feathers?",
    "How do airplanes fly?",
    "What is quantum computing?"
])
for response in responses:
    print(response)

This section describes a chat model method batch(), which parallelizes model calls client-side.It is distinct from batch APIs supported by inference providers, such as OpenAI or Anthropic.

By default, batch() will only return the final output for the entire batch. If you want to receive the output for each individual input as it finishes generating, you can stream results with batch_as_completed():

Yield batch responses upon completionCopyfor response in model.batch_as_completed([
    "Why do parrots have colorful feathers?",
    "How do airplanes fly?",
    "What is quantum computing?"
]):
    print(response)

When using batch_as_completed(), results may arrive out of order. Each includes the input index for matching to reconstruct the original order as needed.

When processing a large number of inputs using batch() or batch_as_completed(), you may want to control the maximum number of parallel calls. This can be done by setting the max_concurrency attribute in the RunnableConfig dictionary.Batch with max concurrencyCopymodel.batch(
    list_of_inputs,
```
    config={
        'max_concurrency': 5,  # Limit to 5 parallel calls
    }
)
See the RunnableConfig reference for a full list of supported attributes.

For more details on batching, see the reference.
```

#### ​Tool calling

Models can request to call tools that perform tasks such as fetching data from a database, searching the web, or running code. Tools are pairings of:

- A schema, including the name of the tool, a description, and/or argument definitions (often a JSON schema)
- A function or coroutine to execute.
You may hear the term “function calling”. We use this interchangeably with “tool calling”.

Here’s the basic tool calling flow between a user and a model:

To make tools that you have defined available for use by a model, you must bind them using bind_tools. In subsequent invocations, the model can choose to call any of the bound tools as needed.

Some model providers offer built-in tools that can be enabled via model or invocation parameters (e.g. ChatOpenAI, ChatAnthropic). Check the respective provider reference for details.

See the tools guide for details and other options for creating tools.

Binding user toolsCopyfrom langchain.tools import tool

```python
@tool
def get_weather(location: str) -> str:
    """Get the weather at a location."""
    return f"It's sunny in {location}."

model_with_tools = model.bind_tools([get_weather])

response = model_with_tools.invoke("What's the weather like in Boston?")
for tool_call in response.tool_calls:
    # View tool calls made by the model
    print(f"Tool: {tool_call['name']}")
    print(f"Args: {tool_call['args']}")

When binding user-defined tools, the model’s response includes a request to execute a tool. When using a model separately from an agent, it is up to you to execute the requested tool and return the result back to the model for use in subsequent reasoning. When using an agent, the agent loop will handle the tool execution loop for you.

Below, we show some common ways you can use tool calling.

Tool execution loopWhen a model returns tool calls, you need to execute the tools and pass the results back to the model. This creates a conversation loop where the model can use tool results to generate its final response. LangChain includes agent abstractions that handle this orchestration for you.Here’s a simple example of how to do this:Tool execution loopCopy# Bind (potentially multiple) tools to the model
model_with_tools = model.bind_tools([get_weather])

# Step 1: Model generates tool calls
messages = [{"role": "user", "content": "What's the weather in Boston?"}]
ai_msg = model_with_tools.invoke(messages)
messages.append(ai_msg)

# Step 2: Execute tools and collect results
for tool_call in ai_msg.tool_calls:
    # Execute the tool with the generated arguments
    tool_result = get_weather.invoke(tool_call)
    messages.append(tool_result)

# Step 3: Pass results back to model for final response
final_response = model_with_tools.invoke(messages)
print(final_response.text)
# "The current weather in Boston is 72°F and sunny."
Each ToolMessage returned by the tool includes a tool_call_id that matches the original tool call, helping the model correlate results with requests.Forcing tool callsBy default, the model has the freedom to choose which bound tool to use based on the user’s input. However, you might want to force choosing a tool, ensuring the model uses either a particular tool or any tool from a given list:Force use of any toolForce use of specific toolsCopymodel_with_tools = model.bind_tools([tool_1], tool_choice="any")
Parallel tool callsMany models support calling multiple tools in parallel when appropriate. This allows the model to gather information from different sources simultaneously.Parallel tool callsCopymodel_with_tools = model.bind_tools([get_weather])

response = model_with_tools.invoke(
    "What's the weather in Boston and Tokyo?"
)

# The model may generate multiple tool calls
print(response.tool_calls)
# [
#   {'name': 'get_weather', 'args': {'location': 'Boston'}, 'id': 'call_1'},
#   {'name': 'get_weather', 'args': {'location': 'Tokyo'}, 'id': 'call_2'},
# ]

# Execute all tools (can be done in parallel with async)
results = []
for tool_call in response.tool_calls:
    if tool_call['name'] == 'get_weather':
        result = get_weather.invoke(tool_call)
    ...
    results.append(result)
The model intelligently determines when parallel execution is appropriate based on the independence of the requested operations.Most models supporting tool calling enable parallel tool calls by default. Some (including OpenAI and Anthropic) allow you to disable this feature. To do this, set parallel_tool_calls=False:Copymodel.bind_tools([get_weather], parallel_tool_calls=False)
Streaming tool callsWhen streaming responses, tool calls are progressively built through ToolCallChunk. This allows you to see tool calls as they’re being generated rather than waiting for the complete response.Streaming tool callsCopyfor chunk in model_with_tools.stream(
    "What's the weather in Boston and Tokyo?"
):
    # Tool call chunks arrive progressively
    for tool_chunk in chunk.tool_call_chunks:
        if name := tool_chunk.get("name"):
            print(f"Tool: {name}")
        if id_ := tool_chunk.get("id"):
            print(f"ID: {id_}")
        if args := tool_chunk.get("args"):
            print(f"Args: {args}")

# Output:
# Tool: get_weather
# ID: call_SvMlU1TVIZugrFLckFE2ceRE
# Args: {"lo
# Args: catio
# Args: n": "B
# Args: osto
# Args: n"}
# Tool: get_weather
# ID: call_QMZdy6qInx13oWKE7KhuhOLR
# Args: {"lo
# Args: catio
# Args: n": "T
# Args: okyo
# Args: "}
You can accumulate chunks to build complete tool calls:Accumulate tool callsCopygathered = None
for chunk in model_with_tools.stream("What's the weather in Boston?"):
    gathered = chunk if gathered is None else gathered + chunk
    print(gathered.tool_calls)
```

#### ​Structured output

Models can be requested to provide their response in a format matching a given schema. This is useful for ensuring the output can be easily parsed and used in subsequent processing. LangChain supports multiple schema types and methods for enforcing structured output.

Pydantic TypedDict JSON SchemaPydantic models provide the richest feature set with field validation, descriptions, and nested structures.Copyfrom pydantic import BaseModel, Field

```python
class Movie(BaseModel):
    """A movie with details."""
    title: str = Field(..., description="The title of the movie")
    year: int = Field(..., description="The year the movie was released")
    director: str = Field(..., description="The director of the movie")
    rating: float = Field(..., description="The movie's rating out of 10")

model_with_structure = model.with_structured_output(Movie)
response = model_with_structure.invoke("Provide details about the movie Inception")
print(response)  # Movie(title="Inception", year=2010, director="Christopher Nolan", rating=8.8)
TypedDict provides a simpler alternative using Python’s built-in typing, ideal when you don’t need runtime validation.Copyfrom typing_extensions import TypedDict, Annotated

class MovieDict(TypedDict):
    """A movie with details."""
    title: Annotated[str, ..., "The title of the movie"]
    year: Annotated[int, ..., "The year the movie was released"]
    director: Annotated[str, ..., "The director of the movie"]
    rating: Annotated[float, ..., "The movie's rating out of 10"]

model_with_structure = model.with_structured_output(MovieDict)
response = model_with_structure.invoke("Provide details about the movie Inception")
print(response)  # {'title': 'Inception', 'year': 2010, 'director': 'Christopher Nolan', 'rating': 8.8}
For maximum control or interoperability, you can provide a raw JSON Schema.Copyimport json

json_schema = {
    "title": "Movie",
    "description": "A movie with details",
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "The title of the movie"
        },
        "year": {
            "type": "integer",
            "description": "The year the movie was released"
        },
        "director": {
            "type": "string",
            "description": "The director of the movie"
        },
        "rating": {
            "type": "number",
            "description": "The movie's rating out of 10"
        }
    },
    "required": ["title", "year", "director", "rating"]
}

model_with_structure = model.with_structured_output(
    json_schema,
    method="json_schema",
)
response = model_with_structure.invoke("Provide details about the movie Inception")
print(response)  # {'title': 'Inception', 'year': 2010, ...}

Key considerations for structured output:
Method parameter: Some providers support different methods ('json_schema', 'function_calling', 'json_mode')

'json_schema' typically refers to dedicated structured output features offered by a provider
'function_calling' derives structured output by forcing a tool call following the given schema
'json_mode' is a precursor to 'json_schema' offered by some providers - it generates valid json, but the schema must be described in the prompt

Include raw: Use include_raw=True to get both the parsed output and the raw AI message
Validation: Pydantic models provide automatic validation, while TypedDict and JSON Schema require manual validation

Example: Message output alongside parsed structureIt can be useful to return the raw AIMessage object alongside the parsed representation to access response metadata such as token counts. To do this, set include_raw=True when calling with_structured_output:Copyfrom pydantic import BaseModel, Field

class Movie(BaseModel):
    """A movie with details."""
    title: str = Field(..., description="The title of the movie")
    year: int = Field(..., description="The year the movie was released")
    director: str = Field(..., description="The director of the movie")
    rating: float = Field(..., description="The movie's rating out of 10")

model_with_structure = model.with_structured_output(Movie, include_raw=True)
response = model_with_structure.invoke("Provide details about the movie Inception")
response
# {
#     "raw": AIMessage(...),
#     "parsed": Movie(title=..., year=..., ...),
#     "parsing_error": None,
# }

Example: Nested structuresSchemas can be nested:Pydantic BaseModelTypedDictCopyfrom pydantic import BaseModel, Field

class Actor(BaseModel):
    name: str
    role: str

class MovieDetails(BaseModel):
    title: str
    year: int
    cast: list[Actor]
    genres: list[str]
    budget: float | None = Field(None, description="Budget in millions USD")

model_with_structure = model.with_structured_output(MovieDetails)
```

#### ​Supported models

LangChain supports all major model providers, including OpenAI, Anthropic, Google, Azure, AWS Bedrock, and more. Each provider offers a variety of models with different capabilities. For a full list of supported models in LangChain, see the integrations page.

#### ​Advanced topics

##### ​Model profiles

This is a beta feature. The format of model profiles is subject to change.

Model profiles require langchain>=1.1.

LangChain chat models can expose a dictionary of supported features and capabilities through a .profile attribute:

Copymodel.profile
```
# {
#   "max_input_tokens": 400000,
#   "image_inputs": True,
#   "reasoning_output": True,
#   "tool_calling": True,
#   ...
# }

Refer to the full set of fields in the API reference.

Much of the model profile data is powered by the models.dev project, an open source initiative that provides model capability data. These data are augmented with additional fields for purposes of use with LangChain. These augmentations are kept aligned with the upstream project as it evolves.

Model profile data allow applications to work around model capabilities dynamically. For example:

- Summarization middleware can trigger summarization based on a model’s context window size.
- Structured output strategies in create_agent can be inferred automatically (e.g., by checking support for native structured output features).
- Model inputs can be gated based on supported modalities and maximum input tokens.
Updating or overwriting profile dataModel profile data can be changed if it is missing, stale, or incorrect.Option 1 (quick fix)You can instantiate a chat model with any valid profile:Copycustom_profile = {
    "max_input_tokens": 100_000,
    "tool_calling": True,
    "structured_output": True,
    # ...
}
model = init_chat_model("...", profile=custom_profile)
The profile is also a regular dict and can be updated in place. If the model instance is shared, consider using model_copy to avoid mutating shared state.Copynew_profile = model.profile | {"key": "value"}
model.model_copy(update={"profile": new_profile})
Option 2 (fix data upstream)The primary source for the data is the models.dev project. This data is merged with additional fields and overrides in LangChain integration packages and are shipped with those packages.Model profile data can be updated through the following process:
(If needed) update the source data at models.dev through a pull request to its repository on GitHub.
(If needed) update additional fields and overrides in langchain_<package>/data/profile_augmentations.toml through a pull request to the LangChain integration package`.
Use the langchain-model-profiles CLI tool to pull the latest data from models.dev, merge in the augmentations and update the profile data:
Copypip install langchain-model-profiles
Copylangchain-profiles refresh --provider <provider> --data-dir <data_dir>
This command:
Downloads the latest data for <provider> from models.dev
Merges augmentations from profile_augmentations.toml in <data_dir>
Writes merged profiles to profiles.py in <data_dir>
For example: from libs/partners/anthropic in the LangChain monorepo:Copyuv run --with langchain-model-profiles --provider anthropic --data-dir langchain_anthropic/data
```

##### ​Multimodal

Certain models can process and return non-textual data such as images, audio, and video. You can pass non-textual data to a model by providing content blocks.

All LangChain chat models with underlying multimodal capabilities support:
Data in the cross-provider standard format (see our messages guide)
OpenAI chat completions format
Any format that is native to that specific provider (e.g., Anthropic models accept Anthropic native format)

See the multimodal section of the messages guide for details.

Some models can return multimodal data as part of their response. If invoked to do so, the resulting AIMessage will have content blocks with multimodal types.

Multimodal outputCopyresponse = model.invoke("Create a picture of a cat")
print(response.content_blocks)
# [
#     {"type": "text", "text": "Here's a picture of a cat"},
#     {"type": "image", "base64": "...", "mime_type": "image/jpeg"},
# ]

See the integrations page for details on specific providers.

##### ​Reasoning

Many models are capable of performing multi-step reasoning to arrive at a conclusion. This involves breaking down complex problems into smaller, more manageable steps.

If supported by the underlying model, you can surface this reasoning process to better understand how the model arrived at its final answer.

Stream reasoning outputComplete reasoning outputCopyfor chunk in model.stream("Why do parrots have colorful feathers?"):
    reasoning_steps = [r for r in chunk.content_blocks if r["type"] == "reasoning"]
    print(reasoning_steps if reasoning_steps else chunk.text)

Depending on the model, you can sometimes specify the level of effort it should put into reasoning. Similarly, you can request that the model turn off reasoning entirely. This may take the form of categorical “tiers” of reasoning (e.g., 'low' or 'high') or integer token budgets.

For details, see the integrations page or reference for your respective chat model.

##### ​Local models

LangChain supports running models locally on your own hardware. This is useful for scenarios where either data privacy is critical, you want to invoke a custom model, or when you want to avoid the costs incurred when using a cloud-based model.

Ollama is one of the easiest ways to run models locally. See the full list of local integrations on the integrations page.

##### ​Prompt caching

Many providers offer prompt caching features to reduce latency and cost on repeat processing of the same tokens. These features can be implicit or explicit:

- Implicit prompt caching: providers will automatically pass on cost savings if a request hits a cache. Examples: OpenAI and Gemini.
- Explicit caching: providers allow you to manually indicate cache points for greater control or to guarantee cost savings. Examples:

ChatOpenAI (via prompt_cache_key)
Anthropic’s AnthropicPromptCachingMiddleware
Gemini.
AWS Bedrock
- ChatOpenAI (via prompt_cache_key)
- Anthropic’s AnthropicPromptCachingMiddleware
- Gemini.
- AWS Bedrock
Prompt caching is often only engaged above a minimum input token threshold. See provider pages for details.

Cache usage will be reflected in the usage metadata of the model response.

##### ​Server-side tool use

Some providers support server-side tool-calling loops: models can interact with web search, code interpreters, and other tools and analyze the results in a single conversational turn.

If a model invokes a tool server-side, the content of the response message will include content representing the invocation and result of the tool. Accessing the content blocks of the response will return the server-side tool calls and results in a provider-agnostic format:

Invoke with server-side tool useCopyfrom langchain.chat_models import init_chat_model

model = init_chat_model("gpt-4.1-mini")

tool = {"type": "web_search"}
model_with_tools = model.bind_tools([tool])

response = model_with_tools.invoke("What was a positive news story from today?")
response.content_blocks

ResultCopy[
```
    {
        "type": "server_tool_call",
        "name": "web_search",
        "args": {
            "query": "positive news stories today",
            "type": "search"
        },
        "id": "ws_abc123"
    },
    {
        "type": "server_tool_result",
        "tool_call_id": "ws_abc123",
        "status": "success"
    },
    {
        "type": "text",
        "text": "Here are some positive news stories from today...",
        "annotations": [
            {
                "end_index": 410,
                "start_index": 337,
                "title": "article title",
                "type": "citation",
                "url": "..."
            }
        ]
    }
]
See all 29 lines

This represents a single conversational turn; there are no associated ToolMessage objects that need to be passed in as in client-side tool-calling.

See the integration page for your given provider for available tools and usage details.
```

##### ​Rate limiting

Many chat model providers impose a limit on the number of invocations that can be made in a given time period. If you hit a rate limit, you will typically receive a rate limit error response from the provider, and will need to wait before making more requests.

To help manage rate limits, chat model integrations accept a rate_limiter parameter that can be provided during initialization to control the rate at which requests are made.

Initialize and use a rate limiterLangChain in comes with (an optional) built-in InMemoryRateLimiter. This limiter is thread safe and can be shared by multiple threads in the same process.Define a rate limiterCopyfrom langchain_core.rate_limiters import InMemoryRateLimiter

rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.1,  # 1 request every 10s
    check_every_n_seconds=0.1,  # Check every 100ms whether allowed to make a request
    max_bucket_size=10,  # Controls the maximum burst size.
)

model = init_chat_model(
    model="gpt-5",
    model_provider="openai",
    rate_limiter=rate_limiter
)
The provided rate limiter can only limit the number of requests per unit time. It will not help if you need to also limit based on the size of the requests.

##### ​Base URL or proxy

For many chat model integrations, you can configure the base URL for API requests, which allows you to use model providers that have OpenAI-compatible APIs or to use a proxy server.

Base URLMany model providers offer OpenAI-compatible APIs (e.g., Together AI, vLLM). You can use init_chat_model with these providers by specifying the appropriate base_url parameter:Copymodel = init_chat_model(
    model="MODEL_NAME",
    model_provider="openai",
    base_url="BASE_URL",
    api_key="YOUR_API_KEY",
)
When using direct chat model class instantiation, the parameter name may vary by provider. Check the respective reference for details.

Proxy configurationFor deployments requiring HTTP proxies, some model integrations support proxy configuration:Copyfrom langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="gpt-4o",
    openai_proxy="http://proxy.example.com:8080"
)
Proxy support varies by integration. Check the specific model provider’s reference for proxy configuration options.

##### ​Log probabilities

Certain models can be configured to return token-level log probabilities representing the likelihood of a given token by setting the logprobs parameter when initializing the model:

Copymodel = init_chat_model(
    model="gpt-4o",
    model_provider="openai"
).bind(logprobs=True)

response = model.invoke("Why do parrots talk?")
print(response.response_metadata["logprobs"])

##### ​Token usage

A number of model providers return token usage information as part of the invocation response. When available, this information will be included on the AIMessage objects produced by the corresponding model. For more details, see the messages guide.

Some provider APIs, notably OpenAI and Azure OpenAI chat completions, require users opt-in to receiving token usage data in streaming contexts. See the streaming usage metadata section of the integration guide for details.

You can track aggregate token counts across models in an application using either a callback or context manager, as shown below:

Callback handler Context managerCopyfrom langchain.chat_models import init_chat_model
```python
from langchain_core.callbacks import UsageMetadataCallbackHandler

model_1 = init_chat_model(model="gpt-4o-mini")
model_2 = init_chat_model(model="claude-haiku-4-5-20251001")

callback = UsageMetadataCallbackHandler()
result_1 = model_1.invoke("Hello", config={"callbacks": [callback]})
result_2 = model_2.invoke("Hello", config={"callbacks": [callback]})
callback.usage_metadata
Copy{
    'gpt-4o-mini-2024-07-18': {
        'input_tokens': 8,
        'output_tokens': 10,
        'total_tokens': 18,
        'input_token_details': {'audio': 0, 'cache_read': 0},
        'output_token_details': {'audio': 0, 'reasoning': 0}
    },
    'claude-haiku-4-5-20251001': {
        'input_tokens': 8,
        'output_tokens': 21,
        'total_tokens': 29,
        'input_token_details': {'cache_read': 0, 'cache_creation': 0}
    }
}
Copyfrom langchain.chat_models import init_chat_model
from langchain_core.callbacks import get_usage_metadata_callback

model_1 = init_chat_model(model="gpt-4o-mini")
model_2 = init_chat_model(model="claude-haiku-4-5-20251001")

with get_usage_metadata_callback() as cb:
    model_1.invoke("Hello")
    model_2.invoke("Hello")
    print(cb.usage_metadata)
Copy{
    'gpt-4o-mini-2024-07-18': {
        'input_tokens': 8,
        'output_tokens': 10,
        'total_tokens': 18,
        'input_token_details': {'audio': 0, 'cache_read': 0},
        'output_token_details': {'audio': 0, 'reasoning': 0}
    },
    'claude-haiku-4-5-20251001': {
        'input_tokens': 8,
        'output_tokens': 21,
        'total_tokens': 29,
        'input_token_details': {'cache_read': 0, 'cache_creation': 0}
    }
}
```

##### ​Invocation config

When invoking a model, you can pass additional configuration through the config parameter using a RunnableConfig dictionary. This provides run-time control over execution behavior, callbacks, and metadata tracking.

Common configuration options include:

Invocation with configCopyresponse = model.invoke(
    "Tell me a joke",
```
    config={
        "run_name": "joke_generation",      # Custom name for this run
        "tags": ["humor", "demo"],          # Tags for categorization
        "metadata": {"user_id": "123"},     # Custom metadata
        "callbacks": [my_callback_handler], # Callback handlers
    }
)

These configuration values are particularly useful when:

- Debugging with LangSmith tracing
- Implementing custom logging or monitoring
- Controlling resource usage in production
- Tracking invocations across complex pipelines
Key configuration attributes​run_namestringIdentifies this specific invocation in logs and traces. Not inherited by sub-calls.​tagsstring[]Labels inherited by all sub-calls for filtering and organization in debugging tools.​metadataobjectCustom key-value pairs for tracking additional context, inherited by all sub-calls.​max_concurrencynumberControls the maximum number of parallel calls when using batch() or batch_as_completed().​callbacksarrayHandlers for monitoring and responding to events during execution.​recursion_limitnumberMaximum recursion depth for chains to prevent infinite loops in complex pipelines.

See full RunnableConfig reference for all supported attributes.
```

##### ​Configurable models

You can also create a runtime-configurable model by specifying configurable_fields. If you don’t specify a model value, then 'model' and 'model_provider' will be configurable by default.

Copyfrom langchain.chat_models import init_chat_model

configurable_model = init_chat_model(temperature=0)

configurable_model.invoke(
    "what's your name",
    config={"configurable": {"model": "gpt-5-nano"}},  # Run with GPT-5-Nano
)
configurable_model.invoke(
    "what's your name",
    config={"configurable": {"model": "claude-sonnet-4-5-20250929"}},  # Run with Claude
)

Configurable model with default valuesWe can create a configurable model with default model values, specify which parameters are configurable, and add prefixes to configurable params:Copyfirst_model = init_chat_model(
        model="gpt-4.1-mini",
        temperature=0,
        configurable_fields=("model", "model_provider", "temperature", "max_tokens"),
        config_prefix="first",  # Useful when you have a chain with multiple models
)

first_model.invoke("what's your name")
Copyfirst_model.invoke(
    "what's your name",
```
    config={
        "configurable": {
            "first_model": "claude-sonnet-4-5-20250929",
            "first_temperature": 0.5,
            "first_max_tokens": 100,
        }
    },
)
See the init_chat_model reference for more details on configurable_fields and config_prefix.

Using a configurable model declarativelyWe can call declarative operations like bind_tools, with_structured_output, with_configurable, etc. on a configurable model and chain a configurable model in the same way that we would a regularly instantiated chat model object.Copyfrom pydantic import BaseModel, Field

class GetWeather(BaseModel):
    """Get the current weather in a given location"""

        location: str = Field(..., description="The city and state, e.g. San Francisco, CA")

class GetPopulation(BaseModel):
    """Get the current population in a given location"""

        location: str = Field(..., description="The city and state, e.g. San Francisco, CA")

model = init_chat_model(temperature=0)
model_with_tools = model.bind_tools([GetWeather, GetPopulation])

model_with_tools.invoke(
    "what's bigger in 2024 LA or NYC", config={"configurable": {"model": "gpt-4.1-mini"}}
).tool_calls
Copy[
    {
        'name': 'GetPopulation',
        'args': {'location': 'Los Angeles, CA'},
        'id': 'call_Ga9m8FAArItEjItHmztPYA22',
        'type': 'tool_call'
    },
    {
        'name': 'GetPopulation',
        'args': {'location': 'New York, NY'},
        'id': 'call_jh2dEvBaAHRaw5JUDthOs7rt',
        'type': 'tool_call'
    }
]
Copymodel_with_tools.invoke(
    "what's bigger in 2024 LA or NYC",
    config={"configurable": {"model": "claude-sonnet-4-5-20250929"}},
).tool_calls
Copy[
    {
        'name': 'GetPopulation',
        'args': {'location': 'Los Angeles, CA'},
        'id': 'toolu_01JMufPf4F4t2zLj7miFeqXp',
        'type': 'tool_call'
    },
    {
        'name': 'GetPopulation',
        'args': {'location': 'New York City, NY'},
        'id': 'toolu_01RQBHcE8kEEbYTuuS8WqY1u',
        'type': 'tool_call'
    }
]

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```


---

## Agents - Docs by LangChain {#doc-41}

**Source:** [https://docs.langchain.com/oss/python/langchain/agents](https://docs.langchain.com/oss/python/langchain/agents)

### Agents

Copy page

#### ​Core components

##### ​Model

The model is the reasoning engine of your agent. It can be specified in multiple ways, supporting both static and dynamic model selection.

###### ​Static model

Static models are configured once when creating the agent and remain unchanged throughout execution. This is the most common and straightforward approach.

To initialize a static model from a model identifier string:

Copyfrom langchain.agents import create_agent

agent = create_agent("gpt-5", tools=tools)

Model identifier strings support automatic inference (e.g., "gpt-5" will be inferred as "openai:gpt-5"). Refer to the reference to see a full list of model identifier string mappings.

For more control over the model configuration, initialize a model instance directly using the provider package. In this example, we use ChatOpenAI. See Chat models for other available chat model classes.

Copyfrom langchain.agents import create_agent
```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="gpt-5",
    temperature=0.1,
    max_tokens=1000,
    timeout=30
    # ... (other params)
)
agent = create_agent(model, tools=tools)

Model instances give you complete control over configuration. Use them when you need to set specific parameters like temperature, max_tokens, timeouts, base_url, and other provider-specific settings. Refer to the reference to see available params and methods on your model.
```

###### ​Dynamic model

Dynamic models are selected at runtime based on the current state and context. This enables sophisticated routing logic and cost optimization.

To use a dynamic model, create middleware using the @wrap_model_call decorator that modifies the model in the request:

Copyfrom langchain_openai import ChatOpenAI
```python
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse

basic_model = ChatOpenAI(model="gpt-4o-mini")
advanced_model = ChatOpenAI(model="gpt-4o")

@wrap_model_call
def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:
    """Choose model based on conversation complexity."""
    message_count = len(request.state["messages"])

    if message_count > 10:
        # Use an advanced model for longer conversations
        model = advanced_model
    else:
        model = basic_model

    return handler(request.override(model=model))

agent = create_agent(
    model=basic_model,  # Default model
    tools=tools,
    middleware=[dynamic_model_selection]
)

Pre-bound models (models with bind_tools already called) are not supported when using structured output. If you need dynamic model selection with structured output, ensure the models passed to the middleware are not pre-bound.

For model configuration details, see Models. For dynamic model selection patterns, see Dynamic model in middleware.
```

##### ​Tools

Tools give agents the ability to take actions. Agents go beyond simple model-only tool binding by facilitating:

- Multiple tool calls in sequence (triggered by a single prompt)
- Parallel tool calls when appropriate
- Dynamic tool selection based on previous results
- Tool retry logic and error handling
- State persistence across tool calls
For more information, see Tools.

###### ​Defining tools

Pass a list of tools to the agent.

Tools can be specified as plain Python functions or coroutines.The tool decorator can be used to customize tool names, descriptions, argument schemas, and other properties.

Copyfrom langchain.tools import tool
```python
from langchain.agents import create_agent

@tool
def search(query: str) -> str:
    """Search for information."""
    return f"Results for: {query}"

@tool
def get_weather(location: str) -> str:
    """Get weather information for a location."""
    return f"Weather in {location}: Sunny, 72°F"

agent = create_agent(model, tools=[search, get_weather])

If an empty tool list is provided, the agent will consist of a single LLM node without tool-calling capabilities.
```

###### ​Tool error handling

To customize how tool errors are handled, use the @wrap_tool_call decorator to create middleware:

Copyfrom langchain.agents import create_agent
```python
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage

@wrap_tool_call
def handle_tool_errors(request, handler):
    """Handle tool execution errors with custom messages."""
    try:
        return handler(request)
    except Exception as e:
        # Return a custom error message to the model
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({str(e)})",
            tool_call_id=request.tool_call["id"]
        )

agent = create_agent(
    model="gpt-4o",
    tools=[search, get_weather],
    middleware=[handle_tool_errors]
)

The agent will return a ToolMessage with the custom error message when a tool fails:

Copy[
    ...
    ToolMessage(
        content="Tool error: Please check your input and try again. (division by zero)",
        tool_call_id="..."
    ),
    ...
]
```

###### ​Tool use in the ReAct loop

Agents follow the ReAct (“Reasoning + Acting”) pattern, alternating between brief reasoning steps with targeted tool calls and feeding the resulting observations into subsequent decisions until they can deliver a final answer.

Example of ReAct loopPrompt: Identify the current most popular wireless headphones and verify availability.Copy================================ Human Message =================================

Find the most popular wireless headphones right now and check if they're in stock

Reasoning: “Popularity is time-sensitive, I need to use the provided search tool.”
Acting: Call search_products("wireless headphones")
Copy================================== Ai Message ==================================
Tool Calls:
  search_products (call_abc123)
 Call ID: call_abc123
  Args:
    query: wireless headphones
Copy================================= Tool Message =================================

Found 5 products matching "wireless headphones". Top 5 results: WH-1000XM5, ...

Reasoning: “I need to confirm availability for the top-ranked item before answering.”
Acting: Call check_inventory("WH-1000XM5")
Copy================================== Ai Message ==================================
Tool Calls:
  check_inventory (call_def456)
 Call ID: call_def456
  Args:
    product_id: WH-1000XM5
Copy================================= Tool Message =================================

Product WH-1000XM5: 10 units in stock

Reasoning: “I have the most popular model and its stock status. I can now answer the user’s question.”
Acting: Produce final answer
Copy================================== Ai Message ==================================

I found wireless headphones (model WH-1000XM5) with 10 units in stock...

To learn more about tools, see Tools.

##### ​System prompt

You can shape how your agent approaches tasks by providing a prompt. The system_prompt parameter can be provided as a string:

Copyagent = create_agent(
    model,
    tools,
    system_prompt="You are a helpful assistant. Be concise and accurate."
)

When no system_prompt is provided, the agent will infer its task from the messages directly.

The system_prompt parameter accepts either a str or a SystemMessage. Using a SystemMessage gives you more control over the prompt structure, which is useful for provider-specific features like Anthropic’s prompt caching:

Copyfrom langchain.agents import create_agent
```python
from langchain.messages import SystemMessage, HumanMessage

literary_agent = create_agent(
    model="anthropic:claude-sonnet-4-5",
    system_prompt=SystemMessage(
        content=[
            {
                "type": "text",
                "text": "You are an AI assistant tasked with analyzing literary works.",
            },
            {
                "type": "text",
                "text": "<the entire contents of 'Pride and Prejudice'>",
                "cache_control": {"type": "ephemeral"}
            }
        ]
    )
)

result = literary_agent.invoke(
    {"messages": [HumanMessage("Analyze the major themes in 'Pride and Prejudice'.")]}
)

The cache_control field with {"type": "ephemeral"} tells Anthropic to cache that content block, reducing latency and costs for repeated requests that use the same system prompt.
```

###### ​Dynamic system prompt

For more advanced use cases where you need to modify the system prompt based on runtime context or agent state, you can use middleware.

The @dynamic_prompt decorator creates middleware that generates system prompts based on the model request:

Copyfrom typing import TypedDict

```python
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

class Context(TypedDict):
    user_role: str

@dynamic_prompt
def user_role_prompt(request: ModelRequest) -> str:
    """Generate system prompt based on user role."""
    user_role = request.runtime.context.get("user_role", "user")
    base_prompt = "You are a helpful assistant."

    if user_role == "expert":
        return f"{base_prompt} Provide detailed technical responses."
    elif user_role == "beginner":
        return f"{base_prompt} Explain concepts simply and avoid jargon."

    return base_prompt

agent = create_agent(
    model="gpt-4o",
    tools=[web_search],
    middleware=[user_role_prompt],
    context_schema=Context
)

# The system prompt will be set dynamically based on context
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Explain machine learning"}]},
    context={"user_role": "expert"}
)

For more details on message types and formatting, see Messages. For comprehensive middleware documentation, see Middleware.
```

#### ​Invocation

You can invoke an agent by passing an update to its State. All agents include a sequence of messages in their state; to invoke the agent, pass a new message:

Copyresult = agent.invoke(
    {"messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]}
)

For streaming steps and / or tokens from the agent, refer to the streaming guide.

Otherwise, the agent follows the LangGraph Graph API and supports all associated methods, such as stream and invoke.

#### ​Advanced concepts

##### ​Structured output

In some situations, you may want the agent to return an output in a specific format. LangChain provides strategies for structured output via the response_format parameter.

###### ​ToolStrategy

ToolStrategy uses artificial tool calling to generate structured output. This works with any model that supports tool calling:

Copyfrom pydantic import BaseModel
```python
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

class ContactInfo(BaseModel):
    name: str
    email: str
    phone: str

agent = create_agent(
    model="gpt-4o-mini",
    tools=[search_tool],
    response_format=ToolStrategy(ContactInfo)
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Extract contact info from: John Doe, john@example.com, (555) 123-4567"}]
})

result["structured_response"]
# ContactInfo(name='John Doe', email='john@example.com', phone='(555) 123-4567')
```

###### ​ProviderStrategy

ProviderStrategy uses the model provider’s native structured output generation. This is more reliable but only works with providers that support native structured output (e.g., OpenAI):

Copyfrom langchain.agents.structured_output import ProviderStrategy

agent = create_agent(
    model="gpt-4o",
    response_format=ProviderStrategy(ContactInfo)
)

As of langchain 1.0, simply passing a schema (e.g., response_format=ContactInfo) is no longer supported. You must explicitly use ToolStrategy or ProviderStrategy.

To learn about structured output, see Structured output.

##### ​Memory

Agents maintain conversation history automatically through the message state. You can also configure the agent to use a custom state schema to remember additional information during the conversation.

Information stored in the state can be thought of as the short-term memory of the agent:

Custom state schemas must extend AgentState as a TypedDict.

There are two ways to define custom state:

- Via middleware (preferred)
- Via state_schema on create_agent

###### ​Defining state via middleware

Use middleware to define custom state when your custom state needs to be accessed by specific middleware hooks and tools attached to said middleware.

Copyfrom langchain.agents import AgentState
```python
from langchain.agents.middleware import AgentMiddleware
from typing import Any

class CustomState(AgentState):
    user_preferences: dict

class CustomMiddleware(AgentMiddleware):
    state_schema = CustomState
    tools = [tool1, tool2]

    def before_model(self, state: CustomState, runtime) -> dict[str, Any] | None:
        ...

agent = create_agent(
    model,
    tools=tools,
    middleware=[CustomMiddleware()]
)

# The agent can now track additional state beyond messages
result = agent.invoke({
    "messages": [{"role": "user", "content": "I prefer technical explanations"}],
    "user_preferences": {"style": "technical", "verbosity": "detailed"},
})
```

###### ​Defining state via state_schema

Use the state_schema parameter as a shortcut to define custom state that is only used in tools.

Copyfrom langchain.agents import AgentState

```python
class CustomState(AgentState):
    user_preferences: dict

agent = create_agent(
    model,
    tools=[tool1, tool2],
    state_schema=CustomState
)
# The agent can now track additional state beyond messages
result = agent.invoke({
    "messages": [{"role": "user", "content": "I prefer technical explanations"}],
    "user_preferences": {"style": "technical", "verbosity": "detailed"},
})

As of langchain 1.0, custom state schemas must be TypedDict types. Pydantic models and dataclasses are no longer supported. See the v1 migration guide for more details.

Defining custom state via middleware is preferred over defining it via state_schema on create_agent because it allows you to keep state extensions conceptually scoped to the relevant middleware and tools.state_schema is still supported for backwards compatibility on create_agent.

To learn more about memory, see Memory. For information on implementing long-term memory that persists across sessions, see Long-term memory.
```

##### ​Streaming

We’ve seen how the agent can be called with invoke to get a final response. If the agent executes multiple steps, this may take a while. To show intermediate progress, we can stream back messages as they occur.

```
Copyfor chunk in agent.stream({
    "messages": [{"role": "user", "content": "Search for AI news and summarize the findings"}]
}, stream_mode="values"):
    # Each chunk contains the full state at that point
    latest_message = chunk["messages"][-1]
    if latest_message.content:
        print(f"Agent: {latest_message.content}")
    elif latest_message.tool_calls:
        print(f"Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")

For more details on streaming, see Streaming.
```

##### ​Middleware

Middleware provides powerful extensibility for customizing agent behavior at different stages of execution. You can use middleware to:

- Process state before the model is called (e.g., message trimming, context injection)
- Modify or validate the model’s response (e.g., guardrails, content filtering)
- Handle tool execution errors with custom logic
- Implement dynamic model selection based on state or context
- Add custom logging, monitoring, or analytics
Middleware integrates seamlessly into the agent’s execution, allowing you to intercept and modify data flow at key points without changing the core agent logic.

For comprehensive middleware documentation including decorators like @before_model, @after_model, and @wrap_tool_call, see Middleware.

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Philosophy - Docs by LangChain {#doc-42}

**Source:** [https://docs.langchain.com/oss/python/langchain/philosophy](https://docs.langchain.com/oss/python/langchain/philosophy)

### Philosophy

Copy page

#### ​History

Given the constant rate of change in the field, LangChain has also evolved over time. Below is a brief timeline of how LangChain has changed over the years, evolving alongside what it means to build with LLMs:

​2022-10-24v0.0.1A month before ChatGPT, LangChain was launched as a Python package. It consisted of two main components:
LLM abstractions
“Chains”, or predetermined steps of computation to run, for common use cases. For example - RAG: run a retrieval step, then run a generation step.
The name LangChain comes from “Language” (like Language models) and “Chains”.

​2022-12The first general purpose agents were added to LangChain.These general purpose agents were based on the ReAct paper (ReAct standing for Reasoning and Acting). They used LLMs to generate JSON that represented tool calls, and then parsed that JSON to determine what tools to call.

​2023-01OpenAI releases a ‘Chat Completion’ API.Previously, models took in strings and returned a string. In the ChatCompletions API, they evolved to take in a list of messages and return a message. Other model providers followed suit, and LangChain updated to work with lists of messages.

​2023-01LangChain releases a JavaScript version.LLMs and agents will change how applications are built and JavaScript is the language of application developers.

​2023-02LangChain Inc. was formed as a company around the open source LangChain project.The main goal was to “make intelligent agents ubiquitous”. The team recognized that while LangChain was a key part (LangChain made it simple to get started with LLMs), there was also a need for other components.

​2023-03OpenAI releases ‘function calling’ in their API.This allowed the API to explicitly generate payloads that represented tool calls. Other model providers followed suit, and LangChain was updated to use this as the preferred method for tool calling (rather than parsing JSON).

​2023-06LangSmith is released as closed source platform by LangChain Inc., providing observability and evalsThe main issue with building agents is getting them to be reliable, and LangSmith, which provides observability and evals, was built to solve that need. LangChain was updated to integrate seamlessly with LangSmith.

​2024-01v0.1.0LangChain releases 0.1.0, its first non-0.0.x.The industry matured from prototypes to production, and as such, LangChain increased its focus on stability.

​2024-02LangGraph is released as an open-source library.The original LangChain had two focuses: LLM abstractions, and high-level interfaces for getting started with common applications; however, it was missing a low-level orchestration layer that allowed developers to control the exact flow of their agent. Enter: LangGraph.When building LangGraph, we learned from lessons when building LangChain and added functionality we discovered was needed: streaming, durable execution, short-term memory, human-in-the-loop, and more.

​2024-06LangChain has over 700 integrations.Integrations were split out of the core LangChain package, and either moved into their own standalone packages (for the core integrations) or langchain-community.

​2024-10LangGraph becomes the preferred way to build any AI application that is more than a single LLM call.As developers tried to improve the reliability of their applications, they needed more control than the high-level interfaces provided. LangGraph provided that low-level flexibility. Most chains and agents were marked as deprecated in LangChain with guides on how to migrate them to LangGraph. There is still one high-level abstraction created in LangGraph: an agent abstraction. It is built on top of low-level LangGraph and has the same interface as the ReAct agents from LangChain.

​2025-04Model APIs become more multimodal.Models started to accept files, images, videos, and more. We updated the langchain-core message format accordingly to allow developers to specify these multimodal inputs in a standard way.

​2025-10-20v1.0.0LangChain releases 1.0 with two major changes:

Complete revamp of all chains and agents in langchain. All chains and agents are now replaced with only one high level abstraction: an agent abstraction built on top of LangGraph. This was the high-level abstraction that was originally created in LangGraph, but just moved to LangChain.
For users still using old LangChain chains/agents who do NOT want to upgrade (note: we recommend you do), you can continue using old LangChain by installing the langchain-classic package.

A standard message content format: Model APIs evolved from returning messages with a simple content string to more complex output types - reasoning blocks, citations, server-side tool calls, etc. LangChain evolved its message formats to standardize these across providers.

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.


---

## Quickstart - Docs by LangChain {#doc-43}

**Source:** [https://docs.langchain.com/oss/python/langchain/quickstart](https://docs.langchain.com/oss/python/langchain/quickstart)

### Quickstart

Copy page

#### ​Requirements

For these examples, you will need to:

- Install the LangChain package
- Set up a Claude (Anthropic) account and get an API key
- Set the ANTHROPIC_API_KEY environment variable in your terminal
Although these examples use Claude, you can use any supported model by changing the model name in the code and setting up the appropriate API key.

#### ​Build a basic agent

Start by creating a simple agent that can answer questions and call tools. The agent will use Claude Sonnet 4.5 as its language model, a basic weather function as a tool, and a simple prompt to guide its behavior.

Copyfrom langchain.agents import create_agent

```python
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

# Run the agent
agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)

To learn how to trace your agent with LangSmith, see the LangSmith documentation.
```

#### ​Build a real-world agent

Next, build a practical weather forecasting agent that demonstrates key production concepts:

- Detailed system prompts for better agent behavior
- Create tools that integrate with external data
- Model configuration for consistent responses
- Structured output for predictable results
- Conversational memory for chat-like interactions
- Create and run the agent create a fully functional agent
Let’s walk through each step:

1Define the system promptThe system prompt defines your agent’s role and behavior. Keep it specific and actionable:CopySYSTEM_PROMPT = """You are an expert weather forecaster, who speaks in puns.

You have access to two tools:

- get_weather_for_location: use this to get the weather for a specific location
- get_user_location: use this to get the user's location

If a user asks you for the weather, make sure you know the location. If you can tell from the question that they mean wherever they are, use the get_user_location tool to find their location."""
2Create toolsTools let a model interact with external systems by calling functions you define.
Tools can depend on runtime context and also interact with agent memory.Notice below how the get_user_location tool uses runtime context:Copyfrom dataclasses import dataclass
```python
from langchain.tools import tool, ToolRuntime

@tool
def get_weather_for_location(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

@dataclass
class Context:
    """Custom runtime context schema."""
    user_id: str

@tool
def get_user_location(runtime: ToolRuntime[Context]) -> str:
    """Retrieve user information based on user ID."""
    user_id = runtime.context.user_id
    return "Florida" if user_id == "1" else "SF"
Tools should be well-documented: their name, description, and argument names become part of the model’s prompt.
LangChain’s @tool decorator adds metadata and enables runtime injection via the ToolRuntime parameter.3Configure your modelSet up your language model with the right parameters for your use case:Copyfrom langchain.chat_models import init_chat_model

model = init_chat_model(
    "claude-sonnet-4-5-20250929",
    temperature=0.5,
    timeout=10,
    max_tokens=1000
)
Depending on the model and provider chosen, initialization parameters may vary; refer to their reference pages for details.4Define response formatOptionally, define a structured response format if you need the agent responses to match
a specific schema.Copyfrom dataclasses import dataclass

# We use a dataclass here, but Pydantic models are also supported.
@dataclass
class ResponseFormat:
    """Response schema for the agent."""
    # A punny response (always required)
    punny_response: str
    # Any interesting information about the weather if available
    weather_conditions: str | None = None
5Add memoryAdd memory to your agent to maintain state across interactions. This allows
the agent to remember previous conversations and context.Copyfrom langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
In production, use a persistent checkpointer that saves to a database.
See Add and manage memory for more details.6Create and run the agentNow assemble your agent with all the components and run it!Copyfrom langchain.agents.structured_output import ToolStrategy

agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[get_user_location, get_weather_for_location],
    context_schema=Context,
    response_format=ToolStrategy(ResponseFormat),
    checkpointer=checkpointer
)

# `thread_id` is a unique identifier for a given conversation.
config = {"configurable": {"thread_id": "1"}}

response = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather outside?"}]},
    config=config,
    context=Context(user_id="1")
)

print(response['structured_response'])
# ResponseFormat(
#     punny_response="Florida is still having a 'sun-derful' day! The sunshine is playing 'ray-dio' hits all day long! I'd say it's the perfect weather for some 'solar-bration'! If you were hoping for rain, I'm afraid that idea is all 'washed up' - the forecast remains 'clear-ly' brilliant!",
#     weather_conditions="It's always sunny in Florida!"
# )

# Note that we can continue the conversation using the same `thread_id`.
response = agent.invoke(
    {"messages": [{"role": "user", "content": "thank you!"}]},
    config=config,
    context=Context(user_id="1")
)

print(response['structured_response'])
# ResponseFormat(
#     punny_response="You're 'thund-erfully' welcome! It's always a 'breeze' to help you stay 'current' with the weather. I'm just 'cloud'-ing around waiting to 'shower' you with more forecasts whenever you need them. Have a 'sun-sational' day in the Florida sunshine!",
#     weather_conditions=None
# )

Show Full example codeCopyfrom dataclasses import dataclass

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.structured_output import ToolStrategy

# Define system prompt
SYSTEM_PROMPT = """You are an expert weather forecaster, who speaks in puns.

You have access to two tools:

- get_weather_for_location: use this to get the weather for a specific location
- get_user_location: use this to get the user's location

If a user asks you for the weather, make sure you know the location. If you can tell from the question that they mean wherever they are, use the get_user_location tool to find their location."""

# Define context schema
@dataclass
class Context:
    """Custom runtime context schema."""
    user_id: str

# Define tools
@tool
def get_weather_for_location(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

@tool
def get_user_location(runtime: ToolRuntime[Context]) -> str:
    """Retrieve user information based on user ID."""
    user_id = runtime.context.user_id
    return "Florida" if user_id == "1" else "SF"

# Configure model
model = init_chat_model(
    "claude-sonnet-4-5-20250929",
    temperature=0
)

# Define response format
@dataclass
class ResponseFormat:
    """Response schema for the agent."""
    # A punny response (always required)
    punny_response: str
    # Any interesting information about the weather if available
    weather_conditions: str | None = None

# Set up memory
checkpointer = InMemorySaver()

# Create agent
agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[get_user_location, get_weather_for_location],
    context_schema=Context,
    response_format=ToolStrategy(ResponseFormat),
    checkpointer=checkpointer
)

# Run agent
# `thread_id` is a unique identifier for a given conversation.
config = {"configurable": {"thread_id": "1"}}

response = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather outside?"}]},
    config=config,
    context=Context(user_id="1")
)

print(response['structured_response'])
# ResponseFormat(
#     punny_response="Florida is still having a 'sun-derful' day! The sunshine is playing 'ray-dio' hits all day long! I'd say it's the perfect weather for some 'solar-bration'! If you were hoping for rain, I'm afraid that idea is all 'washed up' - the forecast remains 'clear-ly' brilliant!",
#     weather_conditions="It's always sunny in Florida!"
# )

# Note that we can continue the conversation using the same `thread_id`.
response = agent.invoke(
    {"messages": [{"role": "user", "content": "thank you!"}]},
    config=config,
    context=Context(user_id="1")
)

print(response['structured_response'])
# ResponseFormat(
#     punny_response="You're 'thund-erfully' welcome! It's always a 'breeze' to help you stay 'current' with the weather. I'm just 'cloud'-ing around waiting to 'shower' you with more forecasts whenever you need them. Have a 'sun-sational' day in the Florida sunshine!",
#     weather_conditions=None
# )

To learn how to trace your agent with LangSmith, see the LangSmith documentation.

Congratulations! You now have an AI agent that can:

- Understand context and remember conversations
- Use multiple tools intelligently
- Provide structured responses in a consistent format
- Handle user-specific information through context
- Maintain conversation state across interactions
Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.
```


---

## Install LangChain - Docs by LangChain {#doc-44}

**Source:** [https://docs.langchain.com/oss/python/langchain/install](https://docs.langchain.com/oss/python/langchain/install)

### Install LangChain

Copy page


---

## LangChain overview - Docs by LangChain {#doc-45}

**Source:** [https://docs.langchain.com/oss/python/langchain/overview](https://docs.langchain.com/oss/python/langchain/overview)

### LangChain overview

Copy page

#### ​ Create an agent

Copy# pip install -qU langchain "langchain[anthropic]"
```python
from langchain.agents import create_agent

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

# Run the agent
agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)

See the Installation instructions and Quickstart guide to get started building your own agents and applications with LangChain.
```

#### ​ Core benefits

Standard model interfaceDifferent providers have unique APIs for interacting with models, including the format of responses. LangChain standardizes how you interact with models so that you can seamlessly swap providers and avoid lock-in.Learn moreEasy to use, highly flexible agentLangChain’s agent abstraction is designed to be easy to get started with, letting you build a simple agent in under 10 lines of code. But it also provides enough flexibility to allow you to do all the context engineering your heart desires.Learn moreBuilt on top of LangGraphLangChain’s agents are built on top of LangGraph. This allows us to take advantage of LangGraph’s durable execution, human-in-the-loop support, persistence, and more.Learn moreDebug with LangSmithGain deep visibility into complex agent behavior with visualization tools that trace execution paths, capture state transitions, and provide detailed runtime metrics.Learn more

Edit this page on GitHub or file an issue.

Connect these docs to Claude, VSCode, and more via MCP for real-time answers.

#### Standard model interface

Different providers have unique APIs for interacting with models, including the format of responses. LangChain standardizes how you interact with models so that you can seamlessly swap providers and avoid lock-in.

Learn more

#### Easy to use, highly flexible agent

LangChain’s agent abstraction is designed to be easy to get started with, letting you build a simple agent in under 10 lines of code. But it also provides enough flexibility to allow you to do all the context engineering your heart desires.

Learn more

#### Built on top of LangGraph

LangChain’s agents are built on top of LangGraph. This allows us to take advantage of LangGraph’s durable execution, human-in-the-loop support, persistence, and more.

Learn more

#### Debug with LangSmith

Gain deep visibility into complex agent behavior with visualization tools that trace execution paths, capture state transitions, and provide detailed runtime metrics.

Learn more


---
