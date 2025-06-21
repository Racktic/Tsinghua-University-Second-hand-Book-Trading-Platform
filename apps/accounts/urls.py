from django.urls import path
from .views import RegisterView, LoginView, LogoutView, VerifyEmailView, CheckActivateView

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('send-verification-code', VerifyEmailView.as_view(), name='send-verification-code'),
    path('check-active', CheckActivateView.as_view(), name='check-active'),
]
