from django.shortcuts import redirect
import functools


def unauthenticated_user(view_func):

    # @functools.wraps(view_func)
    # def unauthenticated_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        else:
            return redirect("api_login")
    return wrapper_func


def allowed_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if not request.user.security_pin:
            return redirect('api_login')
        elif not request.user.otpConfirm:
            return redirect('api_login')
        else:
            return view_func(request, *args, **kwargs)
    return wrapper_func