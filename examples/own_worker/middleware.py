from sqlalchemy import Engine
from sqlmodel import Session
from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction
from starlette.requests import Request
from starlette.types import ASGIApp


class SqlModelSessionMiddleware(BaseHTTPMiddleware):
    def __init__(self,
                 app: ASGIApp,
                 dispatch: DispatchFunction | None = None,
                 engine: Engine | None = None) -> None:
        super().__init__(app=app, dispatch=dispatch)
        self.engine = engine

    async def dispatch(self,
                       request: Request,
                       call_next):
        with Session(self.engine) as session:
            request.state.db = session
            response = await call_next(request)
        return response


def sql_model_session_dependency(request: Request) -> Session:
    return request.state.db
