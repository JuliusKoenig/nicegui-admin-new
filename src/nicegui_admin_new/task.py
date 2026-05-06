from celery import Task


class NiceguiAdminBaseTask(Task):
    def test(self):
        print("test123")
