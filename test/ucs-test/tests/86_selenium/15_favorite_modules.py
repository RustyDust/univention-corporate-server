#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
# -*- coding: utf-8 -*-
## desc: |
##  Test favorite modules
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import re
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

import univention.testing.ucr as ucr_test
from univention.lib.i18n import Translation
from univention.testing import selenium, utils
from univention.testing.selenium.utils import expand_path


_ = Translation('ucs-test-selenium').translate


class FavoriteModulesError(Exception):
    pass


# takes an xpath and expands the
# @containsClass="className"
# attribute to
# contains(concat(" ", normalize-space(@class), " "), " className ")
def cc(xpath):
    pattern = r'(?<=\[)@containsClass=([\"\'])(.*?)\1(?=\])'
    replacement = r'contains(concat(\1 \1, normalize-space(@class), \1 \1), \1 \2 \1)'
    return re.sub(pattern, replacement, xpath)


class UMCTester(object):

    def test_umc(self):
        self.setup()
        self.test_default_favorites()
        self.test_removing_default_favorites()
        self.test_add_to_favorites()
        self.cleanup()

    def setup(self):
        self.selenium.do_login()
        # make sure the favorites category is selected
        self.selenium.click_button(_('Favorites'))

    def test_default_favorites(self):
        # check if the default favorite modules are in the favorites category
        for favorite in self._get_default_favorites():
            try:
                self.selenium.driver.find_element(By.CSS_SELECTOR, '.umcGalleryWrapperItem[moduleid^="%s"]' % (favorite,))
            except NoSuchElementException:
                raise FavoriteModulesError('A default favorite module is missing: %s' % (favorite,))

    def test_removing_default_favorites(self):
        # remove all modules from the favorites category via context menu button (left click)
        module_names = self.selenium.get_gallery_items()
        for module_name in module_names:
            self.selenium.click_tile_menu_icon(module_name)

            self.selenium.click_text(_('Remove from favorites'))
            if not self.selenium.elements_invisible(cc('//div[@containsClass="umcGalleryName"][text() = "%s"]') % (module_name,)):
                raise FavoriteModulesError('Removing module from favorites failed')

        # check if favorites category disappeared after last module is removed from favorites
        time.sleep(1)  # wait for css transition
        if not self.selenium.elements_invisible('//span[@containsClass="umcCategory-_favorites_"]'):
            raise FavoriteModulesError('Favorites category did not disappear after removing all favorite modules')

    def test_add_to_favorites(self):
        # add a module to favorites via right click from users category
        self.selenium.click_button(_('Users'))
        module_name = self.selenium.driver.find_element(By.CSS_SELECTOR, '.umcGalleryName').text
        self.selenium.click_element(
            expand_path('//*[@containsClass="umcGalleryName"][text() = "%s"]' % (module_name,)),
            right_click=True,
        )
        self.selenium.click_text(_('Add to favorites'))

        # check if the flag icon appeared
        if not len(self.selenium.driver.find_elements(By.XPATH, cc('//div[@containsClass="umcGalleryName"][text() = "%s"]/../div[@containsClass="umcFavoriteIconDefault"]') % (module_name,))):
            raise FavoriteModulesError('Adding module to favorites did not update immediately')

        # check if the favorites category reappeared
        time.sleep(1)  # wait for css transition
        if self.selenium.elements_invisible(cc('//span[@containsClass="umcCategory-_favorites_"]')):
            raise FavoriteModulesError('Favorites category did not appear after adding module to favorites')

        # select favorites category and check if it contains the module added to favorites
        self.selenium.click_button(_('Favorites'))
        if self.selenium.elements_invisible(cc('//div[@containsClass="umcGalleryName"][text() = "%s"]') % (module_name,)):
            raise FavoriteModulesError('The favorites catefory did not contain the added module')

    def cleanup(self):
        # remove added module from favorites
        module_name = self.selenium.driver.find_element(By.CSS_SELECTOR, '.umcGalleryName').text
        self.selenium.click_tile_menu_icon(module_name)
        self.selenium.click_text(_('Remove from favorites'))

        # restore the default favorites
        self.selenium.search_module('*')
        for favorite in self._get_default_favorites():
            module_name = self.selenium.driver.find_element(By.CSS_SELECTOR, '.umcGalleryWrapperItem[moduleid^="%s"] .umcGalleryName' % (favorite,)).text
            self.selenium.click_tile_menu_icon(module_name)
            self.selenium.click_text('Add to favorites')

    def _get_default_favorites(self):
        default_favorites_string = ucr.get('umc/web/favorites/default')
        if not utils.package_installed('univention-management-console-module-welcome'):
            default_favorites_string = re.sub(r'welcome(,|$)', '', default_favorites_string).rstrip(',')
        if not utils.package_installed('univention-management-console-module-udm'):
            default_favorites_string = re.sub(r'udm.*?(,|$)', '', default_favorites_string).rstrip(',')
        return default_favorites_string.split(',')


if __name__ == '__main__':
    with ucr_test.UCSTestConfigRegistry() as ucr, selenium.UMCSeleniumTest() as s:
        umc_tester = UMCTester()
        umc_tester.ucr = ucr
        umc_tester.selenium = s

        umc_tester.test_umc()
