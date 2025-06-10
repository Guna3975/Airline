

# inido/urls.py
from django.contrib import admin
from django.urls import path, include  # Add 'include' here



urlpatterns = [
      # Admin URL
    path('', include('myapp.urls')),  # Delegate all app URLs to myapp/urls.py
    path('admin/', admin.site.urls),
  
]

