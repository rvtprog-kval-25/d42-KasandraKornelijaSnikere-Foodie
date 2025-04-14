from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # Authentication pages
    path('', include('counter.urls')),           # Your main app (food search, home)
]
