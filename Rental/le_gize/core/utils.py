from django.db.models import Q
from django.contrib import messages
from django.shortcuts import render


def apply_search_filters(queryset, search_query, fields):
    """Apply case-insensitive icontains filtering across provided fields."""
    if not search_query:
        return queryset

    combined_query = Q()
    for field in fields:
        combined_query |= Q(**{f"{field}__icontains": search_query})

    return queryset.filter(combined_query)


def flash_success(request, subject, action):
    """Reusable helper for success messages."""
    messages.success(request, f'{subject} {action} successfully!')


def flash_error(request, message):
    """Reusable helper for error messages."""
    messages.error(request, message)


def render_form(request, template, form, title, submit_text, extra_context=None):
    """Render a standard CRUD form template with shared context."""
    context = {
        'form': form,
        'title': title,
        'submit_text': submit_text,
    }
    if extra_context:
        context.update(extra_context)
    return render(request, template, context)
