from django.forms import ModelForm


class BootstrapModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        icons = getattr(self.Meta, "icons", dict())

        for field_name, field in self.fields.items():
            if field_name in icons:
                field.icon = icons[field_name]
