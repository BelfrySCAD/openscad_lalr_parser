"""Test fixtures for openscad_lalr_parser tests."""
import pytest
from openscad_lalr_parser import getASTfromString


@pytest.fixture
def parse():
    """Fixture that returns a parse function for convenience."""
    def _parse(code: str):
        return getASTfromString(code)
    return _parse
