# conftest.py
import logging


def pytest_configure(config):
    logging.basicConfig(
        level=logging.CRITICAL,
        format="%(levelname)s - %(message)s - %(name)s - %(funcName)s - %(lineno)d - %(filename)s",
    )
