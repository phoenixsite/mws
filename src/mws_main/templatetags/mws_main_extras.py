from django import template
from django.template.defaultfilters import stringfilter

import markdown

register = template.Library()

@register.filter
@stringfilter
def to_markdown(value):
    return markdown.markdown(value)
