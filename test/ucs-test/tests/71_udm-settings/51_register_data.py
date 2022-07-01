#!/usr/share/ucs-test/runner pytest-3
## desc: Register a settings/data object
## tags: [udm-ldapextensions,apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

import bz2
import os
import pipes
import shutil
import subprocess

import pytest

import univention.testing.strings as uts
import univention.testing.utils as utils

file_name = uts.random_name()
file_path = os.path.join('/tmp', file_name)


@pytest.fixture
def remove_tmp_file():
	yield
	try:
		os.remove(file_path)
	except OSError:
		pass


shutil.copy('/etc/hosts', file_path)
kwargs = dict(
	data_type=uts.random_name(),
	ucsversionstart=uts.random_ucs_version(),
	ucsversionend=uts.random_ucs_version(),
	meta=[uts.random_name(), uts.random_name()],
	package=uts.random_name(),
	packageversion=uts.random_version(),
)


def run_cmd(cmd):
	print('Running: {!r}'.format(cmd))
	cmd_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	cmd_out, cmd_err = cmd_proc.communicate()
	cmd_out, cmd_err = cmd_out.decode('UTF-8', 'replace'), cmd_err.decode('UTF-8', 'replace')
	print('exit code: {!r}'.format(cmd_proc.returncode))
	print('stdout:-----\n{}\n-----'.format(cmd_out))
	print('stderr:-----\n{}\n-----'.format(cmd_err))


@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('dangerous')
@pytest.mark.tags('udm-ldapextensions', 'apptest')
def test_register_data(udm, ucr, remove_tmp_file):
	"""Register a settings/data object"""
	ldap_base = ucr['ldap/base']
	# make sure object is remove at the end
	dn = 'cn={},cn=data,cn=univention,{}'.format(file_name, ldap_base)
	udm._cleanup.setdefault('settings/data', []).append(dn)
	register_cmd = [
		'ucs_registerLDAPExtension',
		'--binddn', 'cn=admin,{}'.format(ucr['ldap/base']),
		'--bindpwdfile', '/etc/ldap.secret',
		'--packagename', kwargs['package'],
		'--packageversion', kwargs['packageversion'],
		'--data', file_path,
		'--ucsversionstart', kwargs['ucsversionstart'],
		'--ucsversionend', kwargs['ucsversionend'],
		'--data_type', kwargs['data_type'],
		'--data_meta', kwargs['meta'][0],
		'--data_meta', kwargs['meta'][1],
	]
	cmd = ['/bin/bash', '-c', 'source /usr/share/univention-lib/ldap.sh && {}'.format(' '.join([pipes.quote(x) for x in register_cmd]))]
	run_cmd(cmd)

	cmd = ['udm', 'settings/data', 'list', '--filter', 'cn={}'.format(file_name)]
	print('Running {!r}...'.format(cmd))
	subprocess.call(cmd)

	with open(file_path) as fp:
		data = fp.read()

	utils.verify_ldap_object(
		dn,
		{
			'cn': [file_name],
			'description': [],  # ucs_registerLDAPExtension doesn't support description
			'univentionDataFilename': [file_name],
			'univentionDataType': [kwargs['data_type']],
			'univentionData': [bz2.compress(data.encode('UTF-8'))],
			'univentionUCSVersionStart': [kwargs['ucsversionstart']],
			'univentionUCSVersionEnd': [kwargs['ucsversionend']],
			'univentionDataMeta': kwargs['meta'],
			'univentionOwnedByPackage': [kwargs['package']],
			'univentionOwnedByPackageVersion': [kwargs['packageversion']],
		}
	)

	nums = kwargs['packageversion'].split('.')
	num0 = int(nums[0])
	num0 -= 1
	older_packageversion = '.'.join([str(num0)] + nums[1:])
	print('Registering with lower package version ({!r}) and changed "data_type"...'.format(kwargs['packageversion']))
	register_cmd = [
		'ucs_registerLDAPExtension',
		'--binddn', 'cn=admin,{}'.format(ucr['ldap/base']),
		'--bindpwdfile', '/etc/ldap.secret',
		'--packagename', kwargs['package'],
		'--packageversion', older_packageversion,
		'--data', file_path,
		'--ucsversionstart', kwargs['ucsversionstart'],
		'--ucsversionend', kwargs['ucsversionend'],
		'--data_type', uts.random_name(),
		'--data_meta', 'Some different meta data',
		'--data_meta', 'Some very different meta data',
	]
	cmd = ['/bin/bash', '-c', 'source /usr/share/univention-lib/ldap.sh && {}'.format(' '.join([pipes.quote(x) for x in register_cmd]))]
	run_cmd(cmd)

	utils.verify_ldap_object(
		dn,
		{
			'cn': [file_name],
			'description': [],  # ucs_registerLDAPExtension does not support description
			'univentionDataFilename': [file_name],
			'univentionDataType': [kwargs['data_type']],
			'univentionData': [bz2.compress(data.encode('UTF-8'))],
			'univentionUCSVersionStart': [kwargs['ucsversionstart']],
			'univentionUCSVersionEnd': [kwargs['ucsversionend']],
			'univentionDataMeta': kwargs['meta'],
			'univentionOwnedByPackage': [kwargs['package']],
			'univentionOwnedByPackageVersion': [kwargs['packageversion']],
		}
	)
	print('OK: object unchanged.')
