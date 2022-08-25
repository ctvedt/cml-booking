from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path('', views.RenderCalendar, name='index'),
    path('booking/', RedirectView.as_view(url='/')),
    path('booking/<int:day>/', views.CreateNewBooking),
    path('booking/<int:day>/<int:slot>/', views.CreateNewBooking),
    path('cancel/<str:cancelcode>/', views.CancelBooking)
]
