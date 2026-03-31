"""Factory for creating PydanticAI agents pre-wired with Mainlayer tools."""
from __future__ import annotations

from typing import Any

from pydantic_ai import Agent

from .deps import MainlayerDeps
from .tools import mainlayer_tools

_SYSTEM_PROMPT = (
    "You are an AI agent with native payment capabilities powered by Mainlayer. "
    "You can create resources for sale, process payments, verify access, discover "
    "available resources, and retrieve revenue analytics. "
    "Always confirm payment amounts with the user before executing a transaction. "
    "When reporting monetary values, format them as USD (e.g. $1.50)."
)


def create_mainlayer_agent(
    api_key: str,
    model: str = "openai:gpt-4o",
    *,
    system_prompt: str = _SYSTEM_PROMPT,
    **agent_kwargs: Any,
) -> Agent[MainlayerDeps, str]:
    """Create a PydanticAI :class:`~pydantic_ai.Agent` with all Mainlayer tools.

    The returned agent has :class:`MainlayerDeps` as its dependency type and
    ``str`` as its result type.  All five Mainlayer tools are registered
    automatically.

    Args:
        api_key: Your Mainlayer API key (``ml_live_...`` or ``ml_test_...``).
        model: PydanticAI model identifier, e.g. ``"openai:gpt-4o"`` or
            ``"anthropic:claude-3-5-sonnet-latest"``.
            Defaults to ``"openai:gpt-4o"``.
        system_prompt: System prompt injected into every conversation.
            Override to customise agent behaviour.
        **agent_kwargs: Additional keyword arguments forwarded to
            :class:`~pydantic_ai.Agent`.

    Returns:
        A fully configured :class:`~pydantic_ai.Agent` instance.

    Example::

        from mainlayer_pydantic_ai import create_mainlayer_agent, MainlayerDeps
        import asyncio

        agent = create_mainlayer_agent(api_key="ml_live_...", model="openai:gpt-4o")

        async def main():
            deps = MainlayerDeps(api_key="ml_live_...")
            result = await agent.run("List the top 5 resources.", deps=deps)
            print(result.data)

        asyncio.run(main())
    """
    agent: Agent[MainlayerDeps, str] = Agent(
        model,
        deps_type=MainlayerDeps,
        system_prompt=system_prompt,
        **agent_kwargs,
    )

    for tool_fn in mainlayer_tools:
        agent.tool(tool_fn)

    return agent
