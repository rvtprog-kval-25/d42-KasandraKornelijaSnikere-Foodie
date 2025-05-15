from django.contrib import admin
from django.urls import path, include
from django.contrib import admin

admin.site.site_header = "Foodie Administration"
admin.site.site_title = "Foodie Admin Portal"
admin.site.index_title = "Welcome to Foodie Admin"


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # Authentication pages
    path('', include('counter.urls')),           # Your main app (food search, home)
]
