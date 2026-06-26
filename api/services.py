from core.models import Vehicle, VehicleInspection
from django.db.models import OuterRef, Subquery
from django.utils import timezone
from rest_framework.exceptions import ValidationError
import datetime


### FASE 1
# Se utilizan filtros como marca, tipo, flota, placa y estado para responder a consultas habituales
# de operación de una flota, como localizar unidades por características, zona o disponibilidad.
def get_queryset_vehicle(parametros):
    queryset = Vehicle.objects.all()

    # El filtro por marca permite agrupar o localizar vehículos de una misma referencia.
    if parametros.get('brand'):
        queryset = queryset.filter(brand__icontains=parametros['brand'])

    # El filtro por tipo ayuda a segmentar la flota por categoría operativa.
    if parametros.get('type'):
        queryset = queryset.filter(type__icontains=parametros['type'])

    # El filtro por fleet permite ver rápidamente los vehículos asignados a una zona o región de operación.
    if parametros.get('fleet'):        
        fleet_normalized = parametros['fleet'].lower()

        if fleet_normalized in ['norte', 'sur', 'centro']:
            queryset = queryset.filter(fleet__iexact=parametros['fleet'])
        else:
            raise ValidationError('El filtro fleet solo acepta las opciones: Norte, Sur o Centro.')

    # El filtro por placa es útil para localizar una unidad específica con búsquedas parciales.
    if parametros.get('plate'):
        queryset = queryset.filter(plate__icontains=parametros['plate'])
    
    # El filtro por estado activo/inactivo permite identificar unidades operativas o fuera de servicio.
    if parametros.get('active'):
        val = int(parametros['active'])
        if val in [0, 1]:
            active_value = bool(val)
            queryset = queryset.filter(active=active_value)        
        else:
            raise ValidationError('El filtro active solo acepta los valores 0 o 1.')
        
    # El ordenamiento permite presentar la información de la flota de forma útil según prioridad operativa.
    par_tipo_orden = parametros.get('order_by', 'id')
    pars_permitidos = ['id', 'plate', 'brand', 'type', 'fleet', 'active', '-id', '-plate', '-brand', '-type', '-fleet', '-active']
    
    if par_tipo_orden in pars_permitidos:
        queryset = queryset.order_by(par_tipo_orden)
    else:
        queryset = queryset.order_by('id')

    return queryset


### FASE 1
# Se incluyen filtros de inspección por unidad, estado, placa, fechas y odómetro porque son criterios
# habituales para monitorear el mantenimiento y desempeño de una flota.
def get_queryset_vehicle_inspection(parametros):  
    queryset = VehicleInspection.objects.all()   
    
    # El filtro por vehicle_id permite revisar el historial de inspecciones de una unidad específica.
    if parametros.get('vehicle_id'):
        queryset = queryset.filter(vehicle__id=parametros['vehicle_id'])

    # El filtro por status permite distinguir inspecciones en curso de las finalizadas.
    if parametros.get('status'):        
        status_valor = int(parametros['status'])       
        if status_valor in [1, 2]:
            queryset = queryset.filter(status=status_valor)
        else:
            raise ValidationError('El filtro status solo acepta los valores 1 o 2.')
     
    
    # El filtro por placa del vehículo ayuda a encontrar inspecciones asociadas a una unidad concreta.
    if parametros.get('vehicle_plate'):
        queryset = queryset.filter(vehicle__plate__icontains=parametros['vehicle_plate'])

    # El rango de fechas permite analizar inspecciones dentro de un periodo para control operativo y mantenimiento.
    if parametros.get('date_start') and parametros.get('date_end'):
        try:
            date_start_format = datetime.datetime.strptime(parametros['date_start'], '%d-%m-%Y')
            date_end_format = datetime.datetime.strptime(parametros['date_end'], '%d-%m-%Y')
        except ValueError as exc:
            raise ValidationError('Las fechas deben tener el formato DD-MM-YYYY.') from exc

        if date_start_format > date_end_format:
            raise ValidationError('La fecha de inicio no puede ser mayor que la fecha de fin.')

        date_start_bd = date_start_format.strftime('%Y-%m-%dT%H:%M:%SZ')
        date_end_bd = date_end_format.strftime('%Y-%m-%dT%H:%M:%SZ')

        queryset = queryset.filter(date__range=(date_start_bd, date_end_bd))
    

    # El rango de odómetro permite identificar inspecciones relacionadas con uso intensivo o desgaste de la flota.
    if parametros.get('odometer_min') and parametros.get('odometer_max'):
        try:
            odometer_min = float(parametros['odometer_min'])
            odometer_max = float(parametros['odometer_max'])

            if odometer_min > odometer_max:
                raise ValidationError('El odómetro máximo no puede ser menor que el odómetro mínimo.')
        
            queryset = queryset.filter(odometer__range=(odometer_min, odometer_max))
        except ValueError as exc:
            raise ValidationError('Los valores del odómetro deben ser números válidos.') from exc

    # El ordenamiento por fecha, odómetro, estado o placa ayuda a priorizar revisiones y seguimiento de la flota.
    par_tipo_orden = parametros.get('order_by', 'id')
    pars_permitidos = ['id', 'date', 'odometer', 'status','vehicle__plate', '-id', '-date', '-odometer', '-status', '-vehicle__plate']
    
    if par_tipo_orden in pars_permitidos:
        queryset = queryset.order_by(par_tipo_orden)
    else:
        queryset = queryset.order_by('id')
    
    return queryset


