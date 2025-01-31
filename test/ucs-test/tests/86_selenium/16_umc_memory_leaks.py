#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
# -*- coding: utf-8 -*-
## desc: Test memory leaks in UMC javascript frontend
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
##  - umc-producttest
##  - producttest
## join: true
## exposure: dangerous

import json
import pprint

from selenium.webdriver.common.by import By

from univention.lib.i18n import Translation
from univention.testing import selenium, utils
from univention.testing.selenium.appcenter import AppCenter


_ = Translation('ucs-test-selenium').translate


class UMCTester(object):

    def test_umc(self):
        pp = pprint.PrettyPrinter(indent=4)
        self.selenium.do_login()

        s = self.gather_dijit_registy_map()
        print("Initial dijit registry map")
        pp.pprint(json.loads(s))

        for module in self.get_available_modules():
            if module == 'App Center':
                self.appcenter.open(do_reload=False)
            else:
                self.selenium.open_module(module, do_reload=False)
            self.selenium.click_button('Close')

        m = self.gather_dijit_registy_map()
        print("Dijit registry map after opening and closing all modules")
        pp.pprint(json.loads(m))

        d = self.diff_dijit_registry_map(m, s)
        print("Difference between last and initial dijit registry map")
        pp.pprint(json.loads(d))

        for k, v in json.loads(d).items():
            if v != 0:
                utils.fail("There were extra widgets in the registry")

    def get_available_modules(self):
        self.selenium.search_module('*')
        tile_headings = self.selenium.driver.find_elements(By.CLASS_NAME, 'umcGalleryName')
        return [tile_heading.text for tile_heading in tile_headings]

    def gather_dijit_registy_map(self):
        return self.selenium.driver.execute_script('''
            var m = umc.tools.dijitRegistryToMap();
            return JSON.stringify(m);
        ''')

    def diff_dijit_registry_map(self, m, s):
        return self.selenium.driver.execute_script('''
            var m = JSON.parse(arguments[0])
            var s = JSON.parse(arguments[1])
            var d = umc.tools.dijitRegistryMapDifference(m, s)
            return JSON.stringify(d)
        ''', m, s)


if __name__ == '__main__':
    with selenium.UMCSeleniumTest() as s:
        umc_tester = UMCTester()
        umc_tester.selenium = s
        umc_tester.appcenter = AppCenter(umc_tester.selenium)

        umc_tester.test_umc()
