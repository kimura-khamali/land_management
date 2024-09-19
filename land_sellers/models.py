from django.db import models

# Create your models here.
from django.db import models

# Create your models here.
from django.db import models

# Create your models here.
from users.models import CustomUser

class LandSeller(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    lawyer = models.ForeignKey('lawyers.Lawyer', on_delete=models.SET_NULL, null=True, blank=True)
    address = models.CharField(max_length=25)

    def __str__(self):
        return f"{self.user.first_name} - {self.user.last_name}"