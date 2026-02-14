"""Claude-powered travel agent with tool use.

Uses the Anthropic SDK to run a conversational agentic loop where Claude
calls travel tools (flight search, hotel booking, etc.) and returns
results to the traveler.  All prices shown include a 10% markup; actual
costs are tracked internally and never exposed.
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

import anthropic

from .tools import TOOL_DEFINITIONS, ToolExecutor

MODEL = "claude-sonnet-4-5-20250929"

SYSTEM_PROMPT = """\
You are **Voyager**, a world-class AI travel agent with a warm, enthusiastic \
personality and a knack for selling unforgettable trips.

## Your personality
- Friendly, upbeat, and persuasive — like a seasoned travel advisor who \
genuinely loves helping people explore the world.
- You paint vivid pictures of destinations and experiences.
- You use light humor and excitement to keep travelers engaged.
- You are concise but thorough — never overwhelming, always helpful.

## What you do
1. **Understand** the traveler's needs: destination, dates, budget, vibe, \
number of travelers, preferences.
2. **Search** for flights, hotels, activities, and points of interest using \
your tools.
3. **Present** options clearly, highlighting the best value and most exciting \
choices.
4. **Book** flights and hotels when the traveler decides.
5. **Generate** a beautiful trip presentation that the traveler can keep.
6. **Issue** tickets and receipts for every booking.

## Pricing rules — CRITICAL
- Every price you see from tools already includes our service fee.
- NEVER mention markups, service fees, commissions, or "actual" vs "display" \
prices.  The price you see IS the price — present it confidently as the cost.
- Always show prices in the currency provided.

## Workflow tips
- If the traveler gives a city name (not an IATA code), use `resolve_location` \
first to find the correct code.
- After booking flights or hotels, let the traveler know their ticket/voucher \
has been generated.
- When a trip plan is coming together, proactively offer to create a trip \
presentation.
- Present search results in a clear, numbered format so the traveler can \
easily pick.
- When presenting flight results, show departure/arrival times, airline, \
stops, duration, and price.
- When presenting hotel results, show hotel name, room type, dates, \
price per night, and total price.

## Formatting
- Use markdown formatting for clarity.
- Use tables or numbered lists for search results.
- Bold important information like prices, dates, and booking IDs.
- Keep responses focused and scannable.
"""


class TravelAgent:
    """Manages a multi-turn conversation with Claude + travel tools."""

    def __init__(self, executor: ToolExecutor | None = None) -> None:
        self.client = anthropic.Anthropic()
        self.executor = executor or ToolExecutor()
        self.messages: list[dict[str, Any]] = []

    async def chat(self, user_message: str) -> AsyncIterator[str]:
        """Send a user message and yield assistant text chunks.

        Handles the full tool-use loop: if Claude returns tool_use blocks,
        execute them and feed results back until Claude produces a final
        text response (end_turn).
        """
        self.messages.append({"role": "user", "content": user_message})

        while True:
            # Stream the response
            collected_content: list[dict[str, Any]] = []
            current_text = ""

            with self.client.messages.stream(
                model=MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=self.messages,
            ) as stream:
                for event in stream:
                    if event.type == "content_block_start":
                        if event.content_block.type == "text":
                            current_text = ""
                        elif event.content_block.type == "tool_use":
                            pass  # will accumulate via deltas
                    elif event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            current_text += event.delta.text
                            yield event.delta.text

                # Get the final message
                final_message = stream.get_final_message()

            # Record assistant message
            self.messages.append({
                "role": "assistant",
                "content": [block.model_dump() for block in final_message.content],
            })

            # Check if there are tool calls to execute
            tool_calls = [
                block for block in final_message.content
                if block.type == "tool_use"
            ]

            if not tool_calls:
                # No tool calls — conversation turn is done
                break

            # Execute tools and feed results back
            tool_results = []
            for tc in tool_calls:
                result_str = self.executor.execute(tc.name, tc.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": result_str,
                })

            self.messages.append({"role": "user", "content": tool_results})
            # Loop again so Claude can process the tool results

    def chat_sync(self, user_message: str) -> str:
        """Synchronous version — returns the complete response as a string.

        Still handles the full tool-use loop internally.
        """
        self.messages.append({"role": "user", "content": user_message})

        while True:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=self.messages,
            )

            self.messages.append({
                "role": "assistant",
                "content": [block.model_dump() for block in response.content],
            })

            tool_calls = [b for b in response.content if b.type == "tool_use"]

            if not tool_calls:
                # Extract text from the response
                text_parts = [b.text for b in response.content if b.type == "text"]
                return "\n".join(text_parts)

            # Execute tools
            tool_results = []
            for tc in tool_calls:
                result_str = self.executor.execute(tc.name, tc.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": result_str,
                })

            self.messages.append({"role": "user", "content": tool_results})

    def get_documents(self) -> list[dict[str, str]]:
        """Return list of generated document files."""
        import os
        docs = []
        doc_dir = self.executor.output_dir
        if not os.path.isdir(doc_dir):
            return docs
        for fname in sorted(os.listdir(doc_dir)):
            fpath = os.path.join(doc_dir, fname)
            if os.path.isfile(fpath):
                with open(fpath) as f:
                    content = f.read()
                doc_type = "ticket" if "ticket" in fname else (
                    "voucher" if "voucher" in fname else (
                        "presentation" if "trip_plan" in fname else "document"
                    )
                )
                docs.append({
                    "filename": fname,
                    "type": doc_type,
                    "content": content,
                })
        return docs

    def get_bookings(self) -> list[dict[str, Any]]:
        """Return booking records (markup prices only)."""
        return [
            {
                "booking_id": b.booking_id,
                "type": b.booking_type,
                "traveler": b.traveler_name,
                "price": b.markup_price,
                "currency": b.currency,
                "details": b.details,
                "timestamp": b.timestamp,
            }
            for b in self.executor.bookings
        ]
