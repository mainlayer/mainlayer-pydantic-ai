# mainlayer-pydantic-ai

[![PyPI](https://img.shields.io/pypi/v/mainlayer-pydantic-ai.svg)](https://pypi.org/project/mainlayer-pydantic-ai/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Production-ready PydanticAI integration for [Mainlayer](https://mainlayer.fr) — the payment infrastructure for AI agents.

Build payment-aware AI agents with clean dependency injection, async-first design, and full type safety. Monetize agent outputs, implement pay-gated services, and enable autonomous marketplace interactions.

## Features

- Five production-ready tool functions covering the full Mainlayer API surface
- Typed `MainlayerDeps` dataclass for clean dependency injection and testing
- `create_mainlayer_agent()` factory — one call wires up every tool
- Full async support with `httpx.AsyncClient` for high-performance agents
- `@mainlayer_tool` decorator for extending with custom payment tools
- Comprehensive test suite: 25+ tests, no network required, all mocked HTTP
- Three production examples: vendor agent, buyer agent, multi-step payment pipeline

## Installation

```bash
pip install mainlayer-pydantic-ai
```

Requires Python 3.11+ and `pydantic-ai>=0.0.9`.

## Quickstart

Create a payment-aware agent in 10 lines:

```python
import asyncio
from mainlayer_pydantic_ai import create_mainlayer_agent, MainlayerDeps

agent = create_mainlayer_agent(
    api_key="ml_live_...",
    model="openai:gpt-4o",
)

async def main():
    deps = MainlayerDeps(api_key="ml_live_...")
    async with deps.client:
        result = await agent.run(
            "Create a resource called 'Summarization API' at $0.05 per call.",
            deps=deps,
        )
        print(result.data)

asyncio.run(main())
```

The agent automatically has access to all five Mainlayer tools.

## Available Tools

| Tool | Description |
|------|-------------|
| `create_resource` | Create a paid resource with a name, price, and billing model |
| `pay_for_resource` | Purchase access to a resource for a given payer |
| `check_access` | Verify whether a payer has active access to a resource |
| `discover_resources` | Search and browse resources available on Mainlayer |
| `get_revenue` | Retrieve revenue analytics (7d / 30d / 90d / 1y) |

## Using Tools Individually

You can register tools on any existing PydanticAI agent:

```python
from pydantic_ai import Agent
from mainlayer_pydantic_ai import MainlayerDeps, mainlayer_tools

agent = Agent("openai:gpt-4o", deps_type=MainlayerDeps)

for tool in mainlayer_tools:
    agent.tool(tool)
```

Or pick individual tools:

```python
from mainlayer_pydantic_ai import create_resource, get_revenue

agent.tool(create_resource)
agent.tool(get_revenue)
```

## Dependency Injection

All tools receive a `RunContext[MainlayerDeps]` as their first argument.
`MainlayerDeps` holds your API key and an `httpx.AsyncClient`:

```python
from mainlayer_pydantic_ai import MainlayerDeps

# Auto-creates the HTTP client
deps = MainlayerDeps(api_key="ml_live_...")

# Or bring your own client (useful for testing)
import httpx
custom_client = httpx.AsyncClient(
    base_url="https://api.mainlayer.fr",
    headers={"Authorization": "Bearer ml_live_..."},
)
deps = MainlayerDeps(api_key="ml_live_...", client=custom_client)
```

## Examples

Three fully worked examples are in the `examples/` directory:

### Vendor Agent — create and monetize a service

```bash
export MAINLAYER_API_KEY="ml_live_..."
python examples/vendor_agent.py
```

### Buyer Agent — discover and purchase a service

```bash
export MAINLAYER_API_KEY="ml_live_..."
python examples/buyer_agent.py
```

### Pipeline — coordinated multi-agent payment flow

```bash
export MAINLAYER_API_KEY="ml_live_..."
python examples/pipeline.py
```

## Running Tests

```bash
pip install -e ".[dev]"
pytest
```

All tests mock HTTP responses — no API key or network connection is required.

## Tool Reference

### `create_resource(ctx, name, price_usd, fee_model="one_time")`

Create a resource to sell access to a service.

- `name` — display name for the resource
- `price_usd` — price in USD (must be >= 0)
- `fee_model` — `"one_time"`, `"subscription"`, or `"pay_per_use"`

Returns the created resource object including its `id`.

### `pay_for_resource(ctx, resource_id, payer_id)`

Execute a payment granting access to a resource.

Returns a confirmation object with `payment_id` and `access_token`.

### `check_access(ctx, resource_id, payer_id)`

Check whether a payer currently holds active access.

Returns `True` or `False`.

### `discover_resources(ctx, query="", limit=10)`

Search the Mainlayer marketplace.

- `query` — optional free-text filter
- `limit` — 1–100, defaults to 10

Returns a list of matching resource objects.

### `get_revenue(ctx, period="30d")`

Retrieve vendor revenue analytics.

- `period` — `"7d"`, `"30d"`, `"90d"`, or `"1y"`

Returns an analytics object with `total_revenue_usd`, `transaction_count`, and `top_resources`.

## Authentication

All requests are authenticated with your Mainlayer API key via the `Authorization: Bearer <api_key>` header. Keys are never logged or exposed in error messages.

Get your API key at [mainlayer.fr](https://mainlayer.fr).

## License

MIT
