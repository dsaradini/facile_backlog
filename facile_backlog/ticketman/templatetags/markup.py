from django.template import Library
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

import bleach
import markdown as markdownlib

register = Library()


# Whitelist from HTML::Pipeline project
# https://github.com/jch/html-pipeline
TAGS = (
    'a', 'b', 'blockquote', 'br', 'code', 'dd', 'del', 'div', 'dl', 'dt',
    'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8', 'hr', 'i', 'img',
    'ins', 'kbd', 'li', 'ol', 'p', 'pre', 'q', 'samp', 'strong', 'sub', 'sup',
    'table', 'tbody', 'tfoot', 'td', 'th', 'thead', 'tr', 'tt', 'ul', 'var',
)

ATTRIBUTES = {
    'a': ['href'],
    'img': ['src'],
    '*': [
        'abbr', 'accept', 'accept-charset', 'accesskey', 'action', 'align',
        'alt', 'axis', 'border', 'cellpadding', 'cellspacing', 'char',
        'charoff', 'charset', 'checked', 'cite', 'clear', 'color', 'cols',
        'colspan', 'compact', 'coords', 'datetime', 'dir', 'disabled',
        'enctype', 'for', 'frame', 'headers', 'height', 'hreflang', 'hspace',
        'ismap', 'itemprophref', 'itemscope', 'itemtype', 'label', 'lang',
        'longdesc', 'maxlength', 'media', 'method', 'multiple', 'name',
        'nohref', 'noshade', 'nowrap', 'prompt', 'readonly', 'rel', 'rev',
        'rows', 'rowspan', 'rules', 'scope', 'selected', 'shape', 'size',
        'span', 'start', 'summary', 'tabindex', 'target', 'title', 'type',
        'usemap', 'valign', 'value', 'vspace', 'width',
    ],
}


@register.filter(is_safe=True)
def markdown(value):
    rendered = markdownlib.markdown(force_text(value), output_format="html5",
                                    safe_mode=False)
    cleaned = bleach.clean(rendered, tags=TAGS, attributes=ATTRIBUTES,
                           strip=True)
    return mark_safe(cleaned)
