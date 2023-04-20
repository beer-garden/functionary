from django.contrib.auth.decorators import login_required
from django.contrib.messages import ERROR, add_message, get_messages
from django.shortcuts import render


@login_required
def retrieve_messages(request):
    all_messages = get_messages(request)

    return render(
        request,
        template_name="partials/messages.html",
        context={"messages": all_messages},
    )


@login_required
def display_generic_error(request):
    add_message(request, ERROR, "Sorry, something went wrong! Please try again.")
    return retrieve_messages(request)
