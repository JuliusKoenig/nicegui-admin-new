from nicegui import ui

from nicegui_admin_new.routing import NiceguiAdminAPIRouter

mailing = NiceguiAdminAPIRouter()


@mailing.page(path="/send-mail")
async def test_page():
    ui.label("Send Mail Page")


@mailing.post("/send-mail")
async def test_api():
    return {"message": "send mail api"}
