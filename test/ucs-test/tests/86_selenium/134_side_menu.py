#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
# -*- coding: utf-8 -*-
## desc: Test the Side menu
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

from univention.lib.i18n import Translation
from univention.testing import selenium


_ = Translation('ucs-test-selenium').translate


class UMCTester(object):

    def test_umc(self):
        self.selenium.do_login()
        self.selenium.open_side_menu()
        self.selenium.click_side_menu_entry(_('User settings'))
        self.selenium.wait_for_text(_('Change password'))  # check if submenu opened
        self.selenium.click_side_menu_back()
        self.selenium.wait_for_text(_('User settings'))  # check if submenu closed
        self.selenium.close_side_menu()
        self.selenium.open_side_menu()  # if opening does not work here that means closing did not work


if __name__ == '__main__':
    with selenium.UMCSeleniumTest() as s:
        umc_tester = UMCTester()
        umc_tester.selenium = s

        umc_tester.test_umc()
