from __future__ import annotations

from collections.abc import Callable


class StrategyNotFoundError(KeyError):
    pass


class Registry[T]:
    def __init__(self, kind: str):
        self.kind = kind
        self._strategies: dict[str, type[T]] = {}
        self._descriptions: dict[str, str] = {}

    def register(self, name: str, description: str = "") -> Callable[[type[T]], type[T]]:
        def _wrap(cls):
            if name in self._strategies:
                raise ValueError(f"{self.kind} strategy '{name}' already registered")
            self._strategies[name] = cls
            self._descriptions[name] = description or (cls.__doc__ or "").strip()
            return cls
        return _wrap

    def get(self, name: str) -> type[T]:
        try:
            return self._strategies[name]
        except KeyError as e:
            raise StrategyNotFoundError(
                f"Unknown {self.kind} strategy '{name}'. Available: {self.names()}"
            ) from e

    def create(self, name: str, **kwargs) -> T:
        return self.get(name)(**kwargs)

    def names(self) -> list[str]:
        return sorted(self._strategies.keys())

    def description(self, name: str) -> str:
        return self._descriptions.get(name, "")

    def as_choices(self) -> dict[str, str]:
        return {name: self._descriptions.get(name, "") for name in self.names()}
