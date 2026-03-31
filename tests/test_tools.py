"""Tests for mainlayer_pydantic_ai tools.

Uses pytest-asyncio with mocked httpx responses so no real network calls
are made.  Each test exercises a specific behaviour or error path.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio

from mainlayer_pydantic_ai.deps import MainlayerDeps
from mainlayer_pydantic_ai.tools import (
    check_access,
    create_resource,
    discover_resources,
    get_revenue,
    mainlayer_tools,
    pay_for_resource,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_response(status_code: int, json_body: object) -> httpx.Response:
    """Build a fake httpx.Response with the given status and JSON body."""
    return httpx.Response(
        status_code=status_code,
        json=json_body,
        request=httpx.Request("GET", "https://api.mainlayer.xyz/"),
    )


def _make_ctx(client: httpx.AsyncClient) -> MagicMock:
    """Return a minimal mock RunContext whose .deps has the given client."""
    deps = MainlayerDeps(api_key="ml_test_key", client=client)
    ctx = MagicMock()
    ctx.deps = deps
    return ctx


# ---------------------------------------------------------------------------
# create_resource
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_resource_success():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    expected = {"id": "res_123", "name": "Weather API", "price_usd": 1.5, "fee_model": "one_time"}
    mock_client.post.return_value = _make_response(201, expected)

    ctx = _make_ctx(mock_client)
    result = await create_resource(ctx, name="Weather API", price_usd=1.5)

    assert result["id"] == "res_123"
    assert result["fee_model"] == "one_time"
    mock_client.post.assert_called_once_with(
        "/v1/resources",
        json={"name": "Weather API", "price_usd": 1.5, "fee_model": "one_time"},
    )


@pytest.mark.asyncio
async def test_create_resource_custom_fee_model():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    expected = {"id": "res_456", "name": "Analytics", "price_usd": 9.99, "fee_model": "subscription"}
    mock_client.post.return_value = _make_response(201, expected)

    ctx = _make_ctx(mock_client)
    result = await create_resource(ctx, name="Analytics", price_usd=9.99, fee_model="subscription")

    assert result["fee_model"] == "subscription"


@pytest.mark.asyncio
async def test_create_resource_pay_per_use():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    expected = {"id": "res_789", "name": "ML Inference", "price_usd": 0.01, "fee_model": "pay_per_use"}
    mock_client.post.return_value = _make_response(201, expected)

    ctx = _make_ctx(mock_client)
    result = await create_resource(ctx, name="ML Inference", price_usd=0.01, fee_model="pay_per_use")

    assert result["fee_model"] == "pay_per_use"


@pytest.mark.asyncio
async def test_create_resource_invalid_fee_model():
    ctx = _make_ctx(AsyncMock(spec=httpx.AsyncClient))
    with pytest.raises(ValueError, match="fee_model must be one of"):
        await create_resource(ctx, name="Bad", price_usd=1.0, fee_model="invalid")


@pytest.mark.asyncio
async def test_create_resource_negative_price():
    ctx = _make_ctx(AsyncMock(spec=httpx.AsyncClient))
    with pytest.raises(ValueError, match="non-negative"):
        await create_resource(ctx, name="Bad", price_usd=-5.0)


@pytest.mark.asyncio
async def test_create_resource_empty_name():
    ctx = _make_ctx(AsyncMock(spec=httpx.AsyncClient))
    with pytest.raises(ValueError, match="non-empty"):
        await create_resource(ctx, name="   ", price_usd=1.0)


@pytest.mark.asyncio
async def test_create_resource_api_error():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = _make_response(400, {"detail": "Duplicate name"})

    ctx = _make_ctx(mock_client)
    with pytest.raises(RuntimeError, match="400"):
        await create_resource(ctx, name="Dup", price_usd=1.0)


# ---------------------------------------------------------------------------
# pay_for_resource
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pay_for_resource_success():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    expected = {"payment_id": "pay_abc", "access_token": "tok_xyz", "status": "success"}
    mock_client.post.return_value = _make_response(200, expected)

    ctx = _make_ctx(mock_client)
    result = await pay_for_resource(ctx, resource_id="res_123", payer_id="agent_007")

    assert result["payment_id"] == "pay_abc"
    assert result["access_token"] == "tok_xyz"
    mock_client.post.assert_called_once_with(
        "/v1/payments",
        json={"resource_id": "res_123", "payer_id": "agent_007"},
    )


@pytest.mark.asyncio
async def test_pay_for_resource_empty_resource_id():
    ctx = _make_ctx(AsyncMock(spec=httpx.AsyncClient))
    with pytest.raises(ValueError, match="resource_id"):
        await pay_for_resource(ctx, resource_id="", payer_id="agent_007")


@pytest.mark.asyncio
async def test_pay_for_resource_empty_payer_id():
    ctx = _make_ctx(AsyncMock(spec=httpx.AsyncClient))
    with pytest.raises(ValueError, match="payer_id"):
        await pay_for_resource(ctx, resource_id="res_123", payer_id="  ")


@pytest.mark.asyncio
async def test_pay_for_resource_payment_required_error():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = _make_response(402, {"detail": "Insufficient funds"})

    ctx = _make_ctx(mock_client)
    with pytest.raises(RuntimeError, match="402"):
        await pay_for_resource(ctx, resource_id="res_123", payer_id="agent_007")


@pytest.mark.asyncio
async def test_pay_for_resource_not_found():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = _make_response(404, {"detail": "Resource not found"})

    ctx = _make_ctx(mock_client)
    with pytest.raises(RuntimeError, match="404"):
        await pay_for_resource(ctx, resource_id="res_nonexistent", payer_id="agent_007")


# ---------------------------------------------------------------------------
# check_access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_check_access_has_access():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _make_response(200, {"has_access": True, "expires_at": "2026-12-31"})

    ctx = _make_ctx(mock_client)
    result = await check_access(ctx, resource_id="res_123", payer_id="agent_007")

    assert result is True
    mock_client.get.assert_called_once_with(
        "/v1/access",
        params={"resource_id": "res_123", "payer_id": "agent_007"},
    )


@pytest.mark.asyncio
async def test_check_access_no_access():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _make_response(200, {"has_access": False})

    ctx = _make_ctx(mock_client)
    result = await check_access(ctx, resource_id="res_123", payer_id="agent_new")

    assert result is False


@pytest.mark.asyncio
async def test_check_access_missing_field_defaults_false():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _make_response(200, {})

    ctx = _make_ctx(mock_client)
    result = await check_access(ctx, resource_id="res_123", payer_id="agent_007")

    assert result is False


@pytest.mark.asyncio
async def test_check_access_empty_resource_id():
    ctx = _make_ctx(AsyncMock(spec=httpx.AsyncClient))
    with pytest.raises(ValueError, match="resource_id"):
        await check_access(ctx, resource_id="", payer_id="agent_007")


@pytest.mark.asyncio
async def test_check_access_api_error():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _make_response(500, {"detail": "Internal server error"})

    ctx = _make_ctx(mock_client)
    with pytest.raises(RuntimeError, match="500"):
        await check_access(ctx, resource_id="res_123", payer_id="agent_007")


# ---------------------------------------------------------------------------
# discover_resources
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_discover_resources_no_query():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    resources = [{"id": "res_1", "name": "API A"}, {"id": "res_2", "name": "API B"}]
    mock_client.get.return_value = _make_response(200, {"resources": resources})

    ctx = _make_ctx(mock_client)
    result = await discover_resources(ctx)

    assert len(result) == 2
    assert result[0]["id"] == "res_1"
    mock_client.get.assert_called_once_with("/v1/resources", params={"limit": 10})


@pytest.mark.asyncio
async def test_discover_resources_with_query():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _make_response(200, {"resources": [{"id": "res_5", "name": "Weather API"}]})

    ctx = _make_ctx(mock_client)
    result = await discover_resources(ctx, query="weather", limit=5)

    assert result[0]["name"] == "Weather API"
    mock_client.get.assert_called_once_with(
        "/v1/resources",
        params={"limit": 5, "q": "weather"},
    )


@pytest.mark.asyncio
async def test_discover_resources_bare_list_response():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    resources = [{"id": "res_1"}, {"id": "res_2"}]
    mock_client.get.return_value = _make_response(200, resources)

    ctx = _make_ctx(mock_client)
    result = await discover_resources(ctx)

    assert len(result) == 2


@pytest.mark.asyncio
async def test_discover_resources_limit_too_high():
    ctx = _make_ctx(AsyncMock(spec=httpx.AsyncClient))
    with pytest.raises(ValueError, match="limit must be between"):
        await discover_resources(ctx, limit=101)


@pytest.mark.asyncio
async def test_discover_resources_limit_zero():
    ctx = _make_ctx(AsyncMock(spec=httpx.AsyncClient))
    with pytest.raises(ValueError, match="limit must be between"):
        await discover_resources(ctx, limit=0)


@pytest.mark.asyncio
async def test_discover_resources_api_error():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _make_response(503, {"detail": "Service unavailable"})

    ctx = _make_ctx(mock_client)
    with pytest.raises(RuntimeError, match="503"):
        await discover_resources(ctx)


# ---------------------------------------------------------------------------
# get_revenue
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_revenue_default_period():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    expected = {
        "period": "30d",
        "total_revenue_usd": 1234.56,
        "transaction_count": 88,
        "top_resources": [{"id": "res_1", "revenue_usd": 800.0}],
    }
    mock_client.get.return_value = _make_response(200, expected)

    ctx = _make_ctx(mock_client)
    result = await get_revenue(ctx)

    assert result["total_revenue_usd"] == 1234.56
    assert result["transaction_count"] == 88
    mock_client.get.assert_called_once_with(
        "/v1/analytics/revenue", params={"period": "30d"}
    )


@pytest.mark.asyncio
async def test_get_revenue_7d_period():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _make_response(200, {"period": "7d", "total_revenue_usd": 200.0})

    ctx = _make_ctx(mock_client)
    result = await get_revenue(ctx, period="7d")

    assert result["period"] == "7d"


@pytest.mark.asyncio
async def test_get_revenue_1y_period():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _make_response(200, {"period": "1y", "total_revenue_usd": 50000.0})

    ctx = _make_ctx(mock_client)
    result = await get_revenue(ctx, period="1y")

    assert result["total_revenue_usd"] == 50000.0


@pytest.mark.asyncio
async def test_get_revenue_invalid_period():
    ctx = _make_ctx(AsyncMock(spec=httpx.AsyncClient))
    with pytest.raises(ValueError, match="period must be one of"):
        await get_revenue(ctx, period="2w")


@pytest.mark.asyncio
async def test_get_revenue_api_error():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _make_response(401, {"detail": "Unauthorized"})

    ctx = _make_ctx(mock_client)
    with pytest.raises(RuntimeError, match="401"):
        await get_revenue(ctx)


# ---------------------------------------------------------------------------
# mainlayer_tools list
# ---------------------------------------------------------------------------


def test_mainlayer_tools_contains_all_functions():
    assert create_resource in mainlayer_tools
    assert pay_for_resource in mainlayer_tools
    assert check_access in mainlayer_tools
    assert discover_resources in mainlayer_tools
    assert get_revenue in mainlayer_tools
    assert len(mainlayer_tools) == 5


# ---------------------------------------------------------------------------
# MainlayerDeps
# ---------------------------------------------------------------------------


def test_deps_creates_client_automatically():
    deps = MainlayerDeps(api_key="ml_test_abc")
    assert deps.client is not None
    assert isinstance(deps.client, httpx.AsyncClient)


def test_deps_accepts_custom_client():
    custom_client = httpx.AsyncClient()
    deps = MainlayerDeps(api_key="ml_test_abc", client=custom_client)
    assert deps.client is custom_client
