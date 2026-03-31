"""Decorator for creating custom Mainlayer payment tools in PydanticAI.

Usage::

    from mainlayer_pydantic_ai import MainlayerDeps, mainlayer_tool

    @mainlayer_tool
    async def custom_payment_tool(ctx: RunContext[MainlayerDeps], resource_id: str) -> dict:
        '''Custom tool that uses Mainlayer client.'''
        response = await ctx.deps.client.get(f'/v1/resources/{resource_id}')
        response.raise_for_status()
        return response.json()

    agent.tool(custom_payment_tool)
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def mainlayer_tool(fn: F) -> F:
    """Decorator that marks a function as a Mainlayer payment tool for PydanticAI.

    This is a no-op decorator that serves as documentation and type hint.
    PydanticAI will automatically recognize async functions as tools.

    Example::

        from pydantic_ai import RunContext
        from mainlayer_pydantic_ai import MainlayerDeps, mainlayer_tool

        @mainlayer_tool
        async def check_balance(ctx: RunContext[MainlayerDeps]) -> float:
            '''Check total earnings for the current account.'''
            response = await ctx.deps.client.get('/v1/analytics/revenue')
            response.raise_for_status()
            data = response.json()
            return float(data.get('total_earned_usd', 0))

        # Use in an agent
        agent.tool(check_balance)
    """

    @wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        return await fn(*args, **kwargs)

    return wrapper  # type: ignore


class MainlayerPaywallDep:
    """Dependency class for adding payment-gated access to PydanticAI agents.

    Use this when you want to gate agent responses behind a Mainlayer payment.

    Example::

        from pydantic_ai import Agent, RunContext
        from mainlayer_pydantic_ai import MainlayerDeps, MainlayerPaywallDep

        class PaywallDeps:
            mainlayer: MainlayerDeps
            paywall: MainlayerPaywallDep

        agent = Agent(
            "openai:gpt-4o",
            deps_type=PaywallDeps,
        )

        @agent.tool
        async def require_payment(ctx: RunContext[PaywallDeps]) -> bool:
            '''Check if the user has paid for premium access.'''
            has_paid = await ctx.deps.paywall.check_access(
                resource_id="res_premium_features",
                payer_id="user_123"
            )
            return has_paid
    """

    def __init__(self, mainlayer_deps: MainlayerDeps):
        """Initialize the paywall dependency.

        Args:
            mainlayer_deps: The MainlayerDeps instance for API calls
        """
        self.mainlayer = mainlayer_deps

    async def check_access(self, resource_id: str, payer_id: str) -> bool:
        """Check if a payer has access to a resource.

        Args:
            resource_id: The resource to check access for
            payer_id: The payer to check

        Returns:
            True if the payer has access, False otherwise
        """
        response = await self.mainlayer.client.get(
            f"/v1/resources/{resource_id}/access",
            params={"payer_id": payer_id},
        )
        response.raise_for_status()
        data = response.json()
        return bool(data.get("access", False))

    async def charge_for_access(
        self, resource_id: str, payer_id: str
    ) -> dict[str, Any]:
        """Charge a user for access to a resource.

        Args:
            resource_id: The resource to charge for
            payer_id: The payer to charge

        Returns:
            Payment confirmation with access token
        """
        response = await self.mainlayer.client.post(
            f"/v1/resources/{resource_id}/pay",
            json={"payer_id": payer_id},
        )
        response.raise_for_status()
        return response.json()
