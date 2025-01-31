#!/usr/share/ucs-test/runner python3
## desc: Test if a domain user account is locked out and freed.
## exposure: dangerous
## packages: [univention-samba4, univention-s4-connector]
## bugs: [35898]
## roles:
## - domaincontroller_master
## - domaincontroller_backup
## - domaincontroller_slave

from subprocess import PIPE, Popen
from sys import exit
from time import sleep

from univention.config_registry import ConfigRegistry
from univention.testing import utils
from univention.testing.codes import TestCodes
from univention.testing.strings import random_username


LOCKOUT_DURATION = 1  # duration of lockout in minutes
LOCKOUT_THRESHOLD = 3  # amount of auth. attempts allowed before the lock out
TEST_USER_PASS = 'Univention1'

UCR = ConfigRegistry()

admin_username = ''
admin_password = ''
test_username = ''
hostname = ''


def remove_samba_warnings(input_str):
    """Removes the Samba Warning/Note from the given input_str."""
    # ignoring following messages (Bug #37362):
    input_str = input_str.replace(b'WARNING: No path in service IPC$ - making it unavailable!', b'')
    return input_str.replace(b'NOTE: Service IPC$ is flagged unavailable.', b'').strip()


def create_and_run_process(cmd, stdout=PIPE):
    """
    Creates a process as a Popen instance with a given 'cmd'
    and 'communicates' with it. Returns (stdout, stderr).
    """
    proc = Popen(cmd, stdout=stdout, stderr=PIPE)
    stdout, stderr = proc.communicate()

    if stderr:
        stderr = remove_samba_warnings(stderr)
    if stdout:
        stdout = remove_samba_warnings(stdout)

    return stdout.decode('UTF-8'), stderr.decode('UTF-8')


def try_to_authenticate(password):
    """
    Tries to authenticate a 'test_username' user with a given 'password'
    using smbclient and execute an 'ls'. Returns (stdout, stderr).
    """
    print("\nTrying to authenticate a '%s' user with a password '%s'" % (test_username, password))

    cmd = (
        "smbclient", "//" + hostname + "/" + test_username,
        "-U", test_username + "%" + password, "--kerberos",
        "-t", "20",  # 20 seconds timeout per operation.
        "-c", "ls",
        "--debuglevel=1",
    )

    return create_and_run_process(cmd)


def set_reset_lockout_settings(lock_duration, lock_threshold):
    """Sets the lockout settings to a given values."""
    print("\nSetting account lockout settings to the following values (lockout duration = %s min; attempts before lockout = %s):" % (lock_duration, lock_threshold))

    cmd = (
        "samba-tool", "domain", "passwordsettings", "set",
        "--account-lockout-duration=" + lock_duration,
        "--account-lockout-threshold=" + lock_threshold,
        "-U", admin_username + '%' + admin_password,
        "--debuglevel=1",
    )

    stdout, stderr = create_and_run_process(cmd)
    if stderr:
        utils.fail("An error/warning occurred while trying to set/reset account lockout settings via samba-tool command '%s':\n%r" % (" ".join(cmd), stderr))
    if stdout:
        print(stdout)


def create_delete_test_user(should_exist):
    """
    Creates or deletes the 'test_username' depending on the given argument
    via 'samba-tool'. User password is TEST_USER_PASS.
    """
    if should_exist is True:
        print("\nCreating a test user with a username '%s'" % test_username)
        cmd = ("samba-tool", "user", 'create', test_username, TEST_USER_PASS)
    elif should_exist is False:
        print("\nDeleting a test user with a username '%s'" % test_username)
        cmd = ("samba-tool", "user", 'delete', test_username)
    else:
        utils.fail("The given 'should_exist'='%s' value is not supported. Pass 'True' to create a user or 'False' to delete." % should_exist)

    cmd += ("-U", admin_username + '%' + admin_password, "--debuglevel=1")

    stdout, stderr = create_and_run_process(cmd)
    if stderr:
        utils.fail("An error/warning occurred while trying to create or remove a user with a username '%s' via command: %s'.\nSTDERR: '%s'." % (test_username, " ".join(cmd), stderr))
    if stdout:
        print(stdout)


def check_no_errors_present_in_output(stdout, stderr):
    """
    Fails the test if there are signs of errors found in the given
    'stdout' or 'stderr'.
    """
    complete_output = stdout + stderr

    if 'NT_STATUS_ACCOUNT_LOCKED_OUT' in complete_output:
        utils.fail("\nThe 'NT_STATUS_ACCOUNT_LOCKED_OUT' error was found in the output.\nSTDOUT: '%s'. STDERR: '%s'." % (stdout, stderr))

    elif 'NT_STATUS_LOGON_FAILURE' in complete_output:
        utils.fail("\nThe 'NT_STATUS_LOGON_FAILURE' error was found in the output.\nSTDOUT: '%s'. STDERR: '%s'." % (stdout, stderr))

    elif 'NT_STATUS_OK' in complete_output:
        # the (only one possible) success status was found
        # (http://msdn.microsoft.com/en-us/library/ee441884.aspx)
        return

    elif 'NT_STATUS_' in complete_output:
        # all the rest status options are signs of errors
        utils.fail("\nAn error occurred. \nSTDOUT: '%s'. STDERR: '%s'" % (stdout, stderr))


def check_error_present_in_output(stdout, stderr):
    """
    Fails the test if there is no 'NT_STATUS_ACCOUNT_LOCKED_OUT' error in
    the given stdout or stderr.
    """
    if 'NT_STATUS_ACCOUNT_LOCKED_OUT' not in (stdout + stderr):
        utils.fail("The 'NT_STATUS_ACCOUNT_LOCKED_OUT' error could not be found in the STDOUT: '%s' or STDERR: '%s'. The account lockout may not work." % (stdout, stderr))


if __name__ == '__main__':
    print("\nObtaining settings for the test from the UCR")
    UCR.load()

    admin_username = UCR.get('tests/domainadmin/account')
    admin_password = UCR.get('tests/domainadmin/pwd')
    hostname = UCR.get('ldap/server/name')

    if not all((admin_username, admin_password, hostname)):
        print("Failed to obtain Administrator credentials or a hostname for the test from UCR. Skipping the test.")
        exit(TestCodes.REASON_INSTALL)

    # extract the 'Administrator' username:
    admin_username = admin_username.split(',')[0][len('uid='):]

    test_username = 'ucs_test_samba4_user_' + random_username(4)
    try:
        # create a user for the test with 'test_username'
        create_delete_test_user(True)

        # change lockout settings to the test values
        set_reset_lockout_settings(str(LOCKOUT_DURATION), str(LOCKOUT_THRESHOLD))

        sleep(30)  # wait a bit

        # try to authenticate the test user with a valid password
        print("\nTrying to authenticate '%s' user with a correct password '%s'" % (test_username, TEST_USER_PASS))
        stdout, stderr = try_to_authenticate(TEST_USER_PASS)
        check_no_errors_present_in_output(stdout, stderr)

        # try to lock the test user out with a random password
        print("\nTrying to lock the '%s' user out attempting to authenticate with a random password %d times:" % (test_username, LOCKOUT_THRESHOLD + 1))
        for _attempt in range(LOCKOUT_THRESHOLD + 1):
            stdout, stderr = try_to_authenticate("Foo" + random_username() + "123")
        check_error_present_in_output(stdout, stderr)

        # check that user is locked and that even a correct password won't work
        print("\nTrying to authenticate '%s' user with a correct password '%s' on a locked out account:" % (test_username, TEST_USER_PASS))
        stdout, stderr = try_to_authenticate(TEST_USER_PASS)
        check_error_present_in_output(stdout, stderr)

        # wait for unlocking
        print("\nWaiting for '%s' user account to be unlocked after the lock out timeout (%d min) expires:" % (test_username, LOCKOUT_DURATION))
        sleep(LOCKOUT_DURATION * 60 + 30)  # convert to seconds + some extra

        # try to authenticate again (should be no errors)
        print("\nTrying to authenticate '%s' user with a correct password '%s' after the lock time has expired" % (test_username, TEST_USER_PASS))
        stdout, stderr = try_to_authenticate(TEST_USER_PASS)
        check_no_errors_present_in_output(stdout, stderr)
    finally:
        # reset the lockout settings to default values
        set_reset_lockout_settings('default', 'default')

        # remove the test user
        create_delete_test_user(False)
