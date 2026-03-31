"""Multi-step agent pipeline example.

Demonstrates a coordinated pipeline where:
1. A **vendor agent** creates and lists a paid resource.
2. A **buyer agent** discovers it, verifies access, and pays.
3. A **monitor agent** reports revenue analytics after the transaction.

This pattern is useful for automated agent-to-agent commerce where one AI
service sells capabilities to another.

Usage::

    export MAINLAYER_API_KEY="ml_live_..."
    python examples/pipeline.py
"""
from __future__ import annotations

import asyncio
import os

from mainlayer_pydantic_ai import MainlayerDeps, create_mainlayer_agent

# ---------------------------------------------------------------------------
# Agent definitions — each has a distinct persona
# ---------------------------------------------------------------------------

_API_KEY = os.environ.get("MAINLAYER_API_KEY", "ml_test_demo")

vendor_agent = create_mainlayer_agent(
    api_key=_API_KEY,
    model="openai:gpt-4o",
    system_prompt=(
        "You are a vendor AI agent. You create and manage monetized services "
        "on Mainlayer. Be concise and business-like."
    ),
)

buyer_agent = create_mainlayer_agent(
    api_key=_API_KEY,
    model="openai:gpt-4o",
    system_prompt=(
        "You are a buyer AI agent with ID 'pipeline_buyer_v1'. "
        "You discover services on Mainlayer, verify access, and purchase "
        "what you need. Be concise."
    ),
)

monitor_agent = create_mainlayer_agent(
    api_key=_API_KEY,
    model="openai:gpt-4o",
    system_prompt=(
        "You are a revenue monitoring AI agent. You report financial analytics "
        "from Mainlayer in a concise, executive-summary style."
    ),
)


# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------

async def step_vendor(deps: MainlayerDeps) -> str:
    """Vendor creates a new resource and returns its ID for later steps."""
    print("[1/3] Vendor Agent — Creating resource...\n")
    result = await vendor_agent.run(
        (
            "Create a new resource called 'Document Summarization API' "
            "priced at $0.10 per call using pay_per_use billing. "
            "After creating it, confirm the resource ID."
        ),
        deps=deps,
    )
    print("Vendor:", result.data)
    print()
    return result.data


async def step_buyer(deps: MainlayerDeps, vendor_context: str) -> None:
    """Buyer discovers the new resource and pays for it."""
    print("[2/3] Buyer Agent — Discovering and purchasing...\n")
    result = await buyer_agent.run(
        (
            "Search for document summarization resources on Mainlayer. "
            "If you find one, check whether pipeline_buyer_v1 already has access. "
            "If not, pay for it."
        ),
        deps=deps,
    )
    print("Buyer:", result.data)
    print()


async def step_monitor(deps: MainlayerDeps) -> None:
    """Monitor agent reports revenue after the transaction."""
    print("[3/3] Monitor Agent — Reporting revenue...\n")
    result = await monitor_agent.run(
        "Generate an executive revenue summary for the last 7 days.",
        deps=deps,
    )
    print("Monitor:", result.data)
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    deps = MainlayerDeps(api_key=_API_KEY)

    print("=" * 60)
    print("  Mainlayer Multi-Agent Payment Pipeline")
    print("=" * 60)
    print()

    async with deps.client:
        vendor_output = await step_vendor(deps)
        await step_buyer(deps, vendor_context=vendor_output)
        await step_monitor(deps)

    print("Pipeline complete.")


if __name__ == "__main__":
    asyncio.run(main())
