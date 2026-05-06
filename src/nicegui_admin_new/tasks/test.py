import time

from celery.utils.log import get_task_logger

# from nicegui_admin_new.admin import celery
from nicegui_admin_new.task import NiceguiAdminBaseTask

from nicegui_admin_mailing.extension import MailingExtension, mailing_extension

logger = get_task_logger(__name__)

mailing_extension_settings: MailingExtension.Settings = mailing_extension.settings


# @celery.task(bind=True)
def test(self: NiceguiAdminBaseTask) -> bool:
    logger.info(f"Test task started ...")
    self.update_state(state="PROGRESS", meta={"progress": 0})
    for i in range(100):
        self.update_state(state="PROGRESS", meta={"progress": i})
        time.sleep(0.1)
    logger.info(f"Test task completed.")
    return True