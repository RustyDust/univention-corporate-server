#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
# -*- coding: utf-8 -*-
## desc: |
##  Test if all expected modules are available for 'root' and 'administrator'
##  users, with different join-states.
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import os.path
import subprocess

from selenium.webdriver.common.by import By

from univention.lib.i18n import Translation
from univention.testing import selenium


_ = Translation('ucs-test-selenium').translate

MASTER = 'master'
BACKUP = 'backup'
SLAVE = 'slave'
MEMBER = 'member'

ADMIN = 'Administrator'
ROOT = 'root'

expected_modules_for_role = {
    MASTER: {
        ADMIN: [
            _('Filesystem quotas'),
            _('Groups'),
            _('Users'),
            _('Computers'),
            _('Nagios'),
            _('Printers'),
            _('DHCP'),
            _('DNS'),
            _('Domain join'),
            _('LDAP directory'),
            _('Mail'),
            _('Networks'),
            _('Policies'),
            _('Shares'),
            _('SAML identity provider'),
            _('Certificate settings'),
            _('Hardware information'),
            _('Language settings'),
            _('Network settings'),
            _('Process overview'),
            _('System services'),
            _('Univention Configuration Registry'),
            _('System diagnostic'),
            _('App Center'),
            _('Package Management'),
            _('Repository Settings'),
            _('Software update'),
        ],
        ROOT: [
            _('Filesystem quotas'),
            _('Domain join'),
            _('Certificate settings'),
            _('Hardware information'),
            _('Language settings'),
            _('Network settings'),
            _('Process overview'),
            _('System services'),
            _('Univention Configuration Registry'),
            _('Software update'),
        ],
    },
    BACKUP: {
        ADMIN: [
            _('Filesystem quotas'),
            _('Groups'),
            _('Users'),
            _('Computers'),
            _('Nagios'),
            _('Printers'),
            _('DHCP'),
            _('DNS'),
            _('Domain join'),
            _('LDAP directory'),
            _('Mail'),
            _('Networks'),
            _('Policies'),
            _('Shares'),
            _('SAML identity provider'),
            _('Hardware information'),
            _('Language settings'),
            _('Network settings'),
            _('Process overview'),
            _('System services'),
            _('Univention Configuration Registry'),
            _('System diagnostic'),
            _('App Center'),
            _('Package Management'),
            _('Repository Settings'),
            _('Software update'),
        ],
        ROOT: [
            _('Filesystem quotas'),
            _('Domain join'),
            _('Hardware information'),
            _('Language settings'),
            _('Network settings'),
            _('Process overview'),
            _('System services'),
            _('Univention Configuration Registry'),
            _('Software update'),
        ],
    },
    SLAVE: {
        ADMIN: [
            _('Filesystem quotas'),
            _('Domain join'),
            _('Hardware information'),
            _('Language settings'),
            _('Network settings'),
            _('Process overview'),
            _('System services'),
            _('Univention Configuration Registry'),
            _('System diagnostic'),
            _('App Center'),
            _('Package Management'),
            _('Repository Settings'),
            _('Software update'),
        ],
        ROOT: [
            _('Filesystem quotas'),
            _('Domain join'),
            _('Hardware information'),
            _('Language settings'),
            _('Network settings'),
            _('Process overview'),
            _('System services'),
            _('Univention Configuration Registry'),
            _('Software update'),
        ],
    },
    MEMBER: {
        ADMIN: [
            _('Filesystem quotas'),
            _('Domain join'),
            _('Hardware information'),
            _('Language settings'),
            _('Network settings'),
            _('Process overview'),
            _('System services'),
            _('Univention Configuration Registry'),
            _('System diagnostic'),
            _('App Center'),
            _('Package Management'),
            _('Repository Settings'),
            _('Software update'),
        ],
        ROOT: [
            _('Filesystem quotas'),
            _('Domain join'),
            _('Hardware information'),
            _('Language settings'),
            _('Network settings'),
            _('Process overview'),
            _('System services'),
            _('Univention Configuration Registry'),
            _('Software update'),
        ],
    },
}


class UmcError(Exception):
    pass


class UMCTester(object):

    def test_umc(self):
        role = self.determine_ucs_role()
        users = self.determine_users_by_join_status()
        self.main_user = users[0]

        for user in users:
            self.selenium.do_login(username=user)
            self.check_if_required_modules_are_visible(role, user)
            self.selenium.end_umc_session()

    def determine_ucs_role(self):
        server_role = subprocess.check_output(['ucr', 'get', 'server/role']).strip()
        if server_role == b'domaincontroller_master':
            return MASTER
        elif server_role == b'domaincontroller_backup':
            return BACKUP
        elif server_role == b'domaincontroller_slave':
            return SLAVE
        elif server_role == b'memberserver':
            return MEMBER
        else:
            raise UmcError('Test is run on invalid server-role %r.' % (server_role,))

    def determine_users_by_join_status(self):
        if os.path.isfile('/var/univention-join/joined'):
            return [ADMIN, ROOT]
        else:
            return [ROOT]

    def check_if_required_modules_are_visible(self, role, user):
        available_modules = [module.lower() for module in self.get_available_modules()]
        requiered_modules = [module.lower() for module in expected_modules_for_role[role][user]]
        missing_modules = set(requiered_modules) - set(available_modules)
        if len(missing_modules) > 0:
            raise UmcError(
                'These modules are missing in the UMC: %r' % (missing_modules,),
            )

    def get_available_modules(self):
        self.selenium.search_module('*')

        xpath = '//*[contains(concat(" ", normalize-space(@class), " "), " umcGalleryName ")]'
        tile_headings = self.selenium.driver.find_elements(By.XPATH, xpath)

        return [tile_heading.text if not tile_heading.get_attribute("title") else tile_heading.get_attribute("title") for tile_heading in tile_headings]


if __name__ == '__main__':
    with selenium.UMCSeleniumTest() as s:
        umc_tester = UMCTester()
        umc_tester.selenium = s

        umc_tester.test_umc()
