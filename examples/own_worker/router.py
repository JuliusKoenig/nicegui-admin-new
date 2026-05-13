import inspect
import json
from inspect import Parameter
from typing import Any, Callable

from nicegui import run
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import ScalarObjectAttributeImpl
from sqlmodel import select, Session
from sqlalchemy import String, and_, cast, false, not_, or_, true, func, select
from sqlalchemy.orm import InstrumentedAttribute, RelationshipProperty
from sqlalchemy.sql import ClauseElement
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import SQLModel

from examples.own_worker.middleware import sql_model_session_dependency


def __is_null(latest_attr: InstrumentedAttribute) -> Any:
    if isinstance(latest_attr.property, RelationshipProperty):
        if isinstance(latest_attr.impl, ScalarObjectAttributeImpl):
            return ~latest_attr.has()
        return ~latest_attr.any()
    return latest_attr.is_(None)


def __is_not_null(latest_attr: InstrumentedAttribute) -> Any:
    if isinstance(latest_attr.property, RelationshipProperty):
        if isinstance(latest_attr.impl, ScalarObjectAttributeImpl):
            return latest_attr.has()
        return latest_attr.any()
    return latest_attr.is_not(None)


OPERATORS: dict[str, Callable[[InstrumentedAttribute, Any], ClauseElement]] = {
    "eq": lambda f, v: f == v,
    "neq": lambda f, v: f != v,
    "lt": lambda f, v: f < v,
    "gt": lambda f, v: f > v,
    "le": lambda f, v: f <= v,
    "ge": lambda f, v: f >= v,
    "in": lambda f, v: f.in_(v),
    "not_in": lambda f, v: f.not_in(v),
    "startswith": lambda f, v: cast(f, String).startswith(v),
    "not_startswith": lambda f, v: not_(cast(f, String).startswith(v)),
    "endswith": lambda f, v: cast(f, String).endswith(v),
    "not_endswith": lambda f, v: not_(cast(f, String).endswith(v)),
    "contains": lambda f, v: cast(f, String).contains(v),
    "not_contains": lambda f, v: not_(cast(f, String).contains(v)),
    "is_false": lambda f, v: f == false(),
    "is_true": lambda f, v: f == true(),
    "is_null": lambda f, v: __is_null(f),
    "is_not_null": lambda f, v: __is_not_null(f),
    "between": lambda f, v: f.between(*v),
    "not_between": lambda f, v: not_(f.between(*v)),
}

WHERE = dict[str, Any] | None
ORDER_BY = list[str] | None


def build_query(where: dict[str, Any],
                model: Any,
                latest_attr: InstrumentedAttribute | None = None) -> Any:
    filters = []
    for key, _ in where.items():
        if key == "or":
            filters.append(or_(*[build_query(v, model, latest_attr) for v in where[key]]))
        elif key == "and":
            filters.append(and_(*[build_query(v, model, latest_attr) for v in where[key]]))
        elif key in OPERATORS:
            filters.append(OPERATORS[key](latest_attr, where[key]))
        else:
            attr: InstrumentedAttribute | None = getattr(model, key, None)
            if attr is not None:
                filters.append(build_query(where[key], model, attr))
    if len(filters) == 1:
        return filters[0]
    if filters:
        return and_(*filters)
    return and_(True)


