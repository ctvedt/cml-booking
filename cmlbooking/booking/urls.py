from django.urls import path

from . import views

urlpatterns = [
    path('', views.RenderCalendar, name='index'),
    path('booking/', views.CreateNewBooking, name='booking'),
    path('booking/<int:day>/', views.CreateNewBooking, name='booking'),
    path('booking/<int:day>/<int:slot>/', views.CreateNewBooking, name='booking'),
]
