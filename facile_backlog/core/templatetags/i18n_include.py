import os
from django import template
from django.template import Library, loader
from django.utils.translation import get_language
register = Library()


class TemplateNode(template.Node):
    def __init__(self, template_name):
        self.template_name = template_name

    def render(self, context):
        templates = [self.template_name]
        lang = get_language()
        if lang:
            file_name, file_ext = os.path.splitext(self.template_name)
            templates.insert(0, "{0}_{1}{2}".format(file_name, lang, file_ext))
        template = loader.select_template(templates)
        return template.render(context)


@register.tag(name="i18n_include")
def do_include(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, format_string = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0])
    if not (format_string[0] == format_string[-1] and
            format_string[0] in ('"', "'")):
        raise template.TemplateSyntaxError(
            "%r tag's argument should be in quotes" % tag_name)
    return TemplateNode(format_string[1:-1])
