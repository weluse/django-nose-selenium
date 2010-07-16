====================
django-nose-selenium
====================


Adds selenium testing support to your nose test suite.

To use, run nosetests with the ``--with-selenium`` flag.

------------
Installation
------------

From PyPI::
   
   pip install django-nose-selenium

From Git::

   pip install -e git://github.com/weluse/django-nose-selenium.git#egg=noseselenium

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


Alternatively, django-nose-selenium provides a mixin that has the benefit that
it raises a SkipTest exception if the plugin was not loaded and the selenium
attribute is accessed::


   from noseselenium.cases import SeleniumTestCaseMixin


   class TestSelenium(TestCase, SeleniumTestCaseMixin):

       def test_start(self):
           """Tests the start page."""

           self.selenium.open("/")

Fixtures
--------

The default fixtures of django are run in transactions and not available to a
live testing server, therefore `noseselenium` provides an option to load and
**commit** fixtures to the database automated. Please note that there's no
automatic rollback, so the data will stay in your test database for the rest of
the run if you don't provide a custom teardown strategy.

::

   from noseselenium.cases import SeleniumTestCaseMixin


   class TestUserLogin(TestCase, SeleniumTestCaseMixin):

       selenium_fixtures = ['user_data.json']

       def test_login(self):
           """Tests the login page."""

           sel = self.selenium
           sel.open("/login/")
           sel.type("id_username", "pascal")
           sel.type("id_password", "iwantapony")
           sel.click(//form[@id='myform']/p/button")

To enable selenium fixtures, nosetests must be called with the
additional ``--with-selenium-fixtures`` flag.
