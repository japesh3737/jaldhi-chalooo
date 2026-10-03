from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'), path('planner/', views.planner, name='planner'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('routes/<int:pk>/rename/', views.rename_route, name='rename_route'),
    path('routes/<int:pk>/delete/', views.delete_route, name='delete_route'),
    path('api/sample/', views.sample, name='sample'), path('api/optimize/', views.optimize, name='optimize'),
    path('api/geocode/', views.address_search, name='geocode'), path('api/routes/save/', views.save_route, name='save_route'),
    path('export/<str:token>/', views.export_csv, name='export_csv'),
]
