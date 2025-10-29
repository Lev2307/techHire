from django import template

register = template.Library()

@register.filter
def splitted_vacancy_field(string: str):
    return string.split(';')