from django.forms import fields
from django.utils.translation import ugettext as _


class ColorPickerField(fields.ChoiceField):
    COLOR_CHOICES = (
        ("", _("None")),
        ("#7bd148", _("Green")),
        ("#5484ed", _("Bold blue")),
        ("#a4bdfc", _("Blue")),
        ("#46d6db", _("Turquoise")),
        ("#7ae7bf", _("Light green")),
        ("#51b749", _("Bold green")),
        ("#fbd75b", _("Yellow")),
        ("#ffb878", _("Orange")),
        ("#ff887c", _("Red")),
        ("#dc2127", _("Bold red")),
        ("#dbadff", _("Purple")),
        ("#e1e1e1", _("Gray")),
    )

    def __init__(self, choices=(), icon_urls={}, required=True, widget=None,
                 label=None, initial=None, help_text=None, *args, **kwargs):
        super(ColorPickerField, self).__init__(
            required=required, widget=widget, label=label, initial=initial,
            help_text=help_text, *args, **kwargs)
        if not choices:
            choices = ColorPickerField.COLOR_CHOICES
        self.choices = choices