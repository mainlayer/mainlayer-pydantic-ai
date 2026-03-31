"""Mainlayer PydanticAI integration.

Provides ready-to-use PydanticAI tool functions and an agent factory for
integrating Mainlayer payments into AI agent workflows.

Quickstart::

    from mainlayer_pydantic_ai import create_mainlayer_agent, MainlayerDeps
    import asyncio

    agent = create_mainlayer_agent(api_key="ml_live_...", model="openai:gpt-4o")

    async def main():
        deps = MainlayerDeps(api_key="ml_live_...")
        result = await agent.run("Show my last 30 days of revenue.", deps=deps)
        print(result.data)

    asyncio.run(main())
"""

from .agent import create_mainlayer_agent
from .decorator import MainlayerPaywallDep, mainlayer_tool
from .deps import MainlayerDeps
from .tools import (
    check_access,
    create_resource,
    discover_resources,
    get_revenue,
    mainlayer_tools,
    pay_for_resource,
)

__all__ = [
    "MainlayerDeps",
    "MainlayerPaywallDep",
    "mainlayer_tool",
    "mainlayer_tools",
    "create_resource",
    "pay_for_resource",
    "check_access",
    "discover_resources",
    "get_revenue",
    "create_mainlayer_agent",
]

__version__ = "0.1.0"
