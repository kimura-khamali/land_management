from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

def validate_phone_number(value):
    if not value.startswith('+'):
        raise ValidationError(_('Phone number must start with a "+" sign.'))
    digits = value[1:]
    if not digits.isdigit() or not (9 <= len(digits) <= 13):
        raise ValidationError(_('Phone number must contain 9 to 13 digits after the "+" sign.'))

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, first_name, last_name, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone Number field must be set')
        if not first_name or not last_name:
            raise ValueError('The first name and last name must be set')
        
        user = self.model(
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, first_name, last_name, password, **extra_fields)

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('lawyer', 'Lawyer'),
        ('admin', 'Admin'),
    ]
    phone_number = models.CharField(validators=[validate_phone_number], max_length=14, unique=True)
    is_phone_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    username = None  
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.phone_number} - {self.role}"

class RegistrationCode(models.Model):
    phone_number = models.CharField(max_length=17)
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('phone_number', 'code')

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.phone_number} - {self.code}"


















# # models.py

# from django.contrib.auth.models import AbstractUser, BaseUserManager
# from django.db import models
# from django.core.exceptions import ValidationError
# from django.utils.translation import gettext_lazy as _
# from django.utils import timezone

# def validate_phone_number(value):
#     if not value.startswith('+'):
#         raise ValidationError(_('Phone number must start with a "+" sign.'))
#     digits = value[1:]
#     if not digits.isdigit() or not (9 <= len(digits) <= 13):
#         raise ValidationError(_('Phone number must contain 9 to 13 digits after the "+" sign.'))

# class CustomUserManager(BaseUserManager):
#     def create_user(self, phone_number, first_name, last_name, password=None, **extra_fields):
#         if not phone_number:
#             raise ValueError('The Phone Number field must be set')
#         if not first_name or not last_name:
#             raise ValueError('The first name and last name must be set')
        
#         user = self.model(
#             phone_number=phone_number,
#             first_name=first_name,
#             last_name=last_name,
#             **extra_fields
#         )
#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, phone_number, first_name, last_name, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)
#         extra_fields.setdefault('role', 'admin')
        
#         if extra_fields.get('is_staff') is not True:
#             raise ValueError('Superuser must have is_staff=True.')
#         if extra_fields.get('is_superuser') is not True:
#             raise ValueError('Superuser must have is_superuser=True.')

#         return self.create_user(phone_number, first_name, last_name, password, **extra_fields)

# class CustomUser(AbstractUser):
#     ROLE_CHOICES = [
#         ('buyer', 'Buyer'),
#         ('seller', 'Seller'),
#         ('lawyer', 'Lawyer'),
#         ('admin', 'Admin'),
#     ]
#     phone_number = models.CharField(validators=[validate_phone_number], max_length=14, unique=True)
#     is_phone_verified = models.BooleanField(default=False)
#     role = models.CharField(max_length=10, choices=ROLE_CHOICES)

#     username = None  
#     USERNAME_FIELD = 'phone_number'
#     REQUIRED_FIELDS = ['first_name', 'last_name']

#     objects = CustomUserManager()

#     def __str__(self):
#         return f"{self.phone_number} - {self.role}"

# class RegistrationCode(models.Model):
#     phone_number = models.CharField(max_length=17)
#     code = models.CharField(max_length=6)
#     expires_at = models.DateTimeField(default=timezone.now)

#     class Meta:
#         unique_together = ('phone_number', 'code')

#     def is_expired(self):
#         return timezone.now() > self.expires_at

#     def __str__(self):
#         return f"{self.phone_number} - {self.code}"
















# # users/models.py

# from django.contrib.auth.models import AbstractUser, BaseUserManager
# from django.db import models
# from django.core.exceptions import ValidationError
# from django.utils.translation import gettext_lazy as _
# from django.utils import timezone

# def validate_phone_number(value):
#     if not value.startswith('+'):
#         raise ValidationError(_('Phone number must start with a "+" sign.'))
#     digits = value[1:]
#     if not digits.isdigit() or not (9 <= len(digits) <= 13):
#         raise ValidationError(_('Phone number must contain 9 to 13 digits after the "+" sign.'))

