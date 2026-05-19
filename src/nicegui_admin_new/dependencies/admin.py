from fastapi import Request, Depends, HTTPException

from nicegui_admin_new.admin import NiceguiAdmin


def get_admin(request: Request) -> NiceguiAdmin:
    return request.app.admin


def get_task(task_name: str,
             admin: NiceguiAdmin = Depends(get_admin)):
    task = admin.tasks.get(task_name)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found!")
    return task
