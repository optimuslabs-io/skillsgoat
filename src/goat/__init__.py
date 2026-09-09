"""SkillsGoat — vulnerable-by-design AI agent skill corpus."""

__all__ = ["main"]


def __getattr__(name: str):
    if name == "main":
        from goat.main import main as _main
        return _main
    raise AttributeError(name)
