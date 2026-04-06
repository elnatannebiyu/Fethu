from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator

from core.mixins import admin_required, any_staff_required
from core.utils import apply_search_filters, flash_success, flash_error, render_form

from .models import User
from .forms import UserCreationForm, UserChangeForm, ProfileUpdateForm

# ============================================================================
# Authentication Views (Public)
# ============================================================================

def login_view(request):
    """Handle user login with role-based redirects"""
    if request.user.is_authenticated:
        return redirect_based_on_role(request.user)
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
                return redirect_based_on_role(user)
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@never_cache
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('accounts:login')

def redirect_based_on_role(user):
    """Helper function to redirect users based on their role"""
    if user.role == 'admin' or user.is_superuser:
        return redirect('core:admin_dashboard')
    elif user.role == 'loading':
        return redirect('core:loading_dashboard')
    elif user.role == 'reception':
        return redirect('personnel:reception_user_dashboard')
    else:  # reception
        return redirect('orders:list')

# ============================================================================
# Profile Management Views (Any logged-in user)
# ============================================================================

@login_required
@never_cache
def profile_view(request):
    """Display user profile"""
    return render(request, 'accounts/profile.html', {'user': request.user})

@login_required
@never_cache
def profile_edit_view(request):
    """Edit user profile"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'accounts/profile_edit.html', {'form': form})

@login_required
@never_cache
def change_password_view(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully changed!")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})

# ============================================================================
# User Management Views (Admin Only)
# ============================================================================

@login_required
@admin_required
def user_list_view(request):
    """List all users with search and filter (admin only)"""
    users = User.objects.all().order_by('-date_joined')
    
    search_query = request.GET.get('search', '')
    users = apply_search_filters(users, search_query, [
        'username', 'email', 'first_name', 'last_name', 'phone'
    ])
    
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)
    
    active_filter = request.GET.get('active', '')
    if active_filter == 'active':
        users = users.filter(is_active=True)
    elif active_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'users': page_obj.object_list,
        'page_obj': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
        'active_filter': active_filter,
        'role_choices': User.ROLE_CHOICES,
    }
    return render(request, 'accounts/user_list.html', context)

@login_required
@admin_required
def user_create_view(request):
    """Create a new user (admin only)"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            flash_success(request, f"User {user.username}", "created")
            return redirect('accounts:user_list')
        flash_error(request, "Please correct the errors below.")
    else:
        form = UserCreationForm()
    
    return render_form(
        request,
        'accounts/user_form.html',
        form,
        'Create New User',
        'Create User'
    )

@login_required
@admin_required
def user_edit_view(request, user_id):
    """Edit an existing user (admin only)"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            flash_success(request, f"User {user.username}", "updated")
            return redirect('accounts:user_list')
        flash_error(request, "Please correct the errors below.")
    else:
        form = UserChangeForm(instance=user)
    
    return render_form(
        request,
        'accounts/user_form.html',
        form,
        f'Edit User: {user.username}',
        'Update User',
        {'user': user}
    )

@login_required
@admin_required
def user_delete_view(request, user_id):
    """Delete a user (admin only)"""
    user = get_object_or_404(User, id=user_id)
    
    if user.id == request.user.id:
        messages.error(request, "You cannot delete your own account!")
        return redirect('accounts:user_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        flash_success(request, f"User {username}", "deleted")
        return redirect('accounts:user_list')
    
    return render(request, 'accounts/user_confirm_delete.html', {'user': user})

@login_required
@admin_required
def user_toggle_active_view(request, user_id):
    """Toggle user active status (admin only)"""
    user = get_object_or_404(User, id=user_id)
    
    if user.id == request.user.id:
        messages.error(request, "You cannot change your own status!")
        return redirect('accounts:user_list')
    
    user.is_active = not user.is_active
    user.save()
    
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.username} has been {status}.")
    return redirect('accounts:user_list')