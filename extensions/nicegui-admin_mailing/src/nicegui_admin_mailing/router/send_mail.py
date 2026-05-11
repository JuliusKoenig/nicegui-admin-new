from nicegui import ui

from nicegui_admin_new.routing import NiceguiAdminAPIRouter

mailing = NiceguiAdminAPIRouter()


@mailing.layout(path="/send-mail")
async def send_mail():
    async def start_new_task():
        ui.notify("start new task")
        # result: AsyncResult = send_mail.apply_async(kwargs={"recipient": receiver.value,
        #                                                     "subject": subject.value,
        #                                                     "html_str": editor.value})
        # ui.notify(result)

    with ui.card().classes("w-full").tight():
        with ui.card_section().classes("w-full"):
            ui.label("Versenden einer Test E-Mail").classes("text-xl text-bold")
        ui.separator()
        with ui.card_section().props("horizontal").classes("w-full"):
            with ui.card_section().classes("w-full"):
                receiver = ui.input(value="julius@koenig-site.de",
                                    placeholder="Receiver").props("outlined dense").classes("w-full, mb-1")
                subject = ui.input(value="Test Mail from Worker Test",
                                   placeholder="Subject").props("outlined dense").classes("w-full mb-1")
                editor = ui.editor(value="""\
<html>
  <body>
    <p>Hi,<br>
       How are you?<br>
       <a href="http://www.realpython.com">Real Python</a>
       has many great tutorials.
    </p>
  </body>
</html>
""",
                                   placeholder="Enter your message body here...")
        ui.separator()
        with ui.card_actions().classes("w-full"):
            ui.button(text="Send",
                      icon="send",
                      on_click=lambda e: start_new_task())


@mailing.post("/send-mail")
async def test_api():
    return {"message": "send mail api"}
