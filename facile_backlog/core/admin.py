from django.contrib import messages, admin
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.views.decorators.debug import sensitive_post_parameters


from .forms import UserChangeForm, UserCreationForm
from .models import User


action_map = {
    ADDITION: _('Addition'),
    CHANGE: _('Change'),
    DELETION: _('Deletion'),
}


class UserAdmin(UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ['email', 'full_name', 'is_active', 'is_staff',
                    'is_superuser', 'auth_token']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['email', 'full_name']
    ordering = ['email']
    fieldsets = (
        (None, {'fields': ('email', 'full_name', 'password')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff',
                                       'is_superuser')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password'),
        }),
    )
    filter_horizontal = ()

    @sensitive_post_parameters()
    def user_change_password(self, request, id, form_url=''):
        if not self.has_change_permission(request):
            raise PermissionDenied
        user = get_object_or_404(self.queryset(request), pk=id)
        if request.method == 'POST':
            form = self.change_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                msg = _('Password changed successfully.')
                messages.success(request, msg)
                return HttpResponseRedirect('..')
        else:
            form = self.change_password_form(user)

        fieldsets = [(None, {'fields': list(form.base_fields)})]
        admin_form = admin.helpers.AdminForm(form, fieldsets, {})

        context = {
            'title': _('Change password: %s') % escape(user.email),
            'adminForm': admin_form,
            'form_url': form_url,
            'form': form,
            'is_popup': '_popup' in request.REQUEST,
            'add': True,
            'change': False,
            'has_delete_permission': False,
            'has_change_permission': True,
            'has_absolute_url': False,
            'opts': self.model._meta,
            'original': user,
            'save_as': False,
            'show_save': True,
        }
        return TemplateResponse(request, [
            self.change_user_password_template or
            'admin/auth/user/change_password.html'
        ], context, current_app=self.admin_site.name)

admin.site.register(User, UserAdmin)
