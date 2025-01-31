#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
# -*- coding: utf-8 -*-
## desc: Test Dudle installation via the 'Appcenter' module
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import time

from univention.testing import selenium
from univention.testing.selenium.appcenter import AppCenter


class UMCTester(object):

    def test_umc(self):
        self.selenium.do_login()
        self.appcenter.install_app('Admin Diary Backend')
        time.sleep(5)
        self.appcenter.uninstall_app('Admin Diary Backend')


if __name__ == '__main__':
    with selenium.UMCSeleniumTest() as s:
        umc_tester = UMCTester()
        umc_tester.selenium = s
        umc_tester.appcenter = AppCenter(umc_tester.selenium)

        umc_tester.test_umc()
