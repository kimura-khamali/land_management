from django.test import TestCase
from django.utils import timezone
from .models import CustomUser, RegistrationCode
from datetime import timedelta

class CustomUserModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            phone_number='+2544567890',
            first_name='Brenda',
            last_name='Khamali',
            password='khamali123',
            role='buyer'
        )
    
    def test_user_creation(self):
        self.assertEqual(self.user.phone_number, '+1234567890')
        self.assertEqual(self.user.first_name, 'Brenda')
        self.assertEqual(self.user.last_name, 'Khamali')
        self.assertTrue(self.user.check_password('khamali123'))
        self.assertEqual(self.user.role, 'buyer')  

    def test_is_buyer(self):
        """Test the is_buyer method"""
        self.assertTrue(self.user.is_buyer())
        self.user.role = 'seller'
        self.user.save()
        self.assertFalse(self.user.is_buyer())

    def test_create_superuser(self):
        superuser = CustomUser.objects.create_superuser(
            phone_number='+25498765432',
            first_name='Ann',
            last_name='jane',
            password='ann123'
        )
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        self.assertEqual(superuser.role, 'admin')



class RegistrationCodeModelTest(TestCase):
    def setUp(self):
        self.registration_code = RegistrationCode.objects.create(
            phone_number='+1234567890',
            code='123456',
            expires_at=timezone.now() + timedelta(minutes=5)
        )

    def test_registration_code_creation(self):
        self.assertEqual(self.registration_code.phone_number, '+1234567890')
        self.assertEqual(self.registration_code.code, '123456')
        self.assertFalse(self.registration_code.is_expired())

    def test_code_expiry(self):
        self.registration_code.expires_at = timezone.now() - timedelta(minutes=1)
        self.registration_code.save()
        self.assertTrue(self.registration_code.is_expired())
