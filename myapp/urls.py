from django.urls import path
from . import views

urlpatterns = [
    # User URLs
    path('', views.home_1, name='home_1'),
    path('home-2/', views.home_2, name='home_2'),
    path('flight-booking/', views.flight_booking, name='flight_booking'),
    path('t-1/', views.t1_view, name='t_1'),
    path('register/', views.register, name='register'),
    path('signin/', views.signin, name='signin'),
    path('logout/', views.logout_view, name='logout'),
    path('search-flights/', views.search_flights, name='search_flights'),
    path('confirm-booking/', views.confirm_booking, name='confirm_booking'),
    path('thank-you/', views.thank_you, name='thank_you'),
    path('configure-twilio/', views.configure_twilio, name='configure_twilio'),
    path('cancel-booking/', views.cancel_booking, name='cancel_booking'),
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('help-desk/', views.help_desk, name='help_desk'),
    
    # Admin URLs
    path('admin/signin/', views.admin_signin, name='admin_signin'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/payment-history/', views.admin_payment_history, name='admin_payment_history'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/notifications/', views.admin_notifications, name='admin_notifications'),
    path('admin/flight-delays/', views.admin_flight_delays, name='admin_flight_delays'),
    path('admin/user-queries/', views.admin_user_queries, name='admin_user_queries'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),  # Added admin_logout URL pattern
    path('admin/seat-inventory/', views.admin_seat_inventory, name='admin_seat_inventory'),
    
]