### FASE 2:
# Se obtiene el detalle de un vehículo junto con su última inspección para tener una vista rápida
# del estado operativo y mantenimiento de la unidad dentro de la flota.
def get_queryset_vehicle_detail(vehicle_id):    
    ultima_inspeccion = VehicleInspection.objects.filter(vehicle=OuterRef('pk')).order_by('-date')
    queryset = Vehicle.objects.filter(pk=vehicle_id).annotate(
        ui_status=Subquery(ultima_inspeccion.values('status')[:1]),
        ui_date=Subquery(ultima_inspeccion.values('date')[:1]),
        ui_odometer=Subquery(ultima_inspeccion.values('odometer')[:1])
    ).values('id', 'plate', 'active', 'brand', 'type', 'fleet', 'ui_status', 'ui_date', 'ui_odometer')
    
    vehicle = queryset.first()
    if not vehicle:
        return None
    
    last_inspection = None
    if vehicle['ui_status'] is not None:
        last_inspection = {
            'status': 'En Curso' if vehicle['ui_status'] == 1 else 'Finalizada',           
            'date': vehicle['ui_date'].strftime('%Y-%m-%d') if vehicle['ui_date'] else None,
            'odometer_km': vehicle['ui_odometer']
        }
    
    return {
        'id': vehicle['id'],
        'plate': vehicle['plate'],
        'active': vehicle['active'],
        'brand': vehicle['brand'],
        'type': vehicle['type'],
        'fleet': vehicle['fleet'],
        'last_inspection': last_inspection 
    }


### FASE 3
# Se crean inspecciones con validaciones para asegurar que solo unidades activas
# y sin inspecciones en curso puedan generar un nuevo registro de mantenimiento.
def create_inspection(vehicle_id, odometer_km):
    vehicle = Vehicle.objects.filter(id=vehicle_id).only('id', 'active').first()
    if not vehicle:
        raise ValidationError('El vehículo no existe.')
    
    if not vehicle.active:
        raise ValidationError('El vehículo no está activo.')
    
    if VehicleInspection.objects.filter(vehicle=vehicle, status=1).exists():
        raise ValidationError('El vehículo ya tiene una inspección en curso.')

    inspection = VehicleInspection.objects.create(
        vehicle=vehicle,
        date=timezone.now(),
        odometer=odometer_km,
        status=1
    )
    return inspection


# Se finaliza una inspección existente para cerrar el ciclo de mantenimiento de una unidad.
def finalize_inspection(id_inspection):
    inspection = VehicleInspection.objects.filter(id=id_inspection).first()
    
    if not inspection:
        raise ValidationError('La inspección no existe.')
    
    if inspection.status != 1:
        raise ValidationError('La inspección no está En Curso (ya ha sido finalizada).')

    inspection.status = 2
    inspection.save()
    return inspection