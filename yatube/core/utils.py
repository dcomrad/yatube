from functools import wraps

from django.core.cache import cache
from django.urls import reverse


def get_login_redirect_url(from_url):
    """Формирует URL при перенаправлении неавторизованных пользователей"""
    login_url = reverse('users:login')
    if from_url:
        return f'{login_url}?next={from_url}'
    else:
        return login_url


def clear_cache(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        cache.clear()
        return func(*args, **kwargs)
    return wrapper
