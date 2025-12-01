from django.urls import path
from .views import BlogViewsAPI, TopAPI, PerformanceAPI

urlpatterns = [
    path('blog-views/', BlogViewsAPI.as_view(), name='blog-views'),
    path('top/', TopAPI.as_view(), name='top'),
    path('performance/', PerformanceAPI.as_view(), name='performance'),
]