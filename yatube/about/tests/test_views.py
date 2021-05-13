from django.test import TestCase
from django.urls import reverse


class AboutViewsTests(TestCase):

    def test_about_page_uses_correct_template(self):
        names_templates = {
            'about:author': 'about/author.html',
            'about:tech': 'about/tech.html',
        }
        for name, template in names_templates.items():
            with self.subTest(name=name, template=template):
                response = self.client.get(reverse(name))
                self.assertTemplateUsed(response, template)
