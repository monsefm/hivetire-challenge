from django.db import models

class Vehicle(models.Model):
    active = models.BooleanField()
    plate = models.CharField(max_length=200)
    brand = models.CharField(max_length=200)
    type = models.CharField(max_length=200)
    fleet = models.CharField(max_length=200)

class VehicleInspection(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    date = models.DateTimeField()
    odometer = models.FloatField(default=0)
    status = models.IntegerField(
        choices=[
            (1, "En Curso"),
            (2, "Finalizada")
        ]
    )




