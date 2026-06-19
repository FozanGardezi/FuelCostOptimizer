from django.urls import path

from .views import RouteFuelPlanView

urlpatterns = [
    path('route/', RouteFuelPlanView.as_view(), name='route-fuel-plan'),
]
