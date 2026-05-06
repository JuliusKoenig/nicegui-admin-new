from nicegui import ui, APIRouter

# from nicegui_admin_new.router import NiceGuiAdminBaseAPIRouter

test = APIRouter(prefix="/test")


@test.page(path="/test-page")
async def test_page():
    ui.label("test page")


@test.get("/test-api")
async def test_api():
    return {"message": "test api"}
