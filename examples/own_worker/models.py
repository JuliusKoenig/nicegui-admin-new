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
