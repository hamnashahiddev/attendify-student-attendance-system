from .models import SiteSetting, Notification


def attendify_context(request):
    ctx = {
        "site_setting": SiteSetting.get(),
    }
    if request.user.is_authenticated:
        ctx["unread_notifications_count"] = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
        ctx["recent_notifications"] = Notification.objects.filter(
            user=request.user
        ).order_by("-created_at")[:5]
    else:
        ctx["unread_notifications_count"] = 0
        ctx["recent_notifications"] = []
    return ctx
