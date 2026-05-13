from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, Depends
from sqlmodel import Session, select
from starlette.middleware import Middleware

from examples.own_worker.db import engine, create_db_and_tables, Worker
from examples.own_worker.middleware import SqlModelSessionMiddleware, sql_model_session_dependency
from examples.own_worker.models import WorkerReadModel, WorkerWriteModel
from examples.own_worker.router import CrudRouter


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(debug=False,
              lifespan=lifespan,
              middleware=[Middleware(SqlModelSessionMiddleware, engine=engine)])


# @app.get("/worker/")
# def list_workers(session: Session = Depends(sql_model_session_dependency)):
#     result = session.exec(select(Worker)).all()
#     return result
#
#
# @app.post("/worker/")
# def create_worker(worker: Worker,
#                   session: Session = Depends(sql_model_session_dependency)):
#     session.add(worker)
#     session.commit()
#     session.refresh(worker)
#     return worker

class WorkerRouter(CrudRouter):
    def __init__(self):
        super().__init__(prefix="/worker",
                         tags=["Worker"],
                         name="Worker",
                         model=Worker,
                         read_model=WorkerReadModel,
                         write_model=WorkerWriteModel)


worker_router = WorkerRouter()

app.include_router(worker_router)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
