import time

from celery.utils.log import get_task_logger

from nicegui_admin_new import __name__ as __package_name__
from nicegui_admin_new.task import NiceguiAdminBaseTask

logger = get_task_logger(__name__)


class Test(NiceguiAdminBaseTask):
    name = f"{__package_name__}.test"
    ignore_result = True

    def run(self,
            count: int = 100) -> bool:
        logger.info(f"Test task started ...")
        self.update_state(state="PROGRESS", meta={"progress": 0})
        for i in range(count):
            self.update_state(state="PROGRESS", meta={"progress": i})
            time.sleep(0.01)
        logger.info(f"Test task completed.")
        print("Test task completed.")
        return "True"
