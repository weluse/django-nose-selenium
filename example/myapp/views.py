from django.shortcuts import render_to_response


def view1(request):
    """A simple view rendering a 'Hello World' HTML page."""

    return render_to_response("myapp/view1.html")


# Temporary solution
view2 = view1
