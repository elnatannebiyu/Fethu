from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

# ============================================================================
# Permission Mixins for Class-Based Views
# ============================================================================

class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin for views that require admin access"""
    
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.role == 'admin' or 
            self.request.user.is_superuser
        )
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('core:dashboard')


class LoadingPersonnelRequiredMixin(UserPassesTestMixin):
    """Mixin for views that require loading personnel access"""
    
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.role == 'loading' or
            self.request.user.role == 'admin' or
            self.request.user.is_superuser
        )
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('core:dashboard')


class ReceptionRequiredMixin(UserPassesTestMixin):
    """Mixin for views that require reception access"""
    
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.role == 'reception' or
            self.request.user.role == 'admin' or
            self.request.user.is_superuser
        )
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('core:dashboard')


class AnyStaffRequiredMixin(UserPassesTestMixin):
    """Mixin for views that any staff can access"""
    
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.role in ['admin', 'loading', 'reception'] or
            self.request.user.is_superuser
        )
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('accounts:login')

# ============================================================================
# Permission Decorators for Function-Based Views
# ============================================================================

def admin_required(view_func):
    """Decorator for function-based views that require admin access"""
    return role_required(['admin'])(view_func)


def loading_personnel_required(view_func):
    """Decorator for function-based views that require loading personnel access"""
    return role_required(['loading', 'admin'])(view_func)


def reception_required(view_func):
    """Decorator for function-based views that require reception access"""
    return role_required(['reception', 'admin'])(view_func)


def any_staff_required(view_func):
    """Decorator for function-based views that any staff can access"""
    return role_required(['admin', 'loading', 'reception'])(view_func)


def role_required(allowed_roles):
    """Generic decorator for custom role requirements"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to access this page.")
                return redirect('accounts:login')
            
            if request.user.role in allowed_roles or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, "You don't have permission to access this page.")
            return redirect('core:dashboard')
        return _wrapped_view
    return decorator