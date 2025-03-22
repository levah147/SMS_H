from django import template

register = template.Library()

@register.filter
def dict_lookup(dictionary, key):
    """Lookup a key in a dictionary and return its value."""
    return dictionary.get(key, None)






@register.filter
def get_item(dictionary, key):
    """Retrieve a value from a dictionary using a key in Django templates."""
    return dictionary.get(key, "")
