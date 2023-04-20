from django.core.exceptions import ValidationError
from django.forms import ModelForm

from core.models import Workflow


class WorkflowUpdateForm(ModelForm):
    class Meta:
        model = Workflow
        fields = ["name", "description"]

    def full_clean(self):
        # Run the base full_clean() first. The constraints run against a model
        # instance and self.instance isn't update until _post_clean() is run.
        super().full_clean()
        try:
            self.instance.validate_constraints()
        except ValidationError as e:
            self._update_errors(e)
