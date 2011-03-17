# -*- coding: utf-8 -*-
"""
noseselenium.plugins
~~~~~~~~~~~~~~~~~~~~

Provides the nose plugins.
Heavily inspired by `django-sane-testing`_.

_django-sane-testing: http://github.com/Almad/django-sane-testing/

:copyright: 2010-2011, Pascal Hartig <phartig@weluse.de>
:license: BSD, see LICENSE for more details.
"""

import socket
import nose
import time
import threading
from nose.plugins import Plugin
from nose.plugins.skip import SkipTest
from noseselenium.thirdparty.selenium import selenium
from unittest import TestCase
# Liveserver imports
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer
from django.core.handlers.wsgi import WSGIHandler
from django.core.servers.basehttp import WSGIRequestHandler, \
        AdminMediaHandler, WSGIServerException
from django.db.backends.creation import TEST_DATABASE_PREFIX
from django.contrib.staticfiles.handlers import StaticFilesHandler


def _get_test_db_name(connection):
    """Tries to build the test database name like django does."""

    if connection.settings_dict['TEST_NAME']:
        return connection.settings_dict['TEST_NAME']
    else:
        old_name = connection.settings_dict['NAME']
        if old_name.startswith(TEST_DATABASE_PREFIX):
            return old_name
        else:
            return TEST_DATABASE_PREFIX + \
                    old_name


def _set_autocommit(connection):
        """Make sure a connection is in autocommit mode."""
        if hasattr(connection.connection, "autocommit"):
            if callable(connection.connection.autocommit):
                connection.connection.autocommit(True)
            else:
                connection.connection.autocommit = True
        elif hasattr(connection.connection, "set_isolation_level"):
            connection.connection.set_isolation_level(0)


def _setup_test_db():
    """Activates a test dbs without recreating them."""

    from django.db import connections

    for alias in connections:
        connection = connections[alias]
        connection.close()

        test_db_name = _get_test_db_name(connection)
        connection.settings_dict['NAME'] = test_db_name

        # SUPPORTS_TRANSACTIONS is not needed in newer versions of djangoo
        if not hasattr(connection.features, 'supports_transactions'):
            can_rollback = connection.creation._rollback_works()
            connection.settings_dict['SUPPORTS_TRANSACTIONS'] = can_rollback

        # Trigger side effects.
        connection.cursor()
        _set_autocommit(connection)


def get_test_case_class(nose_test):
    """
    Extracts the class from the nose tests that depends on whether it's a
    method test case or a function test case.
    """
    if isinstance(nose_test.test, nose.case.MethodTestCase):
        return nose_test.test.test.im_class
    else:
        return nose_test.test.__class__


class SeleniumPlugin(Plugin):
    """
    Adds a selenium attribute to the nose test case and reads the parameters
    from the django config.
    Only works with class based tests, so far.
    """

    activation_parameter = "--with-selenium"
    name = "selenium"
    score = 80

    def startTest(self, test):
        """
        When preparing the test, inject a selenium instance.
        """

        test_case = get_test_case_class(test)
        if getattr(test_case, "selenium_test", False):
            self._inject_selenium(test)

    def stopTest(self, test):
        """
        Destroys the selenium connection.
        """

        test_case = get_test_case_class(test)
        if getattr(test_case, 'selenium_started', False):
            if isinstance(test.test, nose.case.MethodTestCase):
                self = test.test.test.im_self
            elif isinstance(test.test, TestCase):
                self = test.test._exc_info.im_self

            self.selenium.stop()
            del self.selenium

    def _inject_selenium(self, test):
        """
        Injects a selenium instance into the method.
        """
        from django.conf import settings

        test_case = get_test_case_class(test)
        test_case.selenium_plugin_started = True

        # Provide some reasonable default values
        sel = selenium(
            getattr(settings, "SELENIUM_HOST", "localhost"),
            int(getattr(settings, "SELENIUM_PORT", 4444)),
            getattr(settings, "SELENIUM_BROWSER_COMMAND", "*chrome"),
            getattr(settings, "SELENIUM_URL_ROOT", "http://127.0.0.1:8000/"))

        try:
            sel.start()
        except socket.error:
            if getattr(settings, "FORCE_SELENIUM_TESTS", False):
                raise
            else:
                raise SkipTest("Selenium server not available.")
        else:
            test_case.selenium_started = True
            # Only works on method test cases, because we obviously need
            # self.
            if isinstance(test.test, nose.case.MethodTestCase):
                test.test.test.im_self.selenium = sel
            elif isinstance(test.test, TestCase):
                test.test._exc_info.im_self.selenium = sel
            else:
                raise SkipTest("Test skipped because it's not a method.")


class SeleniumFixturesPlugin(Plugin):
    """
    Loads fixtures defined in the attribute `selenium_fixtures`. It does,
    however, not take care of removing them after the test or even the whole
    test case is run.
    Django fixtures are usually run in transactions so a test server accessing
    the test database won't be able access the data.
    """

    activation_parameter = "--with-selenium-fixtures"
    name = "selenium-fixtures"
    score = 80

    def startTest(self, test):
        """
        When preparing the database, check for the `selenium_fixtures`
        attribute and load those.
        """

        from django.test.testcases import call_command

        test_case = get_test_case_class(test)
        fixtures = getattr(test_case, "selenium_fixtures", [])

        if fixtures:
            call_command('loaddata', *fixtures, **{
                'verbosity': 1,
                # Necessary to let the test server access them.
                'commit': True
            })


class StoppableWSGIServer(ThreadingMixIn, HTTPServer):
    """WSGIServer with short timeout, so that server thread can stop this
    server.

    This implementation is again from django-sane-testing, while the original
    code is taken from django ticket #2879 which proposes a live server in the
    django core.
    """

    application = None

    def __init__(self, server_address, RequestHandlerClass=None):
        HTTPServer.__init__(self, server_address, RequestHandlerClass)

    def server_bind(self):
        """Bind server to socket. Overrided to store server name and
        set timeout.
        """

        try:
            HTTPServer.server_bind(self)
        except Exception as e:
            raise WSGIServerException(e)

        self.setup_environ()
        self.socket.settimeout(1)

    def get_request(self):
        """Checks for timeout when getting request."""
        sock, address = self.socket.accept()
        return (sock, address)

    def setup_environ(self):
        """Set up a basic environment."""

        self.base_environ = {
            'SERVER_NAME': self.server_name,
            'GATEWAY_INTERFACE': 'CGI/1.1',
            'SERVER_PORT': str(self.server_port),
            'REMOTE_HOST': '',
            'CONTENT_LENGTH': '',
            'SCRIPT_NAME': '',
        }

    def get_app(self):
        return self.application

    def set_app(self,application):
        self.application = application


class AbstractLiveServerPlugin(Plugin):
    """Base class for live servers."""

    score = 70

    def __init__(self):
        Plugin.__init__(self)
        self.server_started = False
        self.server_thread = None

    def start_server(self):
        raise NotImplementedError()

    def stop_server(self):
        raise NotImplementedError()

    def startTest(self, test):
        """Starts the live server."""

        from django.conf import settings

        test_case = get_test_case_class(test)

        if not self.server_started and \
           getattr(test_case, "start_live_server", False):

            _setup_test_db()

            # Raises an exception if not.
            settings.TEST_MODE = True

            self.start_server(
                address=getattr(settings, 'LIVE_SERVER_ADDRESS',
                                '0.0.0.0'),
                port=getattr(settings, 'LIVE_SERVER_PORT',
                             8080),
                serve_static=getattr(settings, 'LIVE_SERVER_STATIC', True)
            )

            self.server_started = True
            setattr(test_case, 'http_plugin_started', True)

    def stopTest(self, test):
        """Stops the live server if necessary."""

        test_case = get_test_case_class(test)
        if self.server_started and \
           getattr(test_case, 'http_plugin_started', False):

            self.stop_server()
            self.server_started = False


class TestServerThread(threading.Thread):
    """Thread for running a http server while tests are running."""

    def __init__(self, address, port, serve_static=True):
        self.address = address
        self.port = port
        self.serve_static = serve_static
        self._stopevent = threading.Event()
        self.started = threading.Event()
        self.error = None
        super(TestServerThread, self).__init__()

    def run(self):
        """Sets up test server and loops over handling http requests."""
        try:
            handler = AdminMediaHandler(WSGIHandler())
            if self.serve_static:
                handler = StaticFilesHandler(handler)

            server_address = (self.address, self.port)
            httpd = StoppableWSGIServer(server_address, WSGIRequestHandler)
            httpd.application = handler
            self.started.set()
        except WSGIServerException as err:
            self.error = err
            self.started.set()
            return

        # Loop until we get a stop event.
        while not self._stopevent.isSet():
            httpd.handle_request()

    def join(self, timeout=None):
        """Stop the thread and wait for it to finish."""
        self._stopevent.set()
        threading.Thread.join(self, timeout)


class DjangoLiveServerPlugin(AbstractLiveServerPlugin):
    """
    Patch Django on fly and start live HTTP server, if TestCase is inherited
    from HttpTestCase or start_live_server attribute is set to True.

    Taken from Michael Rogers implementation from `getwindmill.com
    <http://trac.getwindmill.com/browser/trunk/windmill/authoring/
    djangotest.py>`_.
    """
    name = 'djangoliveserver'
    activation_parameter = '--with-djangoliveserver'

    def start_server(self, address='0.0.0.0', port=8000, serve_static=True):
        self.server_thread = TestServerThread(address, port, serve_static)
        self.server_thread.start()
        self.server_thread.started.wait()
        if self.server_thread.error:
            raise self.server_thread.error

    def stop_server(self):
        self.server_thread.join()


class CherryPyLiveServerPlugin(AbstractLiveServerPlugin):
    """Live server plugin using cherrypy instead of the django server,
    that got its issues. Original code by Mikeal Rogers, released under
    Apache License.
    """

    name = 'cherrypyliveserver'
    activation_parameter = '--with-cherrypyliveserver'

    def start_server(self, address='0.0.0.0', port=8000, serve_static=True):
        from cherrypy.wsgiserver import CherryPyWSGIServer
        from threading import Thread

        _application = AdminMediaHandler(WSGIHandler())
        if serve_static:
            _application = StaticFilesHandler(_application)

        def application(environ, start_response):
            environ['PATH_INFO'] = environ['SCRIPT_NAME'] + \
                    environ['PATH_INFO']

            return _application(environ, start_response)

        self.httpd = CherryPyWSGIServer((address, port), application,
                                        server_name='django-test-http')
        self.httpd_thread = Thread(target=self.httpd.start)
        self.httpd_thread.start()
        # FIXME: This could be avoided by passing self to thread class starting
        # django and waiting for Event lock
        time.sleep(.5)

    def stop_server(self):
        self.httpd.stop()
