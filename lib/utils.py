from pathlib import Path
from typing import Final
import json5

APP_ROOT_PARENTS: Final[int] = 1


def app_root(joinpath="") -> Path:
    return Path(__file__).parents[APP_ROOT_PARENTS].joinpath(joinpath)


def get_bot_token() -> str:
    """./Config/discord.json5 からボットのトークンを読み出して返します。"""
    path = Path(__file__).parents[1].joinpath("config", "discord.json5")
    with open(path, "r", encoding="utf-8") as f:
        return json5.load(f)["bot_token"]


if __name__ == "__main__":
    """Test code."""
