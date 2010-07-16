# -*- coding: utf-8 -*-
"""
noseselenium.plugins
~~~~~~~~~~~~~~~~~~~~

Provides the nose plugins.
Heavily inspired by `django-sane-testing`_.

_django-sane-testing: http://github.com/Almad/django-sane-testing/

:copyright: 2010, Pascal Hartig <phartig@weluse.de>
:license: BSD, see LICENSE for more details.
"""

import socket
import nose
from nose.plugins import Plugin
from nose.plugins.skip import SkipTest
from noseselenium.thirdparty.selenium import selenium
from unittest import TestCase


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
