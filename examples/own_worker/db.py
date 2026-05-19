import hashlib
import json
import os
import random
import string
from datetime import datetime
from enum import Enum
from typing import Any

from sqlmodel import Field, Relationship, SQLModel, create_engine

ENCODING = "utf-8"
HASH_FUNCTION = "sha256"
INTERACTIONS = 100000
KEY_LENGTH = 128
SALT_LENGTH = 32


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
    current_task: "Task" = Relationship(back_populates="current_worker")

    def hash_token(self,
                   token: str,
                   encoding: str | None = None,
                   hash_function: str | None = None,
                   interactions: int | None = None,
                   key_length: int | None = None,
                   salt: str | None = None) -> dict[str, Any]:
        encoding = encoding or ENCODING
        hash_function = hash_function or HASH_FUNCTION
        interactions = interactions or INTERACTIONS
        key_length = key_length or KEY_LENGTH
        salt = salt or os.urandom(SALT_LENGTH).hex()

        salt_encoded = salt.encode(encoding)
        password_encoded = token.encode(encoding)
        hashed_password_encoded = hashlib.pbkdf2_hmac(hash_function, password_encoded, salt_encoded, interactions, key_length)  # generate hash
        hashed_password = hashed_password_encoded.hex()
        out = {
            "encoding": encoding,
            "hash_function": hash_function,
            "interactions": interactions,
            "key_length": key_length,
            "salt": salt,
            "hashed_password": hashed_password
        }

        return out

    def renew_token(self) -> str:
        # generate random token
        token = "".join(random.choices(string.ascii_letters + string.digits, k=32))

        # hash token
        result = self.hash_token(token=token)

        # dump result
        result_str = json.dumps(result)

        # set token
        self.token = result_str

        return token

    def verify_token(self,
                     verifying_token: str) -> bool:
        hashed_token = json.loads(self.token)

        hashed_verify_token = self.hash_token(
            token=verifying_token,
            encoding=hashed_token["encoding"],
            hash_function=hashed_token["hash_function"],
            interactions=hashed_token["interactions"],
            key_length=hashed_token["key_length"],
            salt=hashed_token["salt"]
        )
        result = hashed_token["hashed_password"] == hashed_verify_token["hashed_password"]
        return result


class Task(SQLModel, table=True):
    id: int | None = Field(default=None,
                           primary_key=True)
    name: str = Field(default=...,
                      nullable=False)
    current_worker_id: int | None = Field(default=None,
                                          foreign_key="worker.id")
    current_worker: Worker | None = Relationship(back_populates="current_task")

    class Status(str, Enum):
        QUEUED = "QUEUED"
        RUNNING = "RUNNING"
        FINISHED = "FINISHED"
        ERROR = "ERROR"

    status: Status = Field(default=Status.QUEUED,
                           nullable=False)
    kwargs: str | None = Field(default=None)
    logs: list["TaskLog"] = Relationship(back_populates="task")


class TaskLog(SQLModel, table=True):
    id: int | None = Field(default=None,
                           primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    task: Task = Relationship(back_populates="logs")
    text: str = Field(default=...,
                      nullable=False)


engine = create_engine(url=f"sqlite:///test.db",
                       echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
