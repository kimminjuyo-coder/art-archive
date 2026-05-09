from src.core.models import Exhibition


class FakeNotionClient:
    def __init__(self, seed_urls: set[str] | None = None):
        self._urls: set[str] = set(seed_urls or [])
        self.created_pages: list[Exhibition] = []
        self.raise_on_create: bool = False

    def fetch_all_source_urls(self) -> set[str]:
        return set(self._urls)

    def create_exhibition(self, ex: Exhibition) -> None:
        if self.raise_on_create:
            raise RuntimeError("simulated notion failure")
        self._urls.add(ex.source_url)
        self.created_pages.append(ex)
