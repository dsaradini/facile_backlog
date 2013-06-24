from urlparse import urlparse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (REDIRECT_FIELD_NAME, login as auth_login,
                                 get_user_model)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import logout as do_logout
from django.core import signing
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect, resolve_url, get_object_or_404
from django.utils.translation import ugettext as _
from django.views import generic

from le_social.registration import views as registration
from password_reset import views as password_reset
from ratelimitbackend.views import login as do_login

from .forms import (ProfileEditionForm, RegistrationForm, PasswordRecoveryForm,
                    PasswordResetForm, ChangeApiKeyForm)


def login(request):
    if request.user.is_authenticated():
        redirect_to = request.REQUEST.get(REDIRECT_FIELD_NAME, '')
        if not redirect_to:
            redirect_to = settings.LOGIN_REDIRECT_URL
        redirect_to = resolve_url(redirect_to)
        netloc = urlparse(redirect_to)[1]
        if netloc and netloc != request.get_host():
            redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)
        return redirect(redirect_to)
    return do_login(request)


def logout(request):
    """
    Logout via POST only, with CSRF check.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed("")
    return do_logout(request)


class ProfileView(generic.UpdateView):
    form_class = ProfileEditionForm
    success_url = reverse_lazy('home')
    template_name = "profile/user_form.html"

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        form.save()
        messages.success(self.request,
                         _('Your profile was successfully updated.'))
        return super(ProfileView, self).form_valid(form)
profile = login_required(ProfileView.as_view())

password_change = lambda x: x

# Registration
registration_complete = registration.RegistrationComplete.as_view(
    template_name='registration/registration_complete.html'
)


class Register(registration.Register):
    form_class = RegistrationForm
    template_name = 'registration/register.html'
    notification_subject_template_name = ('registration/'
                                          'activation_email_subject.txt')
    notification_template_name = 'registration/activation_email.txt'

    def get_notification_context(self):
        context = super(Register, self).get_notification_context()
        context.update({
            'scheme': 'https' if self.request.is_secure() else 'http'
        })
        return context

register = Register.as_view()

activation_complete = registration.ActivationComplete.as_view(
    template_name='registration/activation_complete.html'
)


class Activate(registration.Activate):
    template_name = 'registration/activate.html'

    # TODO update django-le-social and remove this method when the new
    # version is on PyPI
    def dispatch(self, request, *args, **kwargs):
        try:
            self.activation_key = signing.loads(kwargs['activation_key'],
                                                max_age=self.get_expires_in(),
                                                salt='le_social.registration')
        except signing.BadSignature:
            return super(Activate, self).dispatch(request, *args, **kwargs)
        self.request = request
        self.args = args
        self.kwargs = kwargs
        self.activate()
        return redirect(self.get_success_url())

    def activate(self):
        """Activates the user and logs him in."""
        user = get_user_model().objects.get(pk=self.activation_key)
        user.is_active = True
        user.save(update_fields=['is_active'])
        user.backend = 'ratelimitbackend.backends.RateLimitModelBackend'
        auth_login(self.request, user)
activate = Activate.as_view()


# Password recovery
class Recover(password_reset.Recover):
    search_fields = ['email']
    form_class = PasswordRecoveryForm
recover = Recover.as_view()

recover_done = password_reset.RecoverDone.as_view()
reset_done = password_reset.ResetDone.as_view()


class Reset(password_reset.SaltMixin, generic.FormView):
    form_class = PasswordResetForm
    token_expires = 3600 * 48  # Two days
    template_name = 'password_reset/reset.html'
    success_url = reverse_lazy('password_reset_done')

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs

        try:
            pk = signing.loads(kwargs['token'], max_age=self.token_expires,
                               salt=self.salt)
        except signing.BadSignature:
            return self.invalid()

        self.user = get_object_or_404(get_user_model(), pk=pk)
        return super(Reset, self).dispatch(request, *args, **kwargs)

    def invalid(self):
        return self.render_to_response(self.get_context_data(invalid=True))

    def get_form_kwargs(self):
        kwargs = super(Reset, self).get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super(Reset, self).get_context_data(**kwargs)
        if 'invalid' not in ctx:
            ctx.update({
                'username': self.user.username,
                'token': self.kwargs['token'],
            })
        return ctx

    def form_valid(self, form):
        form.save()
        messages.success(self.request,
                         _('Your password was successfully reset.'))
        return redirect(self.get_success_url())
reset = Reset.as_view()


class ChangeAPIKey(generic.FormView):
    form_class = ChangeApiKeyForm
    template_name = 'profile/api_key_form.html'
    success_url = reverse_lazy('auth_profile')

    def get_form_kwargs(self):
        kwargs = super(ChangeAPIKey, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        data = super(ChangeAPIKey, self).get_context_data(**kwargs)
        data['has_token'] = hasattr(self.request.user, "auth_token")
        return data

    def form_valid(self, form):
        created = form.change_or_create()
        if created:
            messages.success(self.request,
                             _('API key successfully created.'))
        else:
            messages.success(self.request,
                             _('API key successfully changed.'))
        return redirect(self.get_success_url())
change_api_key = login_required(ChangeAPIKey.as_view())
