from django.test import TestCase
from noseselenium.cases import SeleniumTestCaseMixin
from selenium import webdriver


class ExampleWebdriverTestCase(TestCase, SeleniumTestCaseMixin):

    def get_driver(self):
        """Overrides the default driver to set project-specific settings."""

        return webdriver.Chrome()


class View1WebdriverTestCase(ExampleWebdriverTestCase):
    def test_view(self):
        self.selenium.get('http://localhost:5888/view1')
        self.assertEquals('Hello, World!', self.selenium.title)
