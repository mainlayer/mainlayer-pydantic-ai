"""Example: Multi-agent payment pipeline on Mainlayer marketplace.

This example shows a complete workflow where:
1. Producer creates and publishes a resource (research report)
2. Buyer discovers the resource on the marketplace
3. Buyer checks cost and makes payment
4. Producer checks earnings

Usage:
    MAINLAYER_API_KEY=ml_... OPENAI_API_KEY=sk-... python marketplace_pipeline.py
"""

import asyncio
import os

from mainlayer_pydantic_ai import (
    MainlayerDeps,
    create_mainlayer_agent,
    create_resource,
    discover_resources,
    pay_for_resource,
    get_revenue,
)


async def main():
    api_key = os.environ.get("MAINLAYER_API_KEY", "ml_your_key_here")
    openai_key = os.environ.get("OPENAI_API_KEY", "")

    if not openai_key:
        print("Set OPENAI_API_KEY to run this example.")
        return

    print("\n=== Mainlayer Marketplace Pipeline ===\n")

    # Step 1: Producer creates a research report and publishes it
    print("1. PRODUCER: Creating research report...")
    producer_agent = create_mainlayer_agent(
        api_key=api_key,
        model="openai:gpt-4o",
    )

    deps = MainlayerDeps(api_key=api_key)
    async with deps.client:
        # Produce and list resource
        producer_result = await producer_agent.run(
            (
                "Create a new resource called 'AI Market Research Report Q1 2025' "
                "priced at $9.99 as a one-time purchase. "
                "Then return the resource ID so a buyer can find it."
            ),
            deps=deps,
        )
        print(f"Producer Result: {producer_result.data}\n")

    # Step 2: Buyer discovers the resource
    print("2. BUYER: Discovering resources on marketplace...")
    buyer_agent = create_mainlayer_agent(
        api_key=api_key,
        model="openai:gpt-4o",
    )

    deps = MainlayerDeps(api_key=api_key)
    async with deps.client:
        buyer_result = await buyer_agent.run(
            (
                "Search the Mainlayer marketplace for 'AI Market Research Report'. "
                "Return the resource ID, name, and price of the best match."
            ),
            deps=deps,
        )
        print(f"Buyer Found: {buyer_result.data}\n")

    # Step 3: Buyer pays for access
    print("3. BUYER: Purchasing access...")
    deps = MainlayerDeps(api_key=api_key)
    async with deps.client:
        payment_result = await buyer_agent.run(
            (
                "Use the resource from step 2. "
                "Make a payment for wallet 'buyer_wallet_001' to get access. "
                "Return the payment confirmation and access token."
            ),
            deps=deps,
        )
        print(f"Payment Result: {payment_result.data}\n")

    # Step 4: Producer checks earnings
    print("4. PRODUCER: Checking earnings...")
    deps = MainlayerDeps(api_key=api_key)
    async with deps.client:
        earnings_result = await producer_agent.run(
            "Check my total earnings and report the revenue analytics.",
            deps=deps,
        )
        print(f"Producer Earnings: {earnings_result.data}\n")

    print("=== Pipeline Complete ===")
    print(
        "\nThis demonstrates a complete marketplace flow:"
        "\n  1. Producer creates a sellable resource"
        "\n  2. Buyer discovers it on the marketplace"
        "\n  3. Buyer pays for access"
        "\n  4. Producer monitors earnings"
    )


if __name__ == "__main__":
    asyncio.run(main())
