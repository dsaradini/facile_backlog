from django.template import Library

register = Library()


@register.filter(name='can_admin')
def can_admin(obj, user):
    if hasattr(obj, 'can_admin'):
        return obj.can_admin(user)
    return False
