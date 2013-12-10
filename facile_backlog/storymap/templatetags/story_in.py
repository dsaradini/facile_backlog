from django.template import Library

register = Library()


@register.filter(is_safe=False)
def filter_theme(stories, theme):
    if not stories:
        return []
    ret = []
    for s in stories:
        if s.theme == theme:
            ret.append(s)
    return ret


@register.filter(is_safe=False)
def filter_phase(stories, phase):
    if not stories:
        return []
    ret = []
    for s in stories:
        if s.phase == phase:
            ret.append(s)
    return ret
