"""Mainlayer tool functions for PydanticAI agents.

Each function follows the PydanticAI tool signature convention:
    async def tool_name(ctx: RunContext[MainlayerDeps], ...) -> ...

Register them via the ``mainlayer_tools`` list or individually with
``agent.tool(fn)``.
"""
from __future__ import annotations

from typing import Any

import httpx
from pydantic_ai import RunContext

from .deps import MainlayerDeps


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _raise_for_status(response: httpx.Response) -> None:
    """Raise a descriptive RuntimeError on non-2xx responses."""
    if response.is_error:
        try:
            detail = response.json().get("detail") or response.json().get("message") or response.text
        except Exception:
            detail = response.text
        raise RuntimeError(
            f"Mainlayer API error {response.status_code}: {detail}"
        )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


async def create_resource(
    ctx: RunContext[MainlayerDeps],
    name: str,
    price_usd: float,
    fee_model: str = "one_time",
) -> dict[str, Any]:
    """Create a Mainlayer resource to sell access to a service.

    Args:
        ctx: PydanticAI run context carrying :class:`MainlayerDeps`.
        name: Human-readable name for the resource (e.g. ``"Weather API"``).\
        price_usd: Price in US dollars charged per access grant.
        fee_model: Billing model — ``"one_time"``, ``"subscription"``, or
            ``"pay_per_use"``.  Defaults to ``"one_time"``.

    Returns:
        The newly created resource object from the Mainlayer API.

    Raises:
        RuntimeError: If the API returns a non-2xx status.
    """
    if price_usd < 0:
        raise ValueError("price_usd must be non-negative")
    if not name or not name.strip():
        raise ValueError("name must be a non-empty string")
    valid_fee_models = {"one_time", "subscription", "pay_per_use"}
    if fee_model not in valid_fee_models:
        raise ValueError(
            f"fee_model must be one of {valid_fee_models}, got {fee_model!r}"
        )

    payload: dict[str, Any] = {
        "name": name.strip(),
        "price_usd": price_usd,
        "fee_model": fee_model,
    }
    response = await ctx.deps.client.post("/v1/resources", json=payload)
    _raise_for_status(response)
    return response.json()


async def pay_for_resource(
    ctx: RunContext[MainlayerDeps],
    resource_id: str,
    payer_id: str,
) -> dict[str, Any]:
    """Pay for access to a Mainlayer resource.

    Args:
        ctx: PydanticAI run context carrying :class:`MainlayerDeps`.
        resource_id: The unique identifier of the resource to purchase.
        payer_id: The identifier of the agent or user making the payment.

    Returns:
        A payment confirmation object including ``payment_id`` and
        ``access_token``.

    Raises:
        RuntimeError: If the API returns a non-2xx status.
    """
    if not resource_id or not resource_id.strip():
        raise ValueError("resource_id must be a non-empty string")
    if not payer_id or not payer_id.strip():
        raise ValueError("payer_id must be a non-empty string")

    payload: dict[str, Any] = {
        "resource_id": resource_id.strip(),
        "payer_id": payer_id.strip(),
    }
    response = await ctx.deps.client.post("/v1/payments", json=payload)
    _raise_for_status(response)
    return response.json()


async def check_access(
    ctx: RunContext[MainlayerDeps],
    resource_id: str,
    payer_id: str,
) -> bool:
    """Check if a payer has active access to a resource.

    Args:
        ctx: PydanticAI run context carrying :class:`MainlayerDeps`.
        resource_id: The unique identifier of the resource.
        payer_id: The identifier of the agent or user to check.

    Returns:
        ``True`` if the payer currently has access, ``False`` otherwise.

    Raises:
        RuntimeError: If the API returns a non-2xx status.
    """
    if not resource_id or not resource_id.strip():
        raise ValueError("resource_id must be a non-empty string")
    if not payer_id or not payer_id.strip():
        raise ValueError("payer_id must be a non-empty string")

    params = {
        "resource_id": resource_id.strip(),
        "payer_id": payer_id.strip(),
    }
    response = await ctx.deps.client.get("/v1/access", params=params)
    _raise_for_status(response)
    data = response.json()
    return bool(data.get("has_access", False))


async def discover_resources(
    ctx: RunContext[MainlayerDeps],
    query: str = "",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Discover available resources on Mainlayer.

    Args:
        ctx: PydanticAI run context carrying :class:`MainlayerDeps`.
        query: Optional free-text search query to filter resources.
        limit: Maximum number of results to return (1–100). Defaults to 10.

    Returns:
        A list of resource objects matching the query.

    Raises:
        ValueError: If ``limit`` is outside the range 1–100.
        RuntimeError: If the API returns a non-2xx status.
    """
    if not (1 <= limit <= 100):
        raise ValueError("limit must be between 1 and 100")

    params: dict[str, Any] = {"limit": limit}
    if query and query.strip():
        params["q"] = query.strip()

    response = await ctx.deps.client.get("/v1/resources", params=params)
    _raise_for_status(response)
    data = response.json()
    # API may return {"resources": [...]} or a bare list
    if isinstance(data, list):
        return data
    return data.get("resources", [])


async def get_revenue(
    ctx: RunContext[MainlayerDeps],
    period: str = "30d",
) -> dict[str, Any]:
    """Get revenue analytics for the authenticated vendor.

    Args:
        ctx: PydanticAI run context carrying :class:`MainlayerDeps`.
        period: Time window for analytics.  Accepted values: ``"7d"``,
            ``"30d"``, ``"90d"``, ``"1y"``.  Defaults to ``"30d"``.

    Returns:
        Analytics object with fields such as ``total_revenue_usd``,
        ``transaction_count``, and ``top_resources``.

    Raises:
        ValueError: If ``period`` is not one of the accepted values.
        RuntimeError: If the API returns a non-2xx status.
    """
    valid_periods = {"7d", "30d", "90d", "1y"}
    if period not in valid_periods:
        raise ValueError(
            f"period must be one of {valid_periods}, got {period!r}"
        )

    response = await ctx.deps.client.get(
        "/v1/analytics/revenue", params={"period": period}
    )
    _raise_for_status(response)
    return response.json()


# ---------------------------------------------------------------------------
# Public list — register all tools in one call
# ---------------------------------------------------------------------------

mainlayer_tools = [
    create_resource,
    pay_for_resource,
    check_access,
    discover_resources,
    get_revenue,
]
