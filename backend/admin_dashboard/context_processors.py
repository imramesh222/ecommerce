def admin_dashboard_context(request):
    """
    Context processor that adds common context variables to all admin dashboard templates.
    """
    context = {
        'site_name': 'E-Commerce Admin',
        'site_header': 'E-Commerce Admin',
        'site_title': 'E-Commerce Admin',
        'site_url': '/admin/',
    }
    
    # Add user info if authenticated
    if hasattr(request, 'user') and request.user.is_authenticated:
        context.update({
            'user': request.user,
            'is_staff': request.user.is_staff,
            'is_superuser': request.user.is_superuser,
        })
    
    return context
