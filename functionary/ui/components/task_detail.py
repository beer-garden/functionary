from django_unicorn.components import PollUpdate, UnicornView


class TaskDetailView(UnicornView):
    def refresh_task(self):
        self.task.refresh_from_db()

        if self.task.status in ["COMPLETE", "ERROR"]:
            return PollUpdate(disable=True, method="refresh_task")
