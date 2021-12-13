from __future__ import annotations

import argparse
import dataclasses
import logging
import re
import shlex
from io import TextIOWrapper
from pathlib import Path
from typing import Dict, Optional

import argcomplete
from dataclasses_json import DataClassJsonMixin
from logging_actions import log_level_action
from xdg import xdg_state_home

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ProgramState(DataClassJsonMixin):
    key_value_pairs: Dict[str, str]

    @classmethod
    def empty(cls) -> ProgramState:
        return ProgramState(key_value_pairs=dict())


def is_valid_environment_variable(s: str) -> bool:
    if not hasattr(is_valid_environment_variable, "pat"):
        is_valid_environment_variable.pat = re.compile(r"^[a-zA-Z_]+[a-zA-Z0-9_]*$")
    pat: re.Pattern = is_valid_environment_variable.pat
    if pat.match(s):
        return True
    return False


def update_state_file(state_file_io: TextIOWrapper, program_state: ProgramState):
    state_file_io.seek(0)
    state_file_io.write(program_state.to_json())
    state_file_io.truncate()


def get_handler(
    state_file_io: TextIOWrapper, program_state: ProgramState, args: argparse.Namespace
):
    key: str = args.key
    value = program_state.key_value_pairs.get(key)
    print(value)


def unset_handler(
    state_file_io: TextIOWrapper, program_state: ProgramState, args: argparse.Namespace
):
    program_state.key_value_pairs.pop(args.key)
    update_state_file(state_file_io, program_state)


def set_handler(
    state_file_io: TextIOWrapper, program_state: ProgramState, args: argparse.Namespace
):
    program_state.key_value_pairs[args.key] = args.value
    update_state_file(state_file_io, program_state)


def clear_handler(
    state_file_io: TextIOWrapper, program_state: ProgramState, args: argparse.Namespace
):
    update_state_file(state_file_io, ProgramState.empty())


def env_handler(
    state_file_io: TextIOWrapper, program_state: ProgramState, args: argparse.Namespace
):
    for key, value in program_state.key_value_pairs.items():
        if not is_valid_environment_variable(key):
            logger.info(
                f"Key {key} isn't a valid environement variable identifier, skipping..."
            )
            continue
        print(f"{'export ' if args.export else ''}{key}={shlex.quote(value)}")


def main(state_file: Optional[Path] = None):
    logger.addHandler(logging.StreamHandler())

    if state_file is None:
        state_file = xdg_state_home().joinpath("kv.json")

    if not state_file.exists():
        try:
            xdg_state_home().mkdir(exist_ok=True)
            logger.info(f"Initializing key-value store at {state_file}")
            state_file.write_text(ProgramState.empty().to_json())
        except Exception as e:
            logger.critical(
                f"Error initializing key-value store at {state_file}", exc_info=e
            )
            raise SystemExit

    # Keep the file open for the duration of the program
    with state_file.open(mode="r+") as state_file_io:
        state_text = state_file_io.read()
        program_state: ProgramState = ProgramState.schema().loads(state_text)

        parser = argparse.ArgumentParser(
            description=f"A persistent key-value store for the shell"
        )
        parser.add_argument(
            "--log-level", action=log_level_action(logger), default="info"
        )

        subparsers = parser.add_subparsers(required=True, dest="subcommand")

        get_subparser = subparsers.add_parser("get", help="retrieve a value")
        get_subparser.add_argument("key", choices=program_state.key_value_pairs.keys())
        get_subparser.set_defaults(handler=get_handler)

        set_subparser = subparsers.add_parser(
            "set", help="set a value, overwriting it if it exists"
        )
        set_subparser.add_argument("key", type=str)
        set_subparser.add_argument("value", type=str)
        set_subparser.set_defaults(handler=set_handler)

        unset_subparser = subparsers.add_parser("unset", help="remove a value")
        unset_subparser.add_argument("key", type=str)
        unset_subparser.set_defaults(handler=unset_handler)

        clear_subparser = subparsers.add_parser("clear", help="remove all values")
        clear_subparser.set_defaults(handler=clear_handler)

        env_subparser = subparsers.add_parser(
            "env", help="print key-value pairs as environment variables (where valid)"
        )
        env_subparser.add_argument(
            "-e",
            "--export",
            help='prefix definitions with "export"',
            # action=argparse.BooleanOptionalAction,
            action="store_true",
            dest="export",
        )
        env_subparser.add_argument(
            "-E", "--no-export", action="store_false", dest="export"
        )
        env_subparser.set_defaults(export=False)
        env_subparser.set_defaults(handler=env_handler)

        argcomplete.autocomplete(parser)
        args = parser.parse_args()

        logger.debug(f"Invoked with args {args}")
        logger.debug(f"Using data at {state_file.absolute()}")
        logger.debug(f"Deserialized as {program_state}")

        # We do it like this because for autocomplete, we MUST have the config file first
        # So it's handled in parallel to the args
        args.handler(
            state_file_io=state_file_io,
            program_state=program_state,
            args=args,
        )
