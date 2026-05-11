import logging

from rich.logging import RichHandler

from nicegui_admin_new import __name__ as __package_name__
from nicegui_admin_new.console import console

logger = logging.getLogger(__package_name__)
logger.setLevel(logging.DEBUG)
ch = RichHandler(level=logging.DEBUG,
                 console=console)
logger.addHandler(ch)

logger.debug("Logger initialized.")
