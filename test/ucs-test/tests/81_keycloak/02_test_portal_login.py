#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Test portal SSO login via keycloak
## tags: [keycloak]
## roles: [domaincontroller_master, domaincontroller_backup]
## exposure: dangerous

import pytest
from selenium.webdriver.common.by import By
from utils import keycloak_get_request, keycloak_password_change, keycloak_sessions_by_user, wait_for_id

import univention.testing.udm as udm_test
from univention.lib.umc import Unauthorized
from univention.testing.umc import Client
from univention.testing.utils import get_ldap_connection, wait_for_listener_replication


def test_login(portal_login_via_keycloak):
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user()[1]
        assert portal_login_via_keycloak(username, "univention")


def test_login_wrong_password_fails(portal_login_via_keycloak, keycloak_config):
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user()[1]
        assert portal_login_via_keycloak(username, "univentionWrong", fails_with=keycloak_config.wrong_password_msg_de)


def test_login_disabled_fails(portal_login_via_keycloak, keycloak_config):
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user(disabled=1)[1]
        assert portal_login_via_keycloak(username, "univention", fails_with=keycloak_config.wrong_password_msg_de)


def test_password_change_pwdChangeNextLogin(portal_login_via_keycloak, keycloak_config):
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user(pwdChangeNextLogin=1)[1]
        assert portal_login_via_keycloak(username, "univention", new_password="Univention.99")
        assert Client(username=username, password="Univention.99")
        with pytest.raises(Unauthorized):
            Client(username=username, password="univention")


def test_password_change_wrong_old_password_fails(portal_login_via_keycloak, keycloak_config):
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user(pwdChangeNextLogin=1)[1]
        assert portal_login_via_keycloak(username, "univentionBAD", fails_with=keycloak_config.wrong_password_msg_de)


def test_password_change_same_passwords_fails(portal_login_via_keycloak, keycloak_config, portal_config):
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user(pwdChangeNextLogin=1)[1]
        driver = portal_login_via_keycloak(
            username,
            "univention",
            new_password="univention",
            fails_with="Passwort ändern fehlgeschlagen. Das Passwort wurde bereits genutzt.")
        wait_for_id(driver, keycloak_config.password_id)


def test_password_change_new_password_too_short_fails(portal_login_via_keycloak, keycloak_config, portal_config):
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user(pwdChangeNextLogin=1)[1]
        portal_login_via_keycloak(
            username,
            "univention",
            new_password="a",
            fails_with="Passwort ändern fehlgeschlagen. Das Passwort ist zu kurz.",
        )


def test_password_change_confirm_new_passwords_fails(portal_login_via_keycloak, keycloak_config, portal_config):
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user(pwdChangeNextLogin=1)[1]
        driver = portal_login_via_keycloak(
            username,
            "univention",
            new_password="univention",
            new_password_confirm="univention1",
            fails_with="Passwörter sind nicht identisch.",
        )
        wait_for_id(driver, keycloak_config.password_id)


def test_password_change_empty_passwords_fails(portal_login_via_keycloak, keycloak_config, portal_config):
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user(pwdChangeNextLogin=1)[1]
        driver = portal_login_via_keycloak(username, "univention", verify_login=False)
        wait_for_id(driver, keycloak_config.password_id)
        # just click the button without old or new passwords
        driver.find_element(By.ID, keycloak_config.password_change_button_id).click()
        error = driver.find_element(By.CSS_SELECTOR, keycloak_config.password_update_error_css_selector)
        assert error.text == "Bitte geben Sie ein Passwort ein.", error.text
        wait_for_id(driver, keycloak_config.password_id)


def test_password_change_after_second_try(portal_login_via_keycloak, keycloak_config, portal_config):
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user(pwdChangeNextLogin=1)[1]
        driver = portal_login_via_keycloak(
            username,
            "univention",
            new_password="univention",
            fails_with="Passwort ändern fehlgeschlagen. Das Passwort wurde bereits genutzt.",
        )
        keycloak_password_change(driver, keycloak_config, "univention", "Univention.99", "Univention.99")
        wait_for_id(driver, portal_config.header_menu_id)
        assert Client(username=username, password="Univention.99")


def test_password_change_expired_shadowLastChange(portal_login_via_keycloak, keycloak_config):
    ldap = get_ldap_connection(primary=True)
    with udm_test.UCSTestUDM() as udm:
        dn, username = udm.create_user()
        changes = [
            ("shadowMax", [""], [b"2"]),
            ("shadowLastChange", [""], [b"1000"]),
        ]
        ldap.modify(dn, changes)
        wait_for_listener_replication()
        assert portal_login_via_keycloak(username, "univention", new_password="Univention.99")
        assert Client(username=username, password="Univention.99")
        with pytest.raises(Unauthorized):
            Client(username=username, password="univention")


def test_logout(portal_login_via_keycloak, portal_config, keycloak_config):
    with udm_test.UCSTestUDM() as udm:
        username = udm.create_user()[1]
        driver = portal_login_via_keycloak(username, "univention")
        wait_for_id(driver, portal_config.header_menu_id).click()
        sessions = keycloak_sessions_by_user(keycloak_config, username)
        assert sessions
        logout = wait_for_id(driver, portal_config.logout_button_id)
        assert logout.text == portal_config.logout_msg_de
        logout.click()
        wait_for_id(driver, portal_config.categories_id)
        sessions = keycloak_sessions_by_user(keycloak_config, username)
        assert not sessions


def test_login_not_possible_with_deleted_user(keycloak_config, portal_login_via_keycloak, portal_config):
    with udm_test.UCSTestUDM() as udm:
        dn, username = udm.create_user()
        # login
        driver = portal_login_via_keycloak(username, "univention")
        users = keycloak_get_request(keycloak_config, "realms/ucs/users", params={"search": username})
        assert len(users) == 1
        assert users[0]["username"] == username
        # logout
        wait_for_id(driver, portal_config.header_menu_id).click()
        wait_for_id(driver, portal_config.logout_button_id).click()
        wait_for_id(driver, portal_config.categories_id)
        sessions = keycloak_sessions_by_user(keycloak_config, username)
        assert not sessions
    wait_for_listener_replication()

    # user has been deleted, login should be denied
    #
    # see https://forge.univention.org/bugzilla/show_bug.cgi?id=55903
    # we can't logon with that deleted user, just check for that
    # generic error message
    # if this bug is fixed, just
    #   assert portal_login_via_keycloak(username, "univention", fails_with=keycloak_config.wrong_password_msg)
    # should do it
    driver = portal_login_via_keycloak(username, "univention", verify_login=False)
    error = wait_for_id(driver, "kc-error-message")
    assert error.text == "Unerwarteter Fehler während der Bearbeitung der Anfrage an den Identity Provider."

    # check that user is no longer available in keycloak
    users = keycloak_get_request(keycloak_config, "realms/ucs/users", params={"search": username})
    assert len(users) == 0
