"""Buyer agent example.

Demonstrates how a buyer AI agent discovers resources on Mainlayer,
verifies access, and pays for one it needs.

Usage::

    export MAINLAYER_API_KEY="ml_live_..."
    python examples/buyer_agent.py
"""
from __future__ import annotations

import asyncio
import os

from mainlayer_pydantic_ai import MainlayerDeps, create_mainlayer_agent

# ---------------------------------------------------------------------------
# Agent setup
# ---------------------------------------------------------------------------

BUYER_ID = "buyer_agent_v1"

agent = create_mainlayer_agent(
    api_key=os.environ.get("MAINLAYER_API_KEY", "ml_test_demo"),
    model="openai:gpt-4o",
    system_prompt=(
        f"You are a buyer AI agent with ID '{BUYER_ID}'. "
        "Your goal is to find services that match your needs, check whether "
        "you already have access, and pay for them if you do not. "
        "Always confirm payment with a brief summary of the resource name "
        "and cost before executing."
    ),
)


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

async def main() -> None:
    api_key = os.environ.get("MAINLAYER_API_KEY", "ml_test_demo")
    deps = MainlayerDeps(api_key=api_key)

    async with deps.client:
        print("=== Buyer Agent: Finding and purchasing a service ===\n")

        # Step 1 — discover resources matching a need
        result = await agent.run(
            "Search for sentiment analysis resources on Mainlayer (limit 5).",
            deps=deps,
        )
        print("Discovery result:", result.data)
        print()

        # Step 2 — check existing access to a specific resource
        result = await agent.run(
            (
                f"Check whether I (payer_id='{BUYER_ID}') already have access "
                "to resource ID 'res_sentiment_001'."
            ),
            deps=deps,
        )
        print("Access check:", result.data)
        print()

        # Step 3 — purchase if not already granted
        result = await agent.run(
            (
                f"I don't have access yet. Please pay for resource "
                f"'res_sentiment_001' on my behalf (payer_id='{BUYER_ID}')."
            ),
            deps=deps,
        )
        print("Purchase confirmation:", result.data)


if __name__ == "__main__":
    asyncio.run(main())
