from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class WorkerReadModel(BaseModel):
    id: int | None = Field(default=...,
                           title="ID",
                           description="The unique identifier of the worker")
    name: str = Field(default=...,
                      title="Name",
                      description="The name of the worker")
    last_seen: datetime | None = Field(default=...,
                                       title="Last Seen",
                                       description="The last time the worker was seen")

    class Status(str, Enum):
        IDLE = "IDLE"
        BUSY = "BUSY"

    status: Status = Field(default=...,
                           title="Status",
                           description="The status of the worker")


class WorkerWriteModel(BaseModel):
    name: str = Field(default=...,
                      title="Name",
                      description="The name of the worker")


class TaskReadModel(BaseModel):
    id: int | None = Field(default=...,
                           title="ID",
                           description="The unique identifier of the Task")
    name: str = Field(default=...,
                      title="Name",
                      description="The name of the Task")
    current_worker: WorkerReadModel | None = Field(default=None,
                                                   title="Current Worker",
                                                   description="The current worker of the Task.")

    class Status(str, Enum):
        QUEUED = "QUEUED"
        RUNNING = "RUNNING"
        FINISHED = "FINISHED"
        ERROR = "ERROR"

    status: Status = Field(default=...,
                           title="Status",
                           description="The status of the Task")
    kwargs: str = Field(default=...,
                        title="Kwargs",
                        description="The kwargs of the Task")
    logs: list["TaskLogReadModel"] = Field(default_factory=list,
                                           title="Logs",
                                           description="The logs of the Task")


class TaskWriteModel(BaseModel):
    name: str = Field(default=...,
                      title="Name",
                      description="The name of the Task")
    kwargs: str = Field(default=...,
                        title="Kwargs",
                        description="The kwargs of the Task")


class TaskLogReadModel(BaseModel):
    id: int | None = Field(default=...,
                           title="ID",
                           description="The unique identifier of the Task Log")
    task: TaskReadModel = Field(default=...,
                                title="Task",
                                description="The task that was logged")
    text: str = Field(default=...,
                      title="Text",
                      description="The text of the Task Log.")
