from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel, create_engine


class Worker(SQLModel, table=True):
    id: int | None = Field(default=None,
                           primary_key=True)
    name: str = Field(unique=True)
    last_seen: datetime | None = Field(default=None)

    class Status(str, Enum):
        IDLE = "IDLE"
        BUSY = "BUSY"

    status: Status = Field(default=Status.IDLE,
                           nullable=False)
    token: str | None = Field(default=None)


engine = create_engine(url=f"sqlite:///test.db",
                       echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
