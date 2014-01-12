from django import forms
from django.utils import six

from .workload import to_string, parse


class WorkloadWidget(forms.TextInput):
    def __init__(self, *args, **kwargs):
        self.by_day = 0
        super(WorkloadWidget, self).__init__(*args, **kwargs)

    def set_by_day(self, value):
        self.by_day = value

    def render(self, name, value, attrs=None):
        if value is None:
            value = ""
        elif isinstance(value, six.string_types):
            pass
        else:
            value = to_string(value, self.by_day)
        return super(WorkloadWidget, self).render(name, value, attrs)

    def _has_changed(self, initial, data):
        """
        We need to make sure the objects are of the canonical form, as a
        string comparison may needlessly fail.
        """
        if initial in ["", None] and data in ["", None]:
            return False

        if initial in ["", None] or data in ["", None]:
            return True

        if initial:
            if not isinstance(initial, int):
                initial = parse(initial, self.by_day)

        if not isinstance(data, int):
            data = parse(data, self.by_day)

        return initial != data
