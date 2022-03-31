import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from dataclasses_json import DataClassJsonMixin, config

logger = logging.getLogger(__name__)

JANUARY_31_10AM = datetime(2022, 1, 31, 10, 0, 0)


def decode_optional_datetime(dt: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(dt) if dt is not None else None


def encode_optional_datetime(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt is not None else None


@dataclass
class Foo(DataClassJsonMixin):
    expires: Optional[datetime] = field(
        default=None,
        metadata=config(
            encoder=encode_optional_datetime, decoder=decode_optional_datetime
        ),
    )


def test_decode_some():
    expected = Foo(expires=JANUARY_31_10AM)
    actual = Foo.from_json(r"""{"expires": "2022-01-31T10:00:00"}""")
    assert expected == actual


def test_decode_empty():
    expected = Foo(expires=None)
    actual = Foo.from_json(r"{}")
    assert expected == actual


def test_decode_null():
    expected = Foo(expires=None)
    actual = Foo.from_json(r"""{"expires": null}""")
    assert expected == actual


def test_encode_some():
    expected = r"""{"expires": "2022-01-31T10:00:00"}"""
    actual = Foo(expires=JANUARY_31_10AM).to_json()
    assert expected == actual


def test_encode_none():
    expected = r"""{"expires": null}"""
    actual = Foo(expires=None).to_json()
    assert expected == actual
