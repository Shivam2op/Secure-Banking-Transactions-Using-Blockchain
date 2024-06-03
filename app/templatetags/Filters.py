from django import template
from django.forms import URLField
from django.utils.html import format_html

register = template.Library()


@register.filter
def verbose_value(bound_field, value):

    field = bound_field.field

    if value and isinstance(field, URLField):
        value = format_html(
            '<a href="{0}" target="_blank">{1}</a>',
            value,
            value[value.find('/', value.rfind(':')+3):],
        )

    return hasattr(field, 'choices') and dict(field.choices).get(value, '') or value
