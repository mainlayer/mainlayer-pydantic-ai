from dataclasses import dataclass, field
import httpx


@dataclass
class MainlayerDeps:
    """Dependencies for Mainlayer PydanticAI tools.

    Holds the API key and shared HTTP client used by all tool functions.
    The client is created automatically if not provided.

    Example::

        deps = MainlayerDeps(api_key="ml_live_...")
        async with deps.client:
            ...
    """

    api_key: str
    client: httpx.AsyncClient = field(default=None)

    def __post_init__(self) -> None:
        if self.client is None:
            self.client = httpx.AsyncClient(
                base_url="https://api.mainlayer.fr",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=httpx.Timeout(30.0),
            )
