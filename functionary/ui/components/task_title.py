from django_unicorn.components import PollUpdate, UnicornView


class TaskTitleView(UnicornView):
    status = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = self.task.status

    def get_status(self):
        self.task.refresh_from_db()
        self.status = self.task.status

        if self.status in ["COMPLETE", "ERROR"]:
            return PollUpdate(disable=True, method="get_status")
