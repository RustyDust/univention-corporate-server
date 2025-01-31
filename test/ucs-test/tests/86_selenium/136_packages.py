#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
# -*- coding: utf-8 -*-
## desc: Test the package management module
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import apt
from selenium.webdriver.common.by import By

from univention.lib.i18n import Translation
from univention.testing import selenium, utils
from univention.testing.selenium.utils import expand_path


_ = Translation('ucs-test-selenium').translate


class UmcError(Exception):
    pass


class UMCTester(object):

    def get_small_package_name(self):
        print("Trying to find small, uninstalled package with no dependencies and recommends...")
        cache = apt.cache.Cache()
        cache.update()
        cache.open()
        small_package = None
        for package in cache:
            if not package.candidate:
                print('Package from cache has no candidate, skipping...: %s' % package)
                continue
            if not package.is_installed \
                    and package.candidate.installed_size < 0.5 * 1000 * 1000 \
                    and not package.candidate.recommends \
                    and not package.candidate.dependencies:
                small_package = package
                break
        if not small_package:
            utils.fail('Did not find small, installed package with no dependencies and recommends')
        print("Found small, uninstalled package: %s" % small_package)
        return small_package.name

    def test_umc(self):
        self.selenium.do_login()
        self.selenium.open_module('Package Management')

        package_name = self.get_small_package_name()

        for action in ['install', 'uninstall']:
            print("Current action: %s" % (action,))
            button_for_action = _('Install') if action == 'install' else _('Uninstall')
            expected_status = _('installed') if action == 'install' else _('not installed')

            self.selenium.enter_input('pattern', package_name)
            self.selenium.submit_input('pattern')
            self.selenium.wait_until_all_standby_animations_disappeared()
            self.selenium.click_checkbox_of_grid_entry(package_name)

            self.selenium.click_button(button_for_action)
            self.selenium.wait_for_text('Confirmation')
            print("Clicking the dialog button %r" % (button_for_action,))
            self.selenium.click_element(expand_path('//*[@containsClass="dijitDialog"]//*[@containsClass="dijitButtonText"][text() = "%s"]' % button_for_action))
            self.selenium.wait_until_all_dialogues_closed()
            self.selenium.wait_until_progress_bar_finishes()
            self.selenium.wait_until_standby_animation_appears_and_disappears()

            installation_status_path = expand_path('//*[text() = "%s"]/ancestor-or-self::*[@containsClass="field-package"]/following-sibling::*[@containsClass="field-status"]' % package_name)
            installation_status = self.selenium.driver.find_element(By.XPATH, installation_status_path).text
            if installation_status != expected_status:
                raise UmcError('The installation status of package "%s" should be "%s" but is "%s"' % (package_name, expected_status, installation_status))


if __name__ == '__main__':
    with selenium.UMCSeleniumTest() as s:
        umc_tester = UMCTester()
        umc_tester.selenium = s

        umc_tester.test_umc()
