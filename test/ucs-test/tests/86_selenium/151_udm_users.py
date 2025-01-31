#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
# -*- coding: utf-8 -*-
## desc: Various test for UDM users/user
## packages:
##  - univention-management-console-module-udm
## roles-not:
##  - memberserver
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import univention.testing.selenium.udm as selenium_udm
import univention.testing.strings as uts
import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test
from univention.lib.i18n import Translation
from univention.testing import selenium
from univention.testing.utils import get_ldap_connection


_ = Translation('ucs-test-selenium').translate


class UmcUdmError(Exception):
    pass


class UMCTester(object):

    def test_umc(self):
        self.users = selenium_udm.Users(self.selenium)
        userdn = self.udm.create_user()[0]
        lo = get_ldap_connection()
        user_object = lo.get(userdn)
        user = {}
        user['username'] = user_object['uid'][0].decode('utf-8')
        user['lastname'] = user_object['sn'][0].decode('utf-8')

        self.selenium.do_login()
        self.selenium.open_module(self.users.name)
        self.users.wait_for_main_grid_load()

        self.move_user_into_containers_and_out_again(user)
        self.test_user_templates()

    def move_user_into_containers_and_out_again(self, user):
        print('*** move user into different container')
        position = self.ucr.get('ldap/base')
        cn_name = uts.random_string()
        self.udm.create_object('container/cn', position=position, name=cn_name)
        ou_name = uts.random_string()
        self.udm.create_object('container/ou', position=position, name=ou_name)

        self.move_user(user, cn_name)
        self.move_user(user, ou_name)
        self.move_user(user, 'users')

    def test_user_templates(self):
        print('*** testing user templates')
        self.test_description_template()
        self.test_group_template()

    def test_description_template(self):
        description_template = uts.random_string()
        self.udm.create_object(
            'settings/usertemplate',
            position='cn=templates,cn=univention,%s' % (self.ucr.get('ldap/base'),),
            name=description_template,
            # Using description instead of mailPrimaryAddress here, because
            # mailPrimaryAddress always gets lower-cased.
            description='<firstname:lower,umlauts>.<lastname>[0:2]@test.com',
        )

        # The user-template would not be available when adding a user without
        # this, sometimes.
        self.selenium.open_module(self.users.name)
        self.users.wait_for_main_grid_load()

        user_description_template = self.users.add(
            template=description_template, firstname=u'Bärbel', lastname='Edison',
        )

        self.users.open_details(user_description_template)
        expected_description = 'baerbel.Ed@test.com'
        if self.users.get_description() != expected_description:
            raise UmcUdmError(
                'Setting the description via a usertemplate did not work. '
                'The generated description was %r instead of %r .'
                % (self.users.get_description(), expected_description),
            )
        self.users.close_details()

        self.users.delete(user_description_template)

    def test_group_template(self):
        secondary_group_template = uts.random_string()
        self.udm.create_object(
            'settings/usertemplate',
            position='cn=templates,cn=univention,%s' % (self.ucr.get('ldap/base'),),
            name=secondary_group_template,
            groups='cn=Domain Admins,cn=groups,%s' % (self.ucr.get('ldap/base'),),
        )

        # The user-template would not be available when adding a user without
        # this, sometimes.
        self.selenium.open_module(self.users.name)
        self.users.wait_for_main_grid_load()

        user_group_template = self.users.add(
            template=secondary_group_template, firstname='Thomas', lastname='Edison',
        )

        self.users.open_details(user_group_template)
        self.selenium.click_tab(_('Groups'))
        self.selenium.wait_for_text(_('Domain Admins'))
        self.users.close_details()

        self.users.delete(user_group_template)

    # container_name has to be a direct child of the LDAP-base.
    def move_user(self, user, container_name):
        print('*** moving user %s into %s' % (user['username'], container_name))
        self.selenium.click_checkbox_of_grid_entry(self.users._get_grid_value(user))
        self.selenium.click_text(_('more'))
        self.selenium.click_text(_('Move to...'))
        self.selenium.click_tree_entry(container_name, scroll_into_view=True)
        self.selenium.click_button(_('Move user'))
        self.users.wait_for_main_grid_load()


if __name__ == '__main__':
    with ucr_test.UCSTestConfigRegistry() as ucr, udm_test.UCSTestUDM() as udm, selenium.UMCSeleniumTest() as s:
        umc_tester = UMCTester()
        umc_tester.ucr = ucr
        umc_tester.udm = udm
        umc_tester.selenium = s

        umc_tester.test_umc()
