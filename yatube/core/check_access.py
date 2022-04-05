from functools import wraps

from django.shortcuts import redirect


def only_user_view(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("/auth/only_user/")
        return func(request, *args, **kwargs)

    return wrapper


def only_anon_view(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("/auth/only_anon/")
        return func(request, *args, **kwargs)

    return wrapper
