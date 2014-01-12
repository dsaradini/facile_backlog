from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.validators import validate_email
from django.utils.translation import ugettext_lazy as _
from facile_backlog.core.models import UserManager

from rest_framework.authtoken.models import Token

from password_reset.forms import (PasswordRecoveryForm as BaseRecovery,
                                  PasswordResetForm as BaseReset)

from .models import User
from ..util import setup_bootstrap_fields

from widgets import WorkloadWidget
from workload import parse


class UserCreationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['email']

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        label=_("Password"),
        help_text=_("Raw passwords are not stored, so there is no way to see "
                    "this user's password, but you can change the password "
                    "using <a href=\"password/\">this form</a>."),
    )

    class Meta:
        model = User

    def clean_password(self):
        return self.initial['password']


class ProfileEditionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ProfileEditionForm, self).__init__(*args, **kwargs)
        setup_bootstrap_fields(self)

    class Meta:
        model = get_user_model()
        fields = ['full_name', 'lang']


class RegistrationForm(forms.Form):
    full_name = forms.CharField(label=_('Full name'))
    email = forms.EmailField(label=_('Email address'))
    password = forms.CharField(label=_('Password'),
                               widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data['email']
        email = UserManager.normalize_email(email)
        try:
            user = get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            pass
        else:
            if user.is_active:
                raise forms.ValidationError(
                    _('This email address is already registered.')
                )
            else:
                # If user is not active, send the activation email again
                self.cleaned_data['user'] = user
                return email
        return email

    def save(self):
        if 'user' not in self.cleaned_data:
            user = get_user_model().objects.create_user(
                self.cleaned_data['email'],
                full_name=self.cleaned_data['full_name'],
            )
            user.set_password(self.cleaned_data['password'])
            user.save()
            return user
        return self.cleaned_data['user']


class PasswordRecoveryForm(BaseRecovery):
    def get_user_by_email(self, email):
        validate_email(email)
        key = 'email__%sexact' % ('' if self.case_sensitive else 'i')
        try:
            user = get_user_model().objects.get(is_active=True, **{key: email})
        except get_user_model().DoesNotExist:
            raise forms.ValidationError(
                _("Sorry, this user isn't registered.")
            )
        return user


class PasswordResetForm(BaseReset):
    def save(self):
        self.user.set_password(self.cleaned_data['password1'])
        self.user.save(update_fields=['password'])


class ChangeApiKeyForm(forms.Form):

    def __init__(self, user, *args, **kwargs):
        super(ChangeApiKeyForm, self).__init__(*args, **kwargs)
        self.user = user

    def change_or_create(self):
        token, created = Token.objects.get_or_create(user=self.user)
        if token:
            token.delete()
        Token.objects.get_or_create(user=self.user)
        return created


class WorkloadFormField(forms.CharField):

    default_error_messages = {
        'invalid': _('Enter a valid time span: e.g. '
                     '"4 hours, 2 minutes"')
    }

    def __init__(self, *args, **kwargs):
        self.by_day = 0
        defaults = {'widget': WorkloadWidget}
        defaults.update(kwargs)
        super(WorkloadFormField, self).__init__(*args, **defaults)

    def set_by_day(self, value):
        self.by_day = value
        self.widget.set_by_day(value)

    def clean(self, value):
        super(WorkloadFormField, self).clean(value)
        if value == '' and not self.required:
            return 0
        try:
            return parse(
                value, self.by_day
            )
        except TypeError:
            raise forms.ValidationError(self.error_messages['invalid'],
                                        code='invalid')
