from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home_view'),
    # path('pdf/', views.some_view, name='some_view'),
    path('pdf/<int:instance_id>/', views.some_view, name='some_view'),
]
