====================
django-nose-selenium
====================


Adds selenium testing support to your nose test suite.

To use, run nosetests with the ``--with-selenium`` flag.


---------------
Django Settings
---------------

The plugin supports the following settings:

   * SELENIUM_HOST, default: `127.0.0.1`
   * SELENIUM_PORT, default: `4444`
   * SELENIUM_BROWSER_COMMAND, default: `chrome`
   * SELENIUM_URL_ROOT, default: `http://127.0.0.1:8000`
   * FORCE_SELENIUM_TESTS, default: `False`. By default, SocketErrors cause the
     tests to be skipped. This options causes the tests to fail when the
     Selenium server is unavailable.

-----
Usage
-----

Define the class variable ``selenium_test = True`` in your nose test class and
run ``nosetests --with-selenium``. You can use ``self.selenium`` to access a
selenium instance with the given options::

   
   class TestSelenium(TestCase):

       selenium_test = True

       def test_start(self):
           """Tests the start page."""

           self.selenium.open("/")
