#!/usr/share/ucs-test/runner /usr/bin/python3
## desc: Test adding portal categories and entries from within the portal
## roles:
##  - domaincontroller_master
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import importlib
import os
import sys
import time


test_lib = os.environ.get('UCS_TEST_LIB', 'univention.testing.apptest')
try:
    test_lib = importlib.import_module(test_lib)
except ImportError:
    print(f'Could not import {test_lib}. Maybe set $UCS_TEST_LIB')
    sys.exit(1)


def _add_german_text(chrome, text):
    chrome.enter_tab()
    chrome.enter_return()
    time.sleep(.1)
    chrome.enter_tab()
    chrome.send_keys(text)
    chrome.enter_tab()
    chrome.enter_tab()
    chrome.enter_return()
    time.sleep(.1)


def test_inline_creation(chrome, admin_username, admin_password, udm):
    # chrome.goto_portal()
    chrome.get('/univention/portal')
    chrome.portal_login(admin_username, admin_password)
    chrome.wait_until_clickable('#portalCategories')
    chrome.wait_until_clickable_and_click('#header-button-menu')
    chrome.wait_until_clickable_and_click('button.portal-sidenavigation__edit-mode')

    chrome.enter_return()
    # create category
    chrome.wait_until_clickable_and_click('.portal-categories__add-button')
    buttons = chrome.find_all('.tile-add-modal-button')
    assert len(buttons) == 2
    buttons[0].click()
    cat_name = 'internal-name-for-a-category'
    cat_display = 'Category Name'
    chrome.send_keys(cat_name)
    chrome.enter_tab()
    chrome.send_keys(cat_display + ' EN')
    _add_german_text(chrome, cat_display + ' DE')
    chrome.enter_tab()
    chrome.enter_tab()
    chrome.enter_return()
    time.sleep(.2)
    chrome.wait_until_gone('.modal-wrapper--isVisible')
    categories = udm.get('portals/category')
    category = list(categories.search('name=%s' % cat_name))[0].open()
    expected = {'name': 'internal-name-for-a-category', 'displayName': {'en_US': 'Category Name EN', 'de_DE': 'Category Name DE'}, 'entries': [], 'objectFlag': []}
    assert category.properties == expected

    # create tile
    buttons = chrome.find_all('.tile-add')
    buttons[-1].click()
    buttons = chrome.find_all('.tile-add-modal-button')
    assert len(buttons) == 4
    buttons[0].click()
    tile_name = 'internal-name-for-a-tile'
    tile_display = 'Tile Name'
    tile_description = 'Tile Description'
    tile_keyword = 'Keyword'
    tile_link = 'https://example.com'
    chrome.send_keys(tile_name)
    chrome.enter_tab()
    chrome.send_keys(tile_display + ' EN')
    _add_german_text(chrome, tile_display + ' DE')
    chrome.enter_tab()
    chrome.send_keys(tile_description + ' EN')
    _add_german_text(chrome, tile_description + ' DE')
    chrome.enter_tab()
    chrome.send_keys(tile_keyword + ' EN')
    _add_german_text(chrome, tile_keyword + ' DE')
    chrome.enter_tab()
    chrome.enter_tab()  # activated
    chrome.send_keys(tile_link)
    chrome.click_element('form.admin-entry button.primary')
    time.sleep(.2)
    chrome.wait_until_gone('.modal-wrapper--isVisible')
    entries = udm.get('portals/entry')
    entry = list(entries.search('name=%s' % tile_name))[0].open()
    expected = {
        'name': 'internal-name-for-a-tile',
        'displayName': {'de_DE': 'Tile Name DE', 'en_US': 'Tile Name EN'},
        'description': {'en_US': 'Tile Description EN', 'de_DE': 'Tile Description DE'},
        'link': [['en_US', 'https://example.com']],
        'allowedGroups': [],
        'activated': True,
        'anonymous': False,
        'icon': None,
        'linkTarget': 'useportaldefault',
        'backgroundColor': None,
        'target': None,
        'keywords': {'de_DE': 'Keyword DE', 'en_US': 'Keyword EN'},
        'objectFlag': [],
    }
    assert entry.properties == expected

    # create folder
    buttons = chrome.find_all('.tile-add')
    buttons[-1].click()
    buttons = chrome.find_all('.tile-add-modal-button')
    assert len(buttons) == 4
    buttons[2].click()
    folder_name = 'internal-name-for-a-folder'
    folder_display = 'Folder Name'
    chrome.send_keys(folder_name)
    chrome.enter_tab()
    chrome.send_keys(folder_display + ' EN')
    _add_german_text(chrome, folder_display + ' DE')
    chrome.enter_shift_tab()
    chrome.enter_return()
    time.sleep(.2)
    chrome.wait_until_gone('.modal-wrapper--isVisible')
    folders = udm.get('portals/folder')
    folder = list(folders.search('name=%s' % folder_name))[0].open()
    expected = {'name': 'internal-name-for-a-folder', 'displayName': {'en_US': 'Folder Name EN', 'de_DE': 'Folder Name DE'}, 'entries': [], 'objectFlag': []}
    assert folder.properties == expected

    category.delete()
    entry.delete()
    folder.delete()


if __name__ == '__main__':
    test_lib.run_test_file(__file__)
