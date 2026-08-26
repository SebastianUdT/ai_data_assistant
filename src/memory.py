class Memory:
    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def set(
        self,
        key: str,
        value: str,
    ) -> None:
        self._data[key] = value

    def get(
        self,
        key: str,
    ) -> str | None:
        return self._data.get(key)

    def all(self) -> dict[str, str]:
        return self._data.copy()