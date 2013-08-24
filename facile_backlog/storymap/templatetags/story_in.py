from django.template import Library

register = Library()


@register.filter(is_safe=False)
def story_in(theme, phase):
    return theme.stories.filter(phase=phase).all()
