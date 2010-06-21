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

import os
import socket
import nose
from nose.plugins import Plugin
from nose.plugins.skip import SkipTest
from noseselenium.thirdparty.selenium import selenium


def get_test_case_class(nose_test):
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

        from django.conf import settings

        if getattr(test_case, "selenium_test", False):
            self._inject_selenium(test)

    def stopTest(self, test):
        """
        Destroys the selenium connection.
        """

        test_case = get_test_case_class(test)
        if getattr(test_case, 'selenium_started', False):
            self = test.test.test.im_self
            self.selenium.stop()
            del self.selenium

    def _inject_selenium(self, test):
        """
        Injects the selenium instance into the mehtod.
        """

        test_case = get_test_case_class(test)
        test_case.selenium_plugin_started = True

        sel = selenium(
            getattr(settings, "SELENIUM_HOST", "localhost").
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
            # `self`.
            if isinstance(test.test, nose.case.MethodTestCase):
                test.test.test.im_self.selenium = sel
            else:
                raise SkipTest("Test skipped because it's not a method.")
