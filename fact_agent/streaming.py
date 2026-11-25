"""Streaming response support for Fact Agent."""

import json
import logging
import urllib.request
from typing import Generator, Optional

from fact_agent.http_client import LLMClient
from fact_agent.logging_setup import get_logger

logger = get_logger(__name__)


def chat_completion_stream(
    client: LLMClient,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int | None = None,
    tools: list[dict] | None = None,
) -> Generator[str, None, None]:
    """Stream chat completion tokens as they arrive.

    Yields:
        Content chunks (tokens) as strings.
    """
    import urllib.request

    payload = {
        "model": client.model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    logger.debug("Streaming LLM request", extra={"messages": len(messages)})

    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {client.api_key}",
    }

    req = urllib.request.Request(
        client.api_url,
        data=data,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=client.timeout) as response:
            # Read streaming response line by line
            for line in response:
                line = line.decode("utf-8").strip()
                if not line:
                    continue

                # SSE format: "data: {...}"
                if line.startswith("data: "):
                    data_str = line[6:]  # Remove "data: "
                    if data_str == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_str)
                        choices = chunk.get("choices")
                        if choices and len(choices) > 0:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        logger.error("Streaming HTTP error", extra={"status": e.code, "body": body})
        raise
    except urllib.error.URLError as e:
        logger.error("Streaming network error", exc_info=e)
        raise
    except Exception as e:
        logger.error("Streaming error", exc_info=e)
        raise


def stream_response(
    client: LLMClient,
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.7,
    max_tokens: int | None = None,
) -> Generator[str, None, None]:
    """Convenience function for streaming a response.

    Args:
        client: LLMClient instance
        messages: Message history
        tools: Optional tool specifications
        temperature: Sampling temperature
        max_tokens: Max tokens to generate

    Yields:
        Content tokens as they arrive.
    """
    if tools:
        # For tool calls, we need to handle them non-streaming first,
        # then stream the final response
        from fact_agent.tools import execute_tool, get_tool_registry

        payload = {
            "model": client.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        logger.debug("LLM request with tools (non-streaming)", extra={"messages": len(messages)})

        tool_calls_made = 0
        max_tool_calls = 5
        current_messages = messages.copy()

        # First, handle tool calls non-streaming
        while tool_calls_made < max_tool_calls:
            # Make non-streaming request
            data = json.dumps(payload).encode("utf-8")
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {client.api_key}",
            }

            req = urllib.request.Request(
                client.api_url,
                data=data,
                headers=headers,
                method="POST",
            )

            try:
                with urllib.request.urlopen(req, timeout=client.timeout) as response:
                    result = json.loads(response.read().decode("utf-8"))
            except Exception as e:
                logger.error("Tool calling request failed", exc_info=e)
                raise

            try:
                choice = result["choices"][0]
                message = choice["message"]
            except (KeyError, IndexError) as e:
                logger.error("Unexpected LLM response format", extra={"response": result})
                raise

            # Check for tool calls
            tool_calls = message.get("tool_calls", [])
            if not tool_calls:
                # No tool calls, stream the content
                break

            # Add assistant message with tool calls to conversation
            current_messages.append(message)

            # Execute each tool call
            from fact_agent.tools import execute_tool
            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])

                logger.info("Executing tool", extra={"tool": function_name, "tool_args": function_args})

                # Execute tool
                result = execute_tool(function_name, **function_args)

                # Add tool result to conversation
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result.content,
                })

                tool_calls_made += 1

            # Update payload for next iteration
            payload["messages"] = current_messages

        # Now stream the final response (no tools needed)
        messages = current_messages
        tools = None

    # Stream the final response
    yield from chat_completion_stream(
        client,
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
        tools=tools,
    )