# class CustomUserManager(BaseUserManager):
#     def create_user(self, phone_number, first_name, last_name, password=None, **extra_fields):
#         if not phone_number:
#             raise ValueError('The Phone Number field must be set')
#         if not first_name or not last_name:
#             raise ValueError('The first name and last name must be set')
        
#         user = self.model(
#             phone_number=phone_number,
#             first_name=first_name,
#             last_name=last_name,
#             **extra_fields
#         )
#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, phone_number, first_name, last_name, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)
#         extra_fields.setdefault('role', 'admin')
        
#         if extra_fields.get('is_staff') is not True:
#             raise ValueError('Superuser must have is_staff=True.')
#         if extra_fields.get('is_superuser') is not True:
#             raise ValueError('Superuser must have is_superuser=True.')

#         return self.create_user(phone_number, first_name, last_name, password, **extra_fields)

# class CustomUser(AbstractUser):
#     ROLE_CHOICES = [
#         ('buyer', 'Buyer'),
#         ('seller', 'Seller'),
#         ('lawyer', 'Lawyer'),
#         ('admin', 'Admin'),
#     ]
#     phone_number = models.CharField(validators=[validate_phone_number], max_length=14, unique=True)
#     is_phone_verified = models.BooleanField(default=False)
#     role = models.CharField(max_length=10, choices=ROLE_CHOICES)

#     username = None  
#     USERNAME_FIELD = 'phone_number'
#     REQUIRED_FIELDS = ['first_name', 'last_name']

#     objects = CustomUserManager()

#     def __str__(self):
#         return f"{self.phone_number} - {self.role}"

#     def is_buyer(self):
#         return self.role == 'buyer'

#     def is_seller(self):
#         return self.role == 'seller'

#     def is_lawyer(self):
#         return self.role == 'lawyer'

#     def is_admin(self):
#         return self.role == 'admin'

# class RegistrationCode(models.Model):
#     phone_number = models.CharField(max_length=17)
#     code = models.CharField(max_length=6)
#     expires_at = models.DateTimeField(default=timezone.now)

#     class Meta:
#         unique_together = ('phone_number', 'code')

#     def is_expired(self):
#         return timezone.now() > self.expires_at

#     def __str__(self):
#         return f"{self.phone_number} - {self.code}"






# from django.contrib.auth.models import AbstractUser, BaseUserManager
# from django.db import models
# from django.core.exceptions import ValidationError
# from django.utils.translation import gettext_lazy as _
# from django.utils import timezone

# def validate_phone_number(value):
#     if not value.startswith('+'):
#         raise ValidationError(_('Phone number must start with a "+" sign.'))
#     digits = value[1:]
#     if not digits.isdigit() or not (9 <= len(digits) <= 13):
#         raise ValidationError(_('Phone number must contain 9 to 13 digits after the "+" sign.'))

# class CustomUserManager(BaseUserManager):
#     def create_user(self, phone_number, first_name, last_name, password=None, **extra_fields):
#         if not phone_number:
#             raise ValueError('The Phone Number field must be set')
#         if not first_name or not last_name:
#             raise ValueError('The first name and last name must be set')
        
#         user = self.model(
#             phone_number=phone_number,
#             first_name=first_name,
#             last_name=last_name,
#             **extra_fields
#         )
#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, phone_number, first_name, last_name, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)
#         extra_fields.setdefault('role', 'admin')
        
#         if extra_fields.get('is_staff') is not True:
#             raise ValueError('Superuser must have is_staff=True.')
#         if extra_fields.get('is_superuser') is not True:
#             raise ValueError('Superuser must have is_superuser=True.')

#         return self.create_user(phone_number, first_name, last_name, password, **extra_fields)

# class CustomUser(AbstractUser):
#     ROLE_CHOICES = [
#         ('buyer', 'Buyer'),
#         ('seller', 'Seller'),
#         ('lawyer', 'Lawyer'),
#         ('admin', 'Admin'),
#     ]
#     phone_number = models.CharField(validators=[validate_phone_number], max_length=14, unique=True)
#     is_phone_verified = models.BooleanField(default=False)
#     role = models.CharField(max_length=10, choices=ROLE_CHOICES)

#     username = None  
#     USERNAME_FIELD = 'phone_number'
#     REQUIRED_FIELDS = ['first_name', 'last_name']

#     objects = CustomUserManager()

#     def __str__(self):
#         return f"{self.phone_number} - {self.role}"

#     def is_buyer(self):
#         return self.role == 'buyer'

#     def is_seller(self):
#         return self.role == 'seller'

#     def is_lawyer(self):
#         return self.role == 'lawyer'

#     def is_admin(self):
#         return self.role == 'admin'

# class RegistrationCode(models.Model):
#     phone_number = models.CharField(max_length=17)
#     code = models.CharField(max_length=6)
#     expires_at = models.DateTimeField(default=timezone.now)

#     class Meta:
#         unique_together = ('phone_number', 'code')

#     def is_expired(self):
#         return timezone.now() > self.expires_at

#     def __str__(self):
#         return f"{self.phone_number} - {self.code}"













# # from datetime import timezone
# from django.utils import timezone

# from django.contrib.auth.models import BaseUserManager
# from django.contrib.auth.models import AbstractUser
# from django.db import models
# # from django.core.validators import RegexValidator
# from django.db import models
# from django.core.exceptions import ValidationError
# from django.utils.translation import gettext_lazy as _

# from django.core.exceptions import ValidationError
# from django.utils.translation import gettext_lazy as _

# class CustomUserManager(BaseUserManager):
#     def create_user(self, phone_number, first_name, last_name, password=None, **extra_fields):
#         if not phone_number:
#             raise ValueError('The Phone Number field must be set')
#         if not first_name or not last_name:
#             raise ValueError('The first name and last name must be set')
        
#         user = self.model(
#             phone_number=phone_number,
#             first_name=first_name,
#             last_name=last_name,
#             **extra_fields
#         )
#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, phone_number, first_name, last_name, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)
#         extra_fields.setdefault('role', 'admin')
        
#         if extra_fields.get('is_staff') is not True:
#             raise ValueError('Superuser must have is_staff=True.')
#         if extra_fields.get('is_superuser') is not True:
#             raise ValueError('Superuser must have is_superuser=True.')

#         return self.create_user(phone_number, first_name, last_name, password, **extra_fields)
    


# def validate_phone_number(value):
#     if not value.startswith('+'):
#         return ValidationError(
#             _('Phone number must start with a "+" sign.')
#         )
#     digits = value[1:]
#     if not digits.isdigit() or not (9 <= len(digits) <= 13):
#         return ValidationError(
#             _('Phone number must contain 9 to 13 digits after the "+" sign.')
            
#         )
# +2541135666
# +17334456901


# class CustomUser(AbstractUser):
#     ROLE_CHOICES = [
#         ('buyer', 'Buyer'),
#         ('seller', 'Seller'),
#         ('lawyer', 'Lawyer'),
#         ('admin', 'Admin'),
#     ]
#     phone_number = models.CharField(validators=[validate_phone_number], max_length=14,unique=True)
#     is_phone_verified = models.BooleanField(default=False)
#     role = models.CharField(max_length=10, choices=ROLE_CHOICES)





#     # def role_changed(self):

#     #     if self.pk:  
#     #         old_role = CustomUser.objects.get(pk=self.pk).role
#     #         return old_role != self.role
#     #     return False

#     username = None  
#     USERNAME_FIELD = 'phone_number'
#     REQUIRED_FIELDS = ['first_name', 'last_name']

#     objects = CustomUserManager()

#     def __str__(self):
#         return f"{self.phone_number} - {self.role}"

#     def is_buyer(self):
#         return self.role == 'buyer'

#     def is_seller(self):
#         return self.role == 'seller'

#     def is_lawyer(self):
#         return self.role == 'lawyer'

#     def is_admin(self):
#         return self.role == 'admin'






# class RegistrationCode(models.Model):
#     phone_number = models.CharField(max_length=17)
#     code = models.CharField(max_length=6)
#     expires_at = models.DateTimeField(default=timezone.now)

#     class Meta:
#         unique_together = ('phone_number', 'code')

#     def is_expired(self):
#         return timezone.now() > self.expires_at

#     def __str__(self):
#         return f"{self.phone_number} - {self.code}"










