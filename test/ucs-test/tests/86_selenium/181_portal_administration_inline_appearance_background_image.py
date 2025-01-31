#!/usr/share/ucs-test/runner /usr/bin/python3
## desc: Test portal_administration_inline_appearance_background_image
## roles:
##  - domaincontroller_master
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import importlib
import os
import sys


test_lib = os.environ.get('UCS_TEST_LIB', 'univention.testing.apptest')
try:
    test_lib = importlib.import_module(test_lib)
except ImportError:
    print(f'Could not import {test_lib}. Maybe set $UCS_TEST_LIB')
    sys.exit(1)


def _save(chrome):
    form = chrome.assert_one('form.edit-mode-side-navigation__form')
    chrome.click_element_below(form, 'button.primary')
    chrome.wait_until_clickable('#portalCategories')


def _change_background(chrome):
    chrome.wait_until_clickable_and_click('#header-button-menu')
    chrome.wait_until_clickable_and_click('button.portal-sidenavigation__edit-mode')
    chrome.wait_until_clickable_and_click('#header-button-settings')
    chrome.wait_until_clickable('form.edit-mode-side-navigation__form')
    chrome.assert_one('form.edit-mode-side-navigation__form')
    uploaders = chrome.find_all('div.image-upload')
    assert len(uploaders) == 2
    uploader = chrome.assert_one_below(uploaders[1], 'input[type=file]')
    img_path = chrome.save_screenshot('background')
    uploader.send_keys(img_path)


def _remove_background(chrome):
    chrome.wait_until_clickable_and_click('#header-button-menu')
    chrome.wait_until_clickable_and_click('button.portal-sidenavigation__edit-mode')
    chrome.wait_until_clickable_and_click('#header-button-settings')
    chrome.wait_until_clickable('form.edit-mode-side-navigation__form')
    chrome.assert_one('form.edit-mode-side-navigation__form')
    uploaders = chrome.find_all('div.image-upload')
    assert len(uploaders) == 2
    buttons = chrome.find_all_below(uploaders[1], 'footer button')
    buttons[1].click()


def test_background(chrome, admin_username, admin_password, test_logger):
    # chrome.goto_portal()
    chrome.get('/univention/portal')
    chrome.portal_login(admin_username, admin_password)
    chrome.wait_until_clickable('#portalCategories')
    body_background = chrome.assert_one('.portal__background').value_of_css_property('background-image')
    if body_background != 'none':
        raise ValueError('Background already set')

    _change_background(chrome)
    body_background = chrome.assert_one('.portal__background').value_of_css_property('background-image')
    if 'data:image/png;base64,' not in body_background:
        raise ValueError('Changing the background image was not hot changed')

    _save(chrome)
    body_background = chrome.assert_one('.portal__background').value_of_css_property('background-image')
    if body_background == 'none':
        raise ValueError('Background not set')

    _remove_background(chrome)
    body_background = chrome.assert_one('.portal__background').value_of_css_property('background-image')
    if body_background != 'none':
        raise ValueError('Background not set')

    _save(chrome)
    body_background = chrome.assert_one('.portal__background').value_of_css_property('background-image')
    if body_background != 'none':
        raise ValueError('Background still set')


if __name__ == '__main__':
    test_lib.run_test_file(__file__)
