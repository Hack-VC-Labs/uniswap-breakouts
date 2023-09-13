import os
from typing import Optional

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True))


def get_env_variable(key: str, default: Optional[str] = None) -> str:
    try:
        return os.environ[key]
    except KeyError as exc:
        if default is not None:
            return default
        raise ValueError(f"Key: '{key}' not set in environment") from exc
