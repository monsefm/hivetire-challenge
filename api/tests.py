from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import Vehicle, VehicleInspection

# Create your tests here.
class HiveTireAPITests(APITestCase):

    def setUp(self):
        #Configuración inicial: Creación de datos para poder probar las rutas de la API.

        self.vehicule_active = Vehicle.objects.create(
            active=True,
            plate='ABC123',
            brand='Toyota',
            type='Sedan',
            fleet='Norte'
        )

        self.vehicule_inactive = Vehicle.objects.create(
            active=False,   
            plate='XYZ-789',
            brand='Volvo',
            type='Furgón',
            fleet='Sur'
        )
       
        #Mapeo de URLs
        self.url_vehicles_list = reverse('vehicle-list')
        self.url_inspections_actions = reverse('inspections-actions')
    

    def test_obtener_detalle_vehiculo(self):
        #Verifica que el detalle del vehículo retorne la última inspección formateada en YYYY-MM-DD.
        # Creamos una inspección con una fecha y hora específica para probar el formato limpio
        fecha_prueba = timezone.now()
        VehicleInspection.objects.create(
            vehicle=self.vehicule_active,
            date=fecha_prueba,
            odometer=12500.0,
            status=2  # Finalizada
        )

        # Construimos dinámicamente la URL usando el name de tu urlpattern
        url_detail = reverse('vehicle-detail', kwargs={'vehicle_id': self.vehicule_active.id})
        response = self.client.get(url_detail)

        # Validaciones de la estructura solicitada
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.vehicule_active.id)
        self.assertEqual(response.data['plate'], 'ABC123')
        
        # Comprobamos el objeto last_inspection y su formato de fecha estricto YYYY-MM-DD
        self.assertIsNotNone(response.data['last_inspection'])
        self.assertEqual(response.data['last_inspection']['status'], 'Finalizada')
        self.assertEqual(response.data['last_inspection']['date'], fecha_prueba.strftime('%Y-%m-%d'))


    def test_obtener_detalle_error(self):
        #Verifica que se retorne un 404 si el ID del vehículo no existe.
        url_detail = reverse('vehicle-detail', kwargs={'vehicle_id': 99999})
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    
    def test_ciclo_completo_crear_finalizar_inspeccion_success(self):       
        payload = {
            "vehicle_id": self.vehicule_active.id,
            "odometer_km": 12500.0
        }
        
        response_create = self.client.post(self.url_inspections_actions, payload, format='json')
        
        # Validamos que se creó correctamente
        self.assertEqual(response_create.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_create.data['status'], 1) #En curso        
       
        inspection_id = response_create.data['id']

        #Finalizar inspección
        url_finalize = reverse('finalize-inspection', kwargs={'id': inspection_id})
        
        # Enviamos el PATCH vacío
        response_finalize = self.client.patch(url_finalize, format='json')
        
        # Validamos que se finalizó correctamente
        self.assertEqual(response_finalize.status_code, status.HTTP_200_OK)
        self.assertEqual(response_finalize.data['status'], 2)
    
    
    def test_crear_inspeccion_vehiculo_inactivo_fails(self):
        #Prueba que la API bloquee la creación si el vehículo está inactivo.
        payload = {
            "vehicle_id": self.vehicule_inactive.id,
            "odometer_km": 90000.0
        }
        
        response = self.client.post(self.url_inspections_actions, payload, format='json')
        
        # Validaciones: Debe dar un error 400 Bad Request por las reglas de negocio
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    

    def test_finalizar_inspeccion_error(self):
        #Validación: Error si intentamos finalizar una inspección que ya está terminada.
        inspection = VehicleInspection.objects.create(
            vehicle=self.vehicule_active,
            date=timezone.now(),
            odometer=60000.0,
            status=2  # Ya finalizada
        )
        
        url_finalize = reverse('finalize-inspection', kwargs={'id': inspection.id})
        response = self.client.patch(url_finalize, format='json')
        
        # Debe lanzar error de negocio
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)