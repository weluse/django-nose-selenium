# -*- coding: utf-8 -*-
"""
noseselenium.cases
~~~~~~~~~~~~~~~~~~

Testcases for selenium.

:copyright: 2010, Pascal Hartig <phartig@weluse.de>
:license: BSD, see LICENSE for more details.
"""

from nose.plugins.skip import SkipTest
from selenium import webdriver


class SeleniumSkipper(object):
    """
    A class that raises a SkipTest exception when an attribute is
    accessed.
    """

    def __getattr__(self, name):
        raise SkipTest("SeleniumPlugin not enabled.")


class SeleniumTestCaseMixin(object):
    """
    Apply this to your TestCase base class to get Webdriver functionality in
    your tests. If the selenium attribute is accessed without having
    :class:`SeleniumPlugin` enabled, the test is skipped.
    """

    selenium = SeleniumSkipper()
    selenium_test = True
    start_live_server = True

    def get_driver(self):
        """Builds the driver instance and returns it. Override this to use
        custom options.
        """

        return webdriver.Firefox()
