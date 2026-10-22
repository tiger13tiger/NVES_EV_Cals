import pytest

from nves_au.config import load_regulation_config


@pytest.fixture(scope="session")
def config():
    return load_regulation_config()
