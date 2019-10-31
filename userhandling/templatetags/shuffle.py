import random
from django import template
register = template.Library()


# allows for random order of voting options. Gotta avoid any bias!
@register.filter
def shuffle(arg):
    aux = list(arg)[:]
    random.shuffle(aux)
    return aux

@register.filter(name='subtract')
def subtract(value, arg):
    return value - arg