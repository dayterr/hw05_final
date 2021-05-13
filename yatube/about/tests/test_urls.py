from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse


class AboutURLTests(TestCase):

    def setUp(self):
        self.urls_names = {
            '/about/author/': 'about:author',
            '/about/tech/': 'about:tech',
        }

    def test_about_pages_url_exists_at_desired_location(self):
        for url in self.urls_names.keys():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_hardcode_url_equals_name(self):
        for url, name in self.urls_names.items():
            with self.subTest(url=url, name=name):
                self.assertEqual(url, reverse(name))
