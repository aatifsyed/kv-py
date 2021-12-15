from __future__ import annotations

import argparse
import logging
from collections import UserDict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Sequence

import argcomplete
import xdg
from dataclasses_json import DataClassJsonMixin, config
from logging_actions import log_level_action

logger = logging.getLogger(__name__)


@dataclass
class Value:
    value: str
    created: datetime = field(
        default_factory=datetime.now,
        metadata=config(encoder=datetime.isoformat, decoder=datetime.fromisoformat),
    )
    comment: Optional[str] = None


@dataclass
class KV(DataClassJsonMixin):
    mapping: Dict[str, Value]


class LenientChoices(UserDict):
    def __contains__(self, key: object) -> bool:
        """Return True so that argparse will validate any key as a choice"""
        return True


def main(
    kv_file: Path = xdg.xdg_data_home().joinpath("kv.json"),
    args: Optional[Sequence[str]] = None,
):
    logger.addHandler(logging.StreamHandler())
    logger.debug(f"{kv_file=}")

    try:
        kv = KV.from_json(kv_file.read_text())
    except Exception as e:
        logger.error(
            f"Unable to load from {kv_file} ({e}), ignoring and using a new kv store",
        )
        kv = KV(mapping={})

    parser = argparse.ArgumentParser(
        description="A persistent key-value store for the shell"
    )
    parser.add_argument(
        "--log-level",
        action=log_level_action(logger),
        default="info",
    )
    parser.add_argument(
        "key",
        choices=LenientChoices(kv.mapping),
        metavar="key",
        help="Retrive the value of this key",
    )
    parser.add_argument("value", nargs="?", help="If specified, set key to value")

    argcomplete.autocomplete(parser)
    args = parser.parse_args(args=args)

    logger.debug(f"{args=}")

    if args.value is None:
        # This is a get. Print out
        print(kv.mapping[args.key].value)
    else:
        # This is a set. Modify and save
        kv.mapping[args.key] = Value(value=args.value)
        kv_file.parent.mkdir(parents=True, exist_ok=True)
        kv_file.write_text(kv.to_json())
