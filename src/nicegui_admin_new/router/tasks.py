from typing import Any

from fastapi import Depends

from nicegui_admin_new.admin import NiceguiAdmin
from nicegui_admin_new.dependencies.admin import get_admin, get_task
from nicegui_admin_new.task import NiceguiAdminBaseTask
from nicegui_admin_new.routing import NiceguiAdminAPIRouter

tasks = NiceguiAdminAPIRouter(prefix="/tasks",
                              tags=["Task"])


@tasks.get("/list")
async def list_tasks(admin: NiceguiAdmin = Depends(get_admin)) -> list[str]:
    return [task_name for task_name, _ in admin.tasks.items()]


@tasks.post("/run")
async def run_task(task: NiceguiAdminBaseTask = Depends(get_task),
                   sync: bool = True,
                   task_kwargs: dict[str, Any] | None = None) -> None:
    if task_kwargs is None:
        task_kwargs = {}
    if sync:
        result = task.apply(kwargs=task_kwargs)
    else:
        result = task.apply_async(kwargs=task_kwargs)
    return result.result
