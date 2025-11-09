"""
Centralised logger for the solution‑parser package.

Features
--------
* Log level can be overridden by the environment variable
  ``SLN_LOG_LEVEL`` (e.g. ``export SLN_LOG_LEVEL=DEBUG``).
* If a JSON config file (default: ``sln_logging.json``) is present
  it is merged with the defaults – you can change format,
  handlers, etc. without touching code.
* The helper provides thin wrappers that mimic the built‑in ``print``
  signature so existing ``print`` calls can be swapped with a single
  search‑replace.
"""

from __future__ import annotations

import json
import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import Any, Mapping

# ------------------------------------------------------------------
# Default logging configuration – can be overridden by a JSON file.
# ------------------------------------------------------------------
_DEFAULT_CONFIG: Mapping[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "stream": "ext://sys.stderr",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}


def _load_external_config(path: Path) -> Mapping[str, Any] | None:
    """
    Load a JSON logging config if the file exists.
    Returns ``None`` if the file cannot be read/parsed.
    """
    if not path.is_file():
        return None
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:  # pragma: no cover – defensive
        print(
            f"[WARN] Could not load logging config from {path}: {exc}",
            file=sys.stderr,
        )
        return None


def configure_logging() -> logging.Logger:
    """
    Initialise the root logger according to the precedence:

    1. Environment variable ``SLN_LOG_LEVEL`` (overrides everything)
    2. Optional JSON file ``sln_logging.json`` in the project root
    3. Built‑in defaults

    Returns the configured *root* logger.
    """
    # -- environment variable takes absolute precedence
    env_level = os.getenv("SLN_LOG_LEVEL", "").strip().upper()
    if env_level:
        # Build a minimal config that only changes the root level.
        cfg = dict(_DEFAULT_CONFIG)
        cfg["root"] = {"level": env_level, "handlers": ["console"]}
        logging.config.dictConfig(cfg)
        return logging.getLogger()

    # -- external JSON config file (optional)
    external_cfg = _load_external_config(Path(__file__).with_name("sln_logging.json"))
    if external_cfg:
        # Merge external config into the defaults – external wins on conflict.
        merged = dict(_DEFAULT_CONFIG)
        merged.update(external_cfg)  # shallow merge is enough for our simple case
        logging.config.dictConfig(merged)
        return logging.getLogger()

    # --fall back to the hard‑coded defaults
    logging.config.dictConfig(_DEFAULT_CONFIG)
    return logging.getLogger()


# ------------------------------------------------------------------
# Helper wrappers that keep the original ``print`` signature.
# ------------------------------------------------------------------
_root_logger = configure_logging()


def log_debug(*args: Any, **kwargs: Any) -> None:
    _root_logger.debug(" ".join(map(str, args)), **kwargs)


def log_info(*args: Any, **kwargs: Any) -> None:
    _root_logger.info(" ".join(map(str, args)), **kwargs)


def log_warning(*args: Any, **kwargs: Any) -> None:
    _root_logger.warning(" ".join(map(str, args)), **kwargs)


def log_error(*args: Any, **kwargs: Any) -> None:
    _root_logger.error(" ".join(map(str, args)), **kwargs)


def log_critical(*args: Any, **kwargs: Any) -> None:
    _root_logger.critical(" ".join(map(str, args)), **kwargs)


# ------------------------------------------------------------------
# Export the public API – other modules just ``from loghelper import …``
# ------------------------------------------------------------------
__all__ = [
    "log_debug",
    "log_info",
    "log_warning",
    "log_error",
    "log_critical",
    "configure_logging",
]