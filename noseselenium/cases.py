# -*- coding: utf-8 -*-
"""
noseselenium.cases
~~~~~~~~~~~~~~~~~~

Testcases for selenium.

:copyright: 2010, Pascal Hartig <phartig@weluse.de>
:license: BSD, see LICENSE for more details.
"""

from nose.plugins.skip import SkipTest


class SeleniumSkipper(object):
    """
    A class that raises a SkipTest exception when an attribute is
    accessed.
    """

    def __getattr__(self, name):
        raise SkipTest("SeleniumPlugin not enabled.")


class SeleniumTestCaseMixin(object):
    """
    Provides a selenium attribute that raises :class:`SkipTest`
    when not overwritten by :class:`SeleniumPlugin`.
    """

    # To be replaced by the plugin.
    selenium = SeleniumSkipper()
    # Triggers the plugin if enabled.
    selenium_test = True
    start_live_server = True
