#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
# -*- coding: utf-8 -*-
## desc: Test the 'System diagnostic' module
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import os
import random
import string
import tempfile

from selenium.common.exceptions import TimeoutException

from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import plugins
from univention.testing import selenium


_ = Translation('ucs-test-selenium').translate


class UmcError(Exception):
    pass


class UMCTester(object):

    PLUGIN_DIR = os.path.dirname(plugins.__file__)

    def init(self):
        self.plugin_path = self.get_plugin_path()
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.plugin_data = {
            'title': '133_system_diagnostics title',
            'description': '133_system_diagnostics description',
            'test_action_label': 'test_action label',
            'temp_file_name': self.temp_file.name,
        }
        self.create_diagnostic_plugin()

    def cleanup(self):
        if os.path.exists(self.plugin_path):
            os.remove(self.plugin_path)
        pyc_file = '%sc' % self.plugin_path
        if os.path.exists(pyc_file):
            os.remove(pyc_file)
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_umc(self):
        try:
            self.init()
            self.selenium.do_login()
            self.selenium.open_module(_('System diagnostic'))
            try:
                self.selenium.wait_for_text(self.plugin_data['title'], timeout=5)
                raise UmcError("Found title '%s' but there should be none" % (self.plugin_data['title']))
            except TimeoutException:
                pass
            print("Writing 'FAIL' into '%s' to cause '%s' to fail" % (self.temp_file.name, self.plugin_path))
            with open(self.temp_file.name, 'w') as f:
                f.write('FAIL')
            self.selenium.click_button('Run system diagnosis')
            self.selenium.wait_until_progress_bar_finishes()
            try:
                self.selenium.wait_for_text(self.plugin_data['title'], timeout=5)
            except TimeoutException:
                raise UmcError("Did not found title '%s' but there should be" % (self.plugin_data['title']))
        finally:
            self.cleanup()

    def create_diagnostic_plugin(self):
        print("write test code into: %s" % (self.plugin_path))
        plugin = '''
#!/usr/bin/python3
# -*- coding: utf-8 -*-

from univention.management.console.modules.diagnostic import Critical

title = '{title}'
description = '{description}'


def run(_umc_instance):
    with open('{temp_file_name}', 'r') as f:
        temp_file_content = f.read().strip()
    if temp_file_content == 'FAIL':
        raise Critical('{description}', buttons=[{{
            'action': 'test_action',
            'label': 'test_action label',
        }}])

def test_action(_umc_instance):
    print('test')


actions = {{
    'test_action': test_action,
}}
'''.format(**self.plugin_data).strip()
        with open(self.plugin_path, 'w') as f:
            f.write(plugin)

    def get_plugin_path(self):
        print('Getting a unique plugin pathname for a test plugin')
        plugin_path = self.get_random_plugin_path()
        while os.path.exists(plugin_path):
            plugin_path = self.get_random_plugin_path()
        print('Unique plugin pathname is: %s' % (plugin_path))
        return plugin_path

    def get_random_plugin_path(self):
        plugin_name = '{}.py'.format(self.get_random_ascii_string(10))
        return os.path.join(self.PLUGIN_DIR, plugin_name)

    def get_random_ascii_string(self, length):
        return ''.join([random.choice(string.ascii_letters) for x in range(length)])


if __name__ == '__main__':
    with selenium.UMCSeleniumTest() as s:
        umc_tester = UMCTester()
        umc_tester.selenium = s

        umc_tester.test_umc()
