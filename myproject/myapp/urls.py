from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home_view'),
    path('pdf/<str:instanceUuid>/', views.report_view, name='report_view'),
]
