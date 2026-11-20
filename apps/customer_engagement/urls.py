from django.urls import path

from .views import signup_lead, send_otp, verify_otp, logout_view


urlpatterns = [

    path(
        'signup-lead/',
        signup_lead,
        name='signup_lead'
    ),

    path(
        'send-otp/',
        send_otp,
        name='send_otp'
    ),

    path(
        'verify-otp/',
        verify_otp,
        name='verify_otp'
    ),

    path(
        'logout/',
        logout_view,
        name='logout'
    ),

]