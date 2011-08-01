====================
django-nose-selenium
====================

Adds selenium testing support to your nose test suite.

To use, run nosetests with the ``--with-selenium`` flag.

-----------------
Why use Selenium?
-----------------

Selenium is a portable testing framework for web applications. It allows you to
write tests that run in the browser to test your user interface and javascript
code that is not available through the usual testing channels. See the examples
below to get a clearer impression of what selenium tests can provide.

django-nose-selenium allows you to write and run selenium tests the same way as
usual django unit tests.

------------
Requirements
------------

The plugin expects that you have configured the django-nose_ app. In a nutshell,
this is done by running ``pip install django-nose``, adding ``django_nose`` to
``INSTALLED_APPS`` and setting ``TEST_RUNNER`` to
``django_nose.NoseTestSuiteRunner`` in the settings.py.

.. _django-nose: https://github.com/jbalogh/django-nose

------------
Installation
------------

From PyPI::

   pip install django-nose-selenium

`In-development version
<https://github.com/weluse/django-nose-selenium/tarball/master#egg=django-nose-selenium-dev>`_
via Pip::

   pip install django-nose-selenium==dev

Directly from Git::

   pip install -e
   git://github.com/weluse/django-nose-selenium.git#egg=django-nose-selenium

---------------
Django Settings
---------------

.. _base_settings:

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

Define the class variable ``selenium_test = True`` in your nose test class.
You can use ``self.selenium`` to access a selenium instance with the given
options::


   class TestSelenium(TestCase):

       selenium_test = True

       def test_start(self):
           """Tests the start page."""

           self.selenium.open("/")

To run this test, you have to pass the option ``--with-selenium`` to the Django
management command test::

   python manage.py test --with-selenium

Alternatively, django-nose-selenium provides a mixin that has the benefit of
raising a SkipTest exception if the plugin was not loaded and the selenium
attribute is accessed::


   from noseselenium.cases import SeleniumTestCaseMixin


   class TestSelenium(TestCase, SeleniumTestCaseMixin):

       def test_start(self):
           """Tests the start page."""

           self.selenium.open("/")

Fixtures
--------

The default fixtures of django are run in transactions and not available to a
live testing server, therefore `noseselenium` provides an option to load **and
commit** fixtures to the database automatically. Please note that there's no
automatic rollback, so the data will stay in your test database for the rest of
the run if you don't provide a custom teardown strategy.

::

   from noseselenium.cases import SeleniumTestCaseMixin


   class TestUserLogin(TestCase, SeleniumTestCaseMixin):

       selenium_fixtures = ['user_data.json']

       def tearDown(self):
           # Remove data from user_data.json

       def test_login(self):
           """Tests the login page."""

           sel = self.selenium
           sel.open("/login/")
           sel.type("id_username", "pascal")
           sel.type("id_password", "iwantapony")
           sel.click("//form[@id='myform']/p/button")
           sel.wait_for_page_to_load(5000)
           self.failUnless(self.is_text_present("Hello, Pascal!"))

To enable selenium fixtures, nosetests must be called with the
additional ``--with-selenium-fixtures`` flag.


Liveserver
----------

`noseselenium` provides expiremental support for running a live server that
Selenium can connect to. Currently, there's a threaded server that reuses
django's development webserver and a cherrypy implementation. It's recommended
you use the cherrypy one as the django devserver is certainly not designed to
run in a multi-threaded environment.

The liveserver plugin introduces two new configuration options:

   * LIVE_SERVER_ADDRESS, defaults to `0.0.0.0`
   * LIVE_SERVER_PORT, defaults to `8080`
   * LIVE_SERVER_STATIC, boolean that defaults to True. If enabled, the live
     server enables serving of static files via the
     ``django.contrib.staticfiles`` app.

These should match your `Selenium Settings`__.

__ base_settings_

To start the liveserver, nosetest is called with either the
``--with-djangoliveserver`` or preferably the ``--with-cherrypyliveserver``
flag.
