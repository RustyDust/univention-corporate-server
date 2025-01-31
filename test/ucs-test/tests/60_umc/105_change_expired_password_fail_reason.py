#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Test detection of changing expired password failure reason
## exposure: dangerous
## packages: [univention-management-console-server]
## roles: [domaincontroller_master]
## tags: [skip_admember]

import contextlib
from typing import Dict, List  # noqa: F401

import pytest
from samba import generate_random_machine_password

from univention.admin.uldap import getAdminConnection
from univention.config_registry import ConfigRegistry
from univention.lib.umc import Unauthorized
from univention.testing import utils


samba4_installed = utils.package_installed('univention-samba4')
ucr = ConfigRegistry()
ucr.load()
lo, pos = getAdminConnection()

REASON_TOO_SHORT = "Changing password failed. The password is too short."
REASON_TOO_SHORT_AT_LEAST_CHARACTERS = "Changing password failed. The password is too short. The password must consist of at least 8 characters."
REASON_TOO_SIMPLE = "Changing password failed. The password is too simple."
REASON_PALINDROME = "Changing password failed. The password is a palindrome."
REASON_DICTIONARY = "Changing password failed. The password is based on a dictionary word."
REASON_DIFFERENT_WORDS = 'Changing password failed. The password does not contain enough different characters.'
REASON_ALREADY_USED = 'Changing password failed. The password was already used.'
REASON_MINIMUM_AGE = 'Changing password failed. The minimum password age is not reached yet.'
REASON_TOO_SIMILAR = 'Changing password failed. The password is too similar to the old one.'

# TODO: add a lot more unimplemented tests!
reasons = {
    REASON_TOO_SHORT: ['Test', 'ana'],
    REASON_TOO_SHORT_AT_LEAST_CHARACTERS: [],
    REASON_TOO_SIMPLE: ['123456789'],
    REASON_PALINDROME: [],
    REASON_DICTIONARY: ['chocolate'],
    REASON_DIFFERENT_WORDS: ['ooooooooo'],
}  # type: Dict[str, List[str]]
if samba4_installed:
    reasons = {
        REASON_TOO_SHORT: [],
        REASON_TOO_SHORT_AT_LEAST_CHARACTERS: ['Test', 'ana'],
        REASON_TOO_SIMPLE: ['123456789', 'chocolate', 'ooooooooo'],
        REASON_PALINDROME: [],
        REASON_DICTIONARY: [],
        REASON_DIFFERENT_WORDS: [],
    }


@contextlib.contextmanager
def enabled_password_quality_checks(ucr):
    # TODO: from 07_expired_password: only if univention-samba4 is not installed
    if samba4_installed:
        yield
        return
    ldap_base = ucr.get('ldap/base')
    dn = f'cn=default-settings,cn=pwhistory,cn=users,cn=policies,{ldap_base}'
    old = lo.getAttr(dn, 'univentionPWQualityCheck')
    new = [b'TRUE']
    lo.modify(dn, [('univentionPWQualityCheck', old, new)])
    yield
    lo.modify(dn, [('univentionPWQualityCheck', new, old)])


@pytest.mark.parametrize('new_password,reason', [[y, reason] for reason, x in reasons.items() for y in x])
def test_password_changing_failure_reason(new_password, reason, udm, Client, random_string, ucr):
    print(f'test_password_changing_failure_reason({new_password!r}, {reason!r})')
    with enabled_password_quality_checks(ucr):
        _test_password_changing_failure_reason(new_password, reason, udm, Client, random_string)


def _test_password_changing_failure_reason(new_password, reason, udm, Client, random_string):
    password = generate_random_machine_password(14, 14)
    userdn, username = udm.create_user(password=password, pwdChangeNextLogin=1)
    client = Client(language='en-US')
    if samba4_installed:
        utils.wait_for_connector_replication()
    print(f'change password from {password!r} to {new_password!r}')
    with pytest.raises(Unauthorized) as msg:
        client.umc_auth(username, password, new_password=new_password)
    assert reason == msg.value.message, f'Expected error {reason!r} but got {msg.value.message!r}'
