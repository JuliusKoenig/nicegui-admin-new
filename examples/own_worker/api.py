import json
import random
import string
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from nicegui import run
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
from starlette.middleware import Middleware

from examples.own_worker.db import engine, create_db_and_tables, Worker, Task
from examples.own_worker.middleware import SqlModelSessionMiddleware, sql_model_session_dependency
from examples.own_worker.models import WorkerReadModel, WorkerWriteModel, TaskReadModel, TaskWriteModel
from examples.own_worker.router import CrudRouter


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(debug=False,
              lifespan=lifespan,
              middleware=[Middleware(SqlModelSessionMiddleware, engine=engine)])


class WorkerRouter(CrudRouter):
    def __init__(self):
        super().__init__(prefix="/worker",
                         tags=["Worker"],
                         name="Worker",
                         model=Worker,
                         read_model=WorkerReadModel,
                         write_model=WorkerWriteModel)


worker_router = WorkerRouter()


@worker_router.post("/renew_token/{pk}",
                    summary=f"Renew {worker_router.name} token")
async def renew_token(pk: int,
                      session: Session = Depends(sql_model_session_dependency)) -> str:
    # select
    statement = select(worker_router.model)

    # where
    statement = statement.where(getattr(worker_router.model, worker_router.pk) == pk)

    # execute query
    obj = await run.io_bound(session.exec, statement)

    # process object
    obj = obj.unique().one_or_none()

    # if not found
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{worker_router.name} with pk={pk} not found!")

    # renew token
    token = obj.renew_token()

    # add to session and commit
    session.add(obj)
    session.commit()

    # refresh object
    session.refresh(obj)

    return token


@worker_router.post("/verify_token/{pk}",
                    summary=f"Renew {worker_router.name} token")
async def verify_token(pk: int,
                       token: str,
                       session: Session = Depends(sql_model_session_dependency)) -> bool:
    # select
    statement = select(worker_router.model)

    # where
    statement = statement.where(getattr(worker_router.model, worker_router.pk) == pk)

    # execute query
    obj = await run.io_bound(session.exec, statement)

    # process object
    obj = obj.unique().one_or_none()

    # if not found
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{worker_router.name} with pk={pk} not found!")

    # verify token
    result = obj.verify_token(verifying_token=token)

    return result

app.include_router(worker_router)


class TaskRouter(CrudRouter):
    def __init__(self):
        super().__init__(prefix="/task",
                         tags=["Task"],
                         name="Task",
                         model=Task,
                         read_model=TaskReadModel,
                         write_model=TaskWriteModel)


task_router = TaskRouter()
app.include_router(task_router)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
