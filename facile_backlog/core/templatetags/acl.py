from django.template import Library

register = Library()


@register.filter(name='can_admin')
def can_admin(obj, user):
    if not user.is_authenticated():
        return False
    if hasattr(obj, 'can_admin'):
        return obj.can_admin(user)
    return False
