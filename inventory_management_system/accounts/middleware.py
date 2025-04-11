from django.utils import timezone
from django.contrib.auth import logout
from .views import get_client_ip


MIDDLEWARE_SESSION_TIMEOUT = 10 * 60

class InactivityTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("🔴 Middleware called")
        user = request.user
        print(f"🔴 User: {user}")
        if user.is_authenticated:
            print("🔴 User is authenticated")
            current_ip = get_client_ip(request)
            now = timezone.now()
            last_activity = user.last_activity
            
            if last_activity:
                try:
                    print("🔴 Last activity is not None")
                    elapsed = (now - last_activity).total_seconds()
                    print(f"🔴 Elapsed time: {elapsed} seconds")
                    if elapsed > MIDDLEWARE_SESSION_TIMEOUT:
                        print("🔴 Elapsed time is greater than session timeout")
                        # Reset device info
                        user.last_ip_address = None
                        user.last_login_device = None
                        user.last_logout_device = now
                        user.save()
                        logout(request)
                        print("✅ Logged out due to inactivity + reset IP")
                    else:
                        print("🔴 Elapsed time is less than session timeout")
                        user.last_activity = now
                        print(f"🔴 Last activity: {user.last_activity}")
                        user.save()

                    if current_ip != user.last_ip_address:
                        print("🔴 Current IP is different from last IP")
                        logout(request)
                        print("✅ Logged out due to IP change")
                except Exception as e:
                    print("❌ Middleware error:", e)

            # Always update activity time

        return self.get_response(request)
