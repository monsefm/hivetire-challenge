from django.shortcuts import render
from api.serializers import ListVehicleSerializer, ListVehicleInspectionSerializer, CreateInspectionSerializer
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from api import services, pagination


### FASE 1 - Lista de Vehículos
class VehicleAPIView(APIView):
    pagination_class = pagination.ShowPagination

    # Lista los vehículos paginados y devuelve la respuesta formateada para la API.
    def get(self, request):       
        queryset = services.get_queryset_vehicle(request.query_params)         
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        
        serializer = ListVehicleSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

       

### FASE 1 - Lista de Inpecciones
### FASE 3 - Creación de Inspección
class VehicleInspectionAPIView(APIView):
    pagination_class = pagination.ShowPagination

    # Lista las inspecciones paginadas y devuelve la información de cada inspección con la placa del vehículo.
    def get(self, request):       
        queryset = services.get_queryset_vehicle_inspection(request.query_params)         
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        
        serializer = ListVehicleInspectionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)   
    
    # Crea una nueva inspección validando el payload y manejando errores de negocio.
    def post(self, request):       
        serializer = CreateInspectionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            inspeccion = services.create_inspection(
                vehicle_id=serializer.validated_data['vehicle_id'], 
                odometer_km=serializer.validated_data['odometer_km'] 
            )
        except ValidationError as error:            
            return Response(error.detail, status=status.HTTP_400_BAD_REQUEST)
        
        # Reutilizamos el serializador de listado para devolver la respuesta limpia
        response_serializer = ListVehicleInspectionSerializer(inspeccion)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


### FASE 2: Visualización de detalle del vehículo.
# Devuelve el detalle de un vehículo junto con su última inspección.
class VehicleDetailAPIView(APIView):

    def get(self, request, vehicle_id):
        vehicle = services.get_queryset_vehicle_detail(vehicle_id)        
        if not vehicle:
            return Response({'detail': 'El vehículo no fue encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(vehicle, status=status.HTTP_200_OK)


class FinalizeInspectionAPIView(APIView):
    # Finaliza una inspección existente cambiando su estado a finalizada.
    def patch(self, request, id):
        try:
            inspeccion = services.finalize_inspection(id)
        
        except ValidationError as error:           
            return Response({'detail': error.detail[0]}, status=status.HTTP_400_BAD_REQUEST)        
       
        return Response({
            'id': inspeccion.id,
            'status': inspeccion.status,
            'date': inspeccion.date,
            'odometer': inspeccion.odometer,
            'vehicle_id': inspeccion.vehicle_id,
        }, status=status.HTTP_200_OK)