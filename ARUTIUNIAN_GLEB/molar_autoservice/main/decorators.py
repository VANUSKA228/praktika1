from django.shortcuts import redirect
from django.contrib import messages


def role_required(*roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            user_role = request.session.get("user_role")

            if not user_role:
                messages.error(request, "Сначала войдите в аккаунт")
                return redirect("/")

            if user_role not in roles:
                messages.error(request, "У вас нет доступа к этой странице")
                return redirect("/")

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator