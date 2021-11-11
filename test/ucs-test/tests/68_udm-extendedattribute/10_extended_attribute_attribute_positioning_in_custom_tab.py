#!/usr/share/ucs-test/runner pytest-3
## desc: Positioning in custom tabs
## tags: [udm]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import subprocess
import univention.testing.strings as uts
import univention.testing.utils as utils
import pytest


class Test_UDMExtension(object):
	@pytest.mark.tags('udm')
	@pytest.mark.roles('domaincontroller_master')
	@pytest.mark.exposure('careful')
	def test_extended_attribute_attribute_positioning_in_custom_tab(self, udm):
		"""Positioning in custom tabs"""
		tab = uts.random_name()
		extended_attributes = {}

		for i in range(4, 0, -1):
			properties = {
				'name': uts.random_name(),
				'shortDescription': uts.random_string(),
				'CLIName': uts.random_name(),
				'module': 'users/user',
				'objectClass': 'univentionFreeAttributes',
				'ldapMapping': 'univentionFreeAttribute%s' % i,
				'tabPosition': str(i),
				'tabName': tab
			}
			udm.create_object('settings/extended_attribute', position=udm.UNIVENTION_CONTAINER, **properties)
			extended_attributes[properties['CLIName']] = i

		module_help_text = subprocess.Popen([udm.PATH_UDM_CLI_CLIENT, properties['module']], stdout=subprocess.PIPE).communicate()[0].decode('UTF-8').splitlines()
		tab_position = 1
		for line in module_help_text:
			try:
				cli_name = line.strip().split()[0]
			except Exception:
				continue

			if cli_name in extended_attributes:
				assert extended_attributes[cli_name] == tab_position, 'Detected mistake in appearance order of attribute CLI names under tab'
				tab_position += 1

		assert tab_position >= 4, 'Not all created attributes found in module'
