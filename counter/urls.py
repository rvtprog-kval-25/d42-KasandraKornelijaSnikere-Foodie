from django.urls import path
from .views import diary_view
from . import views
from .views import weight_progress_view

urlpatterns = [
    path('', views.home, name='home'),
    path('diary/', diary_view, name='diary'),
    path('diary/delete/<int:food_id>/', views.delete_food_entry, name='delete_food'),
    path('calorie-setup/', views.calorie_setup_view, name='calorie_setup'),
    path('progress/', weight_progress_view, name='weight_progress'),
    path('add-custom-food/', views.custom_food_entry_view, name='add_custom_food'),
    path('download-diary-pdf/', views.download_diary_pdf, name='download_diary_pdf'),
    path('download-weight-pdf/', views.download_weight_pdf, name='download_weight_pdf'),


]