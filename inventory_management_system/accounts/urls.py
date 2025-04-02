from django.urls import path
from .views import login_view, logout_view , reset_last_ip


app_name ="accounts"
urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path('reset-last-ip/', reset_last_ip, name='reset_last_ip'),
]
