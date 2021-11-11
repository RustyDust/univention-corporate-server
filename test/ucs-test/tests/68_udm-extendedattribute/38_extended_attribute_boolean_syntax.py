#!/usr/share/ucs-test/runner pytest-3
## desc: settings/extended_attribute with boolean syntax
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools
## versions:
##  4.1-2: skip
##  4.1-3: fixed


import univention.testing.strings as uts
import univention.testing.utils as utils
import pytest


class Test_UDMExtension(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	@pytest.mark.xfail(reason='wrong version')
	def test_extended_attribute_boolean_syntax(self, udm):
		"""settings/extended_attribute with boolean syntax"""
		# versions:
		#  4.1-2: skip
		#  4.1-3: fixed
		properties = {
			'name': uts.random_name(),
			'shortDescription': uts.random_string(),
			'CLIName': uts.random_name(),
			'module': 'users/user',
			'syntax': 'boolean',
			'mayChange': '1',
			'objectClass': 'univentionFreeAttributes',
			'ldapMapping': 'univentionFreeAttribute15'
		}
		extended_attribute = udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)

		userA = udm.create_user(**{properties['CLIName']: '0'})[0]
		userB = udm.create_user(**{properties['CLIName']: '1'})[0]
		utils.wait_for_connector_replication()
		utils.verify_ldap_object(userA, {properties['ldapMapping']: []})
		utils.verify_ldap_object(userB, {properties['ldapMapping']: ['1']})
		udm.modify_object('users/user', dn=userA, **{properties['CLIName']: '1'})
		udm.modify_object('users/user', dn=userB, **{properties['CLIName']: '0'})
		utils.verify_ldap_object(userA, {properties['ldapMapping']: ['1']})
		utils.verify_ldap_object(userB, {properties['ldapMapping']: []})
