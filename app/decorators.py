from functools import wraps

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url
import urllib.parse
from constance import config  # For the explicitly user-configurable stuff

from django.contrib.auth.decorators import user_passes_test

# There is really nothing that would prevent me from hijacking user_passes_test from the Django decorators here.
def constance_check(test_func, next_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    A wrapper for views that check specific constance settings. Only used for site_is_configured below.
    The test should be a callable
    that takes the user object and returns True if the user passes.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if test_func():
                # If the test function we were passed returns true, just return the view
                return view_func(request, *args, **kwargs)
            # Otherwise, build the redirect
            path = request.build_absolute_uri()
            resolved_setup_url = resolve_url(next_url or settings.CONSTANCE_SETUP_URL)
            # If the setup url is the same scheme and net location then just
            # use the path as the "next" url.
            setup_scheme, setup_netloc = urllib.parse.urlparse(resolved_setup_url)[:2]
            current_scheme, current_netloc = urllib.parse.urlparse(path)[:2]
            if ((not setup_scheme or setup_scheme == current_scheme) and
                    (not setup_netloc or setup_netloc == current_netloc)):
                path = request.get_full_path()
            # TODO - Change this to redirect, not redirect to login
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(path, resolved_setup_url, redirect_field_name)
        return _wrapped_view
    return decorator


def site_is_configured(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    def check_constance_is_configured():
        return config.USER_HAS_COMPLETED_CONFIGURATION

    actual_decorator = constance_check(
        check_constance_is_configured,
        next_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def login_if_required_for_dashboard(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in, redirecting to the log-in page if necessary -
    but only if REQUIRE_LOGIN_FOR_DASHBOARD is set True in Constance.
    """

    def authenticated_test(u):
        if config.REQUIRE_LOGIN_FOR_DASHBOARD:
            return u.is_authenticated
        else:
            return True

    actual_decorator = user_passes_test(
        authenticated_test,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def gravity_support_enabled(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    def check_gravity_support_enabled():
        return config.GRAVITY_SUPPORT_ENABLED

    actual_decorator = constance_check(
        check_gravity_support_enabled,
        next_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
