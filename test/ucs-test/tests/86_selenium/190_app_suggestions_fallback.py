#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
# -*- coding: utf-8 -*-
## desc: |
##  Test fallback for invalid suggestions
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import shutil

from univention.admin import localization
from univention.appcenter.app_cache import AppCenterCache, default_server
from univention.testing import selenium
from univention.testing.selenium.appcenter import AppCenter


translator = localization.translation('ucs-test-selenium')
_ = translator.translate


class UMCTester(object):
    def setup(self):
        cache = AppCenterCache.build(server=default_server())
        self.json_file = cache.get_cache_file('.suggestions.json')
        self.json_file_bak = cache.get_cache_file('.suggestions.bak.json')
        print('moving %s to %s' % (self.json_file, self.json_file_bak))
        shutil.move(self.json_file, self.json_file_bak)

    def cleanup(self):
        try:
            print('restoring %s' % self.json_file)
            shutil.move(self.json_file_bak, self.json_file)
        except (OSError, IOError):
            pass

    def test_umc(self):
        self.selenium.do_login()
        self.write_invalid_json()
        print('checking fallback for invalid json')
        self.check()
        self.write_missing_key()
        print('checking fallback for missing key')
        self.check()

    def check(self):
        self.appcenter.open()
        self.selenium.wait_for_text('Available')
        log = self.selenium.driver.get_log('browser')
        assert any('Could not load appcenter/suggestions' in e['message'] for e in log)

    def write_invalid_json(self):
        with open(self.json_file, 'w') as fd:
            fd.write('asd')

    def write_missing_key(self):
        with open(self.json_file, 'w') as fd:
            fd.write('''
{
    "xxx": {}
}
''')


if __name__ == '__main__':
    with selenium.UMCSeleniumTest() as s:
        umc_tester = UMCTester()
        umc_tester.selenium = s
        umc_tester.appcenter = AppCenter(umc_tester.selenium)

        try:
            umc_tester.setup()
            umc_tester.test_umc()
        finally:
            umc_tester.cleanup()
