from django import template

register = template.Library()

@register.filter
def can_edit(comment, user):
    return comment.can_edit(user)

@register.filter
def can_delete(comment, user):
    return comment.can_delete(user) 