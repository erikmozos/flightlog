from django.contrib.auth.models import User
from django.test import TestCase


class UserAuthTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username="piloto1",
            password="contraseña-segura",
        )
        self.assertEqual(user.username, "piloto1")
        self.assertTrue(user.check_password("contraseña-segura"))
