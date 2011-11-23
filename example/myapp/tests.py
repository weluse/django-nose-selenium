from django.test import TestCase
from noseselenium.cases import SeleniumTestCaseMixin
from selenium import webdriver


class ExampleWebdriverTestCase(TestCase, SeleniumTestCaseMixin):

    def get_driver(self):
        """Overrides the default driver to set project-specific settings."""

        return webdriver.Chrome()


class View1WebdriverTestCase(ExampleWebdriverTestCase):
    # XXX: This should be automatically used.
    BASE_URL = "http://127.0.0.1:8080"

    def test_view(self):
        self.selenium.get(self.BASE_URL + '/view1')
        self.assertEquals('Hello, World!', self.selenium.title)
