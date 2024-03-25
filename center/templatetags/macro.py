from django import template
from django.template.defaultfilters import stringfilter
from django.template.exceptions import TemplateSyntaxError
import math

register = template.Library()

@register.filter('return_item')
def return_item(l, i):
    try:
        return l[i]
    except:
        return None

@register.filter('title_persist')
def title_persist(sentence):
    components = sentence.split(' ')
    result = []
    for word in components:
        result.append(word.capitalize())
    return " ".join(result)

@register.filter('ceil')
def ceil(number):
    if not isinstance(number, (float, int)):
        raise TemplateSyntaxError('ceil filter only receives float or int')
    
    return math.ceil(number)

@register.filter('custom_divide')
def custom_divide(number1, number2):
    if not (isinstance(number1, (float, int)) and isinstance(number2, (float, int))):
        raise TemplateSyntaxError('divide filter only receives float or int')
    
    return number1 / number2

@register.filter('character_from_unicode')
def character_from_unicode(number):
    return chr(number)