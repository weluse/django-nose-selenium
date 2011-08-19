from django.test import TestCase
from noseselenium.cases import SeleniumTestCaseMixin
from selenium import webdriver


class ExampleWebdriverTestCase(TestCase, SeleniumTestCaseMixin):

    def get_driver(self):
        """Overrides the default driver to set project-specific settings."""

        return webdriver.Chrome()


class View1WebdriverTestCase(ExampleWebdriverTestCase):
    def test_view(self):
        driver = self.selenium.driver
        self.selenium.open('/view1')
        self.assertEquals('Hello, World!', driver.title)
