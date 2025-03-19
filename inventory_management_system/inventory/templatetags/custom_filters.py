# from django import template

# register = template.Library()

# @register.filter
# def getattr(obj, attr_name):
#     """Safely fetch an attribute from an object"""
#     if hasattr(obj, attr_name):
#         return getattr(obj, attr_name)
#     return ''  # Default empty string agar attribute na mile


from django import template

register = template.Library()

@register.filter
def remove_sort_field(sort_by, field):
    """ Remove a field from the sort_by string and clean up commas """
    fields = sort_by.split(",")  # Comma-separated sorting fields
    fields = [f for f in fields if f and f != field and f != f"-{field}"]  # Remove field and -field
    return ",".join(fields)  # Return cleaned string

@register.filter
def zip_list(a, b):
    """Zips two lists together for template rendering"""
    return zip(a, b)

@register.filter
def index(lst, i):
    """Gets the index value of a list"""
    try:
        return lst[i]
    except IndexError:
        return None
    
@register.filter
def get_item(dictionary, key):
    """Dictionary se key ka value return kare, agar key exist na kare to empty string return kare"""
    if isinstance(dictionary, dict):  # ✅ Ensure it's a dictionary
        return dictionary.get(key, "")
    return ""  # ✅ Default empty string if dictionary nahi hai
@register.filter
def dict_key(obj, key):
    return obj.get(key, "") if isinstance(obj, dict) else getattr(obj, key, "")

@register.filter
def split(value, key):
    """Split string using the provided key (e.g., comma)"""
    return value.split(key)