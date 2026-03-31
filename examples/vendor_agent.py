"""Vendor agent example.

Demonstrates how a vendor AI agent creates a paid resource on Mainlayer
and monitors its revenue.

Usage::

    export MAINLAYER_API_KEY="ml_live_..."
    python examples/vendor_agent.py
"""
from __future__ import annotations

import asyncio
import os

from mainlayer_pydantic_ai import MainlayerDeps, create_mainlayer_agent

# ---------------------------------------------------------------------------
# Agent setup
# ---------------------------------------------------------------------------

agent = create_mainlayer_agent(
    api_key=os.environ.get("MAINLAYER_API_KEY", "ml_test_demo"),
    model="openai:gpt-4o",
    system_prompt=(
        "You are a vendor AI agent that monetizes services via Mainlayer. "
        "When asked to launch a new service, create the resource and confirm "
        "the price and billing model with the user before proceeding."
    ),
)


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

async def main() -> None:
    api_key = os.environ.get("MAINLAYER_API_KEY", "ml_test_demo")
    deps = MainlayerDeps(api_key=api_key)

    async with deps.client:
        # Step 1 — create a resource
        print("=== Vendor Agent: Creating a monetized service ===\n")
        result = await agent.run(
            (
                "Create a new resource called 'Real-Time Sentiment API' "
                "priced at $0.05 per call using the pay_per_use billing model."
            ),
            deps=deps,
        )
        print("Agent response:", result.data)
        print()

        # Step 2 — check revenue
        result = await agent.run(
            "Show me revenue analytics for the last 30 days.",
            deps=deps,
        )
        print("Revenue report:", result.data)
        print()

        # Step 3 — discover what else is out there
        result = await agent.run(
            "Discover the top 5 resources on Mainlayer right now.",
            deps=deps,
        )
        print("Marketplace snapshot:", result.data)


if __name__ == "__main__":
    asyncio.run(main())