class CrudRouter(APIRouter):
    def __init__(self,
                 *args,
                 prefix: str,
                 tags: list[str] | None = None,
                 name: str,
                 model: type[SQLModel],
                 read_model: type[BaseModel],
                 write_model: type[BaseModel],
                 pk: str = "id",
                 **kwargs):
        super().__init__(*args,
                         prefix=prefix,
                         tags=tags,
                         **kwargs)
        self._name = name
        self._model = model
        self._read_model = read_model
        self._write_model = write_model
        self._pk = pk

        async def count_objects(where,
                                session):
            # try to parse where clause
            try:
                where_dict = json.loads(where)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=422, detail=f"Invalid where clause: {e}")

            result = await self._count(where=where_dict,
                                       session=session)

            return result

        count_objects.__signature__ = inspect.signature(count_objects).replace(parameters=[Parameter(name="where",
                                                                                                     default="{}",
                                                                                                     annotation=str | None,
                                                                                                     kind=Parameter.POSITIONAL_OR_KEYWORD),
                                                                                           Parameter(name="session",
                                                                                                     default=Depends(sql_model_session_dependency),
                                                                                                     annotation=Session,
                                                                                                     kind=Parameter.POSITIONAL_OR_KEYWORD)])

        async def list_objects(offset,
                               limit,
                               where,
                               order_by,
                               session):
            # try to parse where clause
            try:
                where_dict = json.loads(where)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=422, detail=f"Invalid where clause: {e}")

            # try to parse order_by clause
            try:
                order_by_list = json.loads(order_by)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=422, detail=f"Invalid order_by clause: {e}")

            result = await self._list(offset=offset,
                                      limit=limit,
                                      where=where_dict,
                                      order_by=order_by_list,
                                      session=session)

            return result

        # noinspection PyTypeHints
        list_objects.__signature__ = inspect.signature(list_objects).replace(parameters=[Parameter(name="offset",
                                                                                                   default=0,
                                                                                                   annotation=int,
                                                                                                   kind=Parameter.POSITIONAL_OR_KEYWORD),
                                                                                         Parameter(name="limit",
                                                                                                   default=100,
                                                                                                   annotation=int,
                                                                                                   kind=Parameter.POSITIONAL_OR_KEYWORD),
                                                                                         Parameter(name="where",
                                                                                                   default="{}",
                                                                                                   annotation=str | None,
                                                                                                   kind=Parameter.POSITIONAL_OR_KEYWORD),
                                                                                         Parameter(name="order_by",
                                                                                                   default="[]",
                                                                                                   annotation=str | None,
                                                                                                   kind=Parameter.POSITIONAL_OR_KEYWORD),
                                                                                         Parameter(name="session",
                                                                                                   default=Depends(sql_model_session_dependency),
                                                                                                   annotation=Session,
                                                                                                   kind=Parameter.POSITIONAL_OR_KEYWORD)],
                                                                             return_annotation=list[self.read_model])

        async def detail_object(pk,
                                session):
            result = await self._detail(pk=pk,
                                        session=session)
            if result is None:
                raise HTTPException(status_code=404, detail=f"{self.name} with pk={pk} not found!")

            return result

        detail_object.__signature__ = inspect.signature(detail_object).replace(parameters=[Parameter(name="pk",
                                                                                                     default=...,
                                                                                                     annotation=int,
                                                                                                     kind=Parameter.POSITIONAL_OR_KEYWORD),
                                                                                           Parameter(name="session",
                                                                                                     default=Depends(sql_model_session_dependency),
                                                                                                     annotation=Session,
                                                                                                     kind=Parameter.POSITIONAL_OR_KEYWORD)],
                                                                               return_annotation=self.read_model)

        async def create_object(data,
                                session):
            try:
                result = await self._create(data=data,
                                            session=session)
            except IntegrityError as e:
                if "UNIQUE constraint failed: " in str(e):
                    raise HTTPException(status_code=422,
                                        detail=f"{self.name} with {str(e).split('UNIQUE constraint failed: ')[1].split("\n")[0]} already exists!")
                else:
                    raise HTTPException(status_code=500, detail=f"Database error: {e}")
            return result

        create_object.__signature__ = inspect.signature(create_object).replace(parameters=[Parameter(name="data",
                                                                                                     default=...,
                                                                                                     annotation=self.write_model,
                                                                                                     kind=Parameter.POSITIONAL_OR_KEYWORD),
                                                                                           Parameter(name="session",
                                                                                                     default=Depends(sql_model_session_dependency),
                                                                                                     annotation=Session,
                                                                                                     kind=Parameter.POSITIONAL_OR_KEYWORD)],
                                                                               return_annotation=self.read_model)

        async def edit_object(pk,
                              data,
                              session):
            result = await self._edit(pk=pk,
                                      data=data,
                                      session=session)

            return result

        edit_object.__signature__ = inspect.signature(edit_object).replace(parameters=[Parameter(name="pk",
                                                                                                 default=...,
                                                                                                 annotation=int,
                                                                                                 kind=Parameter.POSITIONAL_OR_KEYWORD),
                                                                                       Parameter(name="data",
                                                                                                 default=...,
                                                                                                 annotation=self.write_model,
                                                                                                 kind=Parameter.POSITIONAL_OR_KEYWORD),
                                                                                       Parameter(name="session",
                                                                                                 default=Depends(sql_model_session_dependency),
                                                                                                 annotation=Session,
                                                                                                 kind=Parameter.POSITIONAL_OR_KEYWORD)],
                                                                           return_annotation=self.read_model)

        async def delete_object(pk,
                                session):
            result = await self._delete(pk=pk,
                                        session=session)

            return result

        delete_object.__signature__ = inspect.signature(delete_object).replace(parameters=[Parameter(name="pk",
                                                                                                     default=...,
                                                                                                     annotation=int,
                                                                                                     kind=Parameter.POSITIONAL_OR_KEYWORD),
                                                                                           Parameter(name="session",
                                                                                                     default=Depends(sql_model_session_dependency),
                                                                                                     annotation=Session,
                                                                                                     kind=Parameter.POSITIONAL_OR_KEYWORD)],
                                                                               return_annotation=bool)

        # create routes
        self.add_api_route(path="/count",
                           endpoint=count_objects,
                           methods=["GET"])
        self.add_api_route(path="/list",
                           endpoint=list_objects,
                           methods=["GET"])
        self.add_api_route(path="/detail/{pk}",
                           endpoint=detail_object,
                           methods=["GET"])
        self.add_api_route(path="/create",
                           endpoint=create_object,
                           methods=["POST"])
        self.add_api_route(path="/edit/{pk}",
                           endpoint=edit_object,
                           methods=["PUT"])
        self.add_api_route(path="/delete/{pk}",
                           endpoint=delete_object,
                           methods=["DELETE"])

    @property
    def name(self) -> str:
        return self._name

    @property
    def model(self) -> type[SQLModel]:
        return self._model

    @property
    def read_model(self) -> type[BaseModel]:
        return self._read_model

    @property
    def write_model(self) -> type[BaseModel]:
        return self._write_model

    @property
    def pk(self):
        return self._pk

    async def _count(self,
                     where: WHERE,
                     session: Session) -> int:
        # select
        statement = select(func.count()).select_from(self.model)

        # where
        if where is not None:
            where = build_query(where, self.model)
            statement = statement.where(where)

        # execute query
        result = await run.io_bound(session.execute, statement)

        # process result
        result = result.scalar_one()

        return result

    async def _list(self,
                    offset: int,
                    limit: int,
                    where: WHERE,
                    order_by: ORDER_BY,
                    session: Session) -> list[SQLModel]:
        # select
        statement = select(self.model)

        # limit
        if limit > 0:
            statement = statement.limit(limit)

        # offset
        if offset > 0:
            statement = statement.offset(offset)

        # where
        if where is not None:
            where = build_query(where, self.model)
            statement = statement.where(where)

        # order_by
        order_by = order_by or []
        for value in order_by:
            sorting_attr = getattr(self.model, value.lstrip("+-"), None)
            if sorting_attr is None:
                raise HTTPException(status_code=422, detail=f"Invalid order_by value: {value}")
            if value.startswith("+"):
                statement = statement.order_by(sorting_attr)
            elif value.startswith("-"):
                statement = statement.order_by(sorting_attr.desc())
            else:
                statement = statement.order_by(sorting_attr)

        # execute query
        objs = await run.io_bound(session.exec, statement)

        # process objects
        objs = objs.scalars().unique().all()

        # serialize objects
        objs_read = []
        for obj in objs:
            obj_read_dict = obj.model_dump()
            obj_read = self.read_model(**obj_read_dict)
            objs_read.append(obj_read)

        return objs_read

    async def _detail(self,
                      pk: int,
                      session: Session) -> SQLModel | None:
        # select
        statement = select(self.model)

        # where
        statement = statement.where(getattr(self.model, self.pk) == pk)

        # execute query
        obj = await run.io_bound(session.exec, statement)

        # process object
        obj = obj.scalars().unique().one_or_none()

        # if not found
        if obj is None:
            return None

        # serialize object
        data_read_dict = obj.model_dump()
        obj_read = self.read_model(**data_read_dict)

        return obj_read

    async def _create(self,
                      data: BaseModel,
                      session: Session) -> SQLModel:
        # parse object
        data_write_dict = data.model_dump()
        obj = self.model(**data_write_dict)

        # add to session and commit
        session.add(obj)
        session.commit()

        # refresh object
        session.refresh(obj)

        # serialize object
        data_read_dict = obj.model_dump()
        obj_read = self.read_model(**data_read_dict)

        return obj_read

    async def _edit(self,
                    pk: int,
                    data: BaseModel,
                    session: Session) -> SQLModel | None:
        # select
        statement = select(self.model)

        # where
        statement = statement.where(getattr(self.model, self.pk) == pk)

        # execute query
        obj = await run.io_bound(session.exec, statement)

        # process object
        obj = obj.scalars().unique().one_or_none()

        # if not found
        if obj is None:
            return None

        # update object
        data_write_dict = data.model_dump()
        for key, value in data_write_dict.items():
            setattr(obj, key, value)

        # add to session and commit
        session.add(obj)
        session.commit()

        # refresh object
        session.refresh(obj)

        # serialize object
        data_read_dict = obj.model_dump()
        obj_read = self.read_model(**data_read_dict)

        return obj_read

    async def _delete(self,
                      pk: int,
                      session: Session) -> bool:
        # select
        statement = select(self.model)

        # where
        statement = statement.where(getattr(self.model, self.pk) == pk)

        # execute query
        obj = await run.io_bound(session.exec, statement)

        # process object
        obj = obj.scalars().unique().one_or_none()

        # if not found
        if obj is None:
            return False

        # delete object
        session.delete(obj)
        session.commit()

        return True
