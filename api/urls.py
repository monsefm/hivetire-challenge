from django.urls import path
from api.views import VehicleAPIView, VehicleDetailAPIView, VehicleInspectionAPIView, FinalizeInspectionAPIView


urlpatterns = [        
    path('vehicles/', VehicleAPIView.as_view(), name='vehicle-list'), 
    path('vehicles/<int:vehicle_id>/', VehicleDetailAPIView.as_view(), name='vehicle-detail'),   
    path('inspections/', VehicleInspectionAPIView.as_view(), name='inspections-actions'),    
    path('inspections/<int:id>/finalize/', FinalizeInspectionAPIView.as_view(), name='finalize-inspection')     
]