"""Example: PydanticAI agent with payment-gated features.

This example shows how to create an agent that:
1. Checks if the user has paid for premium features
2. Charges for premium API access
3. Allows limited free access without payment

Usage:
    MAINLAYER_API_KEY=ml_... OPENAI_API_KEY=sk-... python paywalled_agent.py
"""

import asyncio
import os
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from mainlayer_pydantic_ai import MainlayerDeps, MainlayerPaywallDep, mainlayer_tool


@dataclass
class PaywallDeps:
    """Dependencies including Mainlayer payment capabilities."""

    mainlayer: MainlayerDeps
    paywall: MainlayerPaywallDep


async def main():
    api_key = os.environ.get("MAINLAYER_API_KEY", "ml_your_key_here")
    openai_key = os.environ.get("OPENAI_API_KEY", "")

    if not openai_key:
        print("Set OPENAI_API_KEY to run this example.")
        return

    # Create an agent with payment gating
    agent = Agent(
        "openai:gpt-4o",
        deps_type=PaywallDeps,
        system_prompt=(
            "You are a premium AI analyst with payment-gated features. "
            "For basic analysis you provide free summaries. "
            "For advanced analysis (deep research, backtesting, custom models) "
            "the user must have paid for premium access."
        ),
    )

    @agent.tool
    async def check_premium_access(
        ctx: RunContext[PaywallDeps], user_id: str
    ) -> bool:
        """Check if the user has premium access.

        Args:
            user_id: The user to check

        Returns:
            True if user has paid for premium, False if free tier only
        """
        try:
            return await ctx.deps.paywall.check_access(
                resource_id="res_premium_analyst",
                payer_id=user_id,
            )
        except Exception as e:
            # In demo mode, anyone can access
            print(f"Note: {e} (using demo mode)")
            return False

    @agent.tool
    async def request_premium_payment(
        ctx: RunContext[PaywallDeps], user_id: str
    ) -> str:
        """Request payment for premium analysis features.

        Args:
            user_id: The user to charge

        Returns:
            Payment confirmation message
        """
        try:
            result = await ctx.deps.paywall.charge_for_access(
                resource_id="res_premium_analyst",
                payer_id=user_id,
            )
            return f"Payment successful! Access token: {result.get('access_token', 'N/A')}"
        except Exception as e:
            return f"Payment request initiated: {e}"

    # Create dependencies
    async with MainlayerDeps(api_key=api_key).client as client:
        deps = PaywallDeps(
            mainlayer=MainlayerDeps(api_key=api_key, client=client),
            paywall=MainlayerPaywallDep(MainlayerDeps(api_key=api_key)),
        )

        # Basic request (should work without payment)
        print("\n--- Free Tier Request ---")
        result = await agent.run(
            "Provide a quick summary of AI market trends in 2 sentences.",
            deps=deps,
        )
        print(result.data)

        # Premium request (requires payment)
        print("\n--- Premium Request ---")
        result = await agent.run(
            (
                "User 'user_123' is requesting deep research on the AI agent market. "
                "Check if they have premium access. If not, request a $4.99 payment. "
                "Then provide a detailed 500-word analysis."
            ),
            deps=deps,
        )
        print(result.data)


if __name__ == "__main__":
    asyncio.run(main())
