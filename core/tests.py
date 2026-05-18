from django.test import TestCase


class CoreSmokeTests(TestCase):
    def test_admin_url_redirects_when_anonymous(self):
        response = self.client.get("/admin/")
        self.assertIn(response.status_code, (301, 302))
