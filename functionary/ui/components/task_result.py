from django_unicorn.components import PollUpdate, UnicornView


class TaskResultView(UnicornView):
    result = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = self.task.result or ""

    def get_result(self):
        self.task.refresh_from_db()

        if (task_result := self.task.result) is not None:
            self.result = task_result
            return PollUpdate(disable=True, method="get_status")
