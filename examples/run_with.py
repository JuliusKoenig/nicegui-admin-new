import uvicorn
from fastapi import FastAPI, Request
from nicegui import ui, app as ui_app, APIRouter

from nicegui_admin_new import __title__, __description__, __version__, __author__, __author_email__, __license__, __license_url__, __terms_of_service__

api_app = FastAPI(debug=True,
                  title=__title__,
                  description=__description__,
                  version=__version__,
                  author=__author__,
                  author_email=__author_email__,
                  license_info={"name": __license__, "url": __license_url__},
                  terms_of_service=__terms_of_service__,
                  docs_url="/admin/api/docs",
                  redoc_url="/admin/api/redoc",
                  openapi_url="/admin/api/openapi.json")


ui_router = APIRouter(prefix="/router")


@ui_router.get("/info", tags=["Info"])
def get_info():
    return {"info": {"title": __title__,
                     "description": __description__,
                     "version": __version__,
                     "author": __author__,
                     "author_email": __author_email__,
                     "license": __license__,
                     "license_url": __license_url__,
                     "terms_of_service": __terms_of_service__}}


@ui_router.page("/hello", include_in_schema=True)
def say_hello():
    ui.label("Hello NiceGUI from Router!")

ui_app.docs_url = "/docs"
ui_app.redoc_url = "/redoc"
ui_app.openapi_url = "/openapi.json"
ui_app.setup()


ui.run_with(app=api_app,
            mount_path="/admin")

api_app.include_router(ui_router)

if __name__ == "__main__":
    uvicorn.run(api_app, host="0.0.0.0", port=8000)
