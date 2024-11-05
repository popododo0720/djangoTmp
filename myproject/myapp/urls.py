from django.urls import path
from . import views, basic

urlpatterns = [
    path('', views.home_view, name='home_view'),
    path('pdf/<int:instance_id>/', basic.some_view, name='some_view'),
]
