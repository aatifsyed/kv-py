import argparse
from argparse import FileType
from collections import UserDict, defaultdict
from typing import Any, Callable, Dict, Iterable, Mapping, Sequence, Tuple, TypeVar
from ZODB.Connection import Connection
from ZODB.DB import ContextManager as DBContextManager
import argcomplete
import logging
from pathlib import Path
from logging_actions import log_level_action
from datetime import datetime
from dataclasses import dataclass, field
import ZODB
from persistent.mapping import PersistentMapping

logger = logging.getLogger(__name__)


@dataclass
class Value:
    value: str
    created: field(default_factory=datetime.now)
    comment: str


def main():
    logger.addHandler(logging.StreamHandler())

    conn: Connection
    with ZODB.DB("db").transaction() as conn:
        try:
            mapping: Mapping[str, Value] = conn.root.mapping
        except AttributeError:
            logger.info(f"Initializing database {conn}")
            conn.root.mapping = PersistentMapping()
            mapping: Mapping[str, Value] = conn.root.mapping

        parser = argparse.ArgumentParser(description="description")
        parser.add_argument(
            "-l",
            "--log-level",
            action=log_level_action(logger),
            default="info",
        )
        parser.add_argument(
            "key", choices=defaultdict(None, mapping)
        )  # Default because we want to accept new keys, but still get autocompletion for old ones
        parser.add_argument("value", nargs="?")
        args = parser.parse_args()

        logger.debug(f"{args=}")
