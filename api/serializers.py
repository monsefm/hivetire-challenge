from core.models import Vehicle, VehicleInspection
from rest_framework import serializers  

# FASE 1: Lista de Vehículos
class ListVehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'plate', 'active', 'brand', 'type', 'fleet']


# FASE 1: Lista de Inspecciones
class ListVehicleInspectionSerializer(serializers.ModelSerializer):
    vehicle_plate = serializers.CharField(source='vehicle.plate', read_only=True)

    class Meta:
        model = VehicleInspection
        fields = ['id', 'status', 'date', 'odometer', 'vehicle_id', 'vehicle_plate']


# FASE 3 - Creacion de Inspección
# Valida y transforma los datos enviados para crear una inspección desde la API.
class CreateInspectionSerializer(serializers.ModelSerializer):
    vehicle_id = serializers.IntegerField(required=True)
    odometer_km = serializers.FloatField(required=True, min_value=0)

    class Meta:
        model = VehicleInspection
        fields = ['vehicle_id', 'odometer_km']
