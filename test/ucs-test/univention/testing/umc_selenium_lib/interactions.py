from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import json
import logging

logger = logging.getLogger(__name__)


class Interactions(object):
	def click_text(self, text):
		logger.info("Clicking the text %r", text)
		self.click_element('//*[contains(text(), "%s")]' % (text,))

	def click_checkbox_of_grid_entry(self, name):
		logger.info("Clicking the checkbox of the grid entry  %r", name)
		self.click_element(
			'//*[contains(concat(" ", normalize-space(@class), " "), " dgrid-cell ")][@role="gridcell"]//*[contains(text(), "%s")]/../..//input[@type="checkbox"]/..'
			% (name,)
		)

	def click_grid_entry(self, name):
		logger.info("Clicking the grid entry %r", name)
		self.click_element(
			'//*[contains(concat(" ", normalize-space(@class), " "), " dgrid-cell ")][@role="gridcell"]/descendant-or-self::node()[contains(text(), "%s")]'
			% (name,)
		)

	def click_tree_entry(self, name):
		logger.info("Clicking the tree entry %r", name)
		self.click_element('//*[contains(concat(" ", normalize-space(@class), " "), " dgrid-column-label ")][contains(text(), "%s")]' % (name,))

	def click_button(self, buttonname):
		logger.info("Clicking the button %r", buttonname)
		self.click_element('//*[contains(concat(" ", normalize-space(@class), " "), " dijitButtonText ")][text() = "%s"]' % (buttonname,))

	def click_tile(self, tilename):
		logger.info("Clicking the tile %r", tilename)
		self.click_element('//*[contains(concat(" ", normalize-space(@class), " "), " umcGalleryName ")][text() = "%s"]' % (tilename,))

	def click_tab(self, tabname):
		logger.info("Clicking the tab %r", tabname)
		self.click_element('//*[contains(concat(" ", normalize-space(@class), " "), " tabLabel ")][text() = "%s"]' % (tabname,))

	def click_element(self, xpath):
		"""
		Click on the element which is found by the given xpath.

		Only use with caution when there are multiple elements with that xpath.
		Waits for the element to be clickable before attempting to click.
		"""
		elems = webdriver.support.ui.WebDriverWait(xpath, 60).until(
			self.get_all_enabled_elements
		)

		if len(elems) != 1:
			logger.warn(
				"Found %d clickable elements instead of 1. Trying to click on "
				"the first one." % (len(elems),)
			)
		elems[0].click()

	def open_side_menu(self):
		self.click_element('//*[@class="umcMobileMenuToggleButton"]')

	def enter_input(self, inputname, inputvalue):
		"""
		Enter inputvalue into an input-element with the tag inputname.
		"""
		logger.info('Entering %r into the input-field %r.', inputvalue, inputname)
		elem = self.get_input(inputname)
		elem.clear()
		elem.send_keys(inputvalue)

	def submit_input(self, inputname):
		"""
		Submit the input in an input-element with the tag inputname.
		"""
		logger.info('Submitting input field %r.' % (inputname,))
		elem = self.get_input(inputname)
		# elem.submit() -> This doesn't work, when there is an html element
		# named 'submit'.
		elem.send_keys(Keys.RETURN)

	def get_input(self, inputname):
		"""
		Get an input-element with the tag inputname.
		"""
		xpath = '//input[@name= %s ]' % (json.dumps(inputname),)
		elems = webdriver.support.ui.WebDriverWait(xpath, 60).until(
			self.get_all_enabled_elements
		)

		if len(elems) != 1:
			logger.warn(
				"Found %d input elements instead of 1. Trying to use the first "
				"one." % (len(elems),)
			)
		return elems[0]

	def get_all_enabled_elements(self, xpath):
		elems = self.driver.find_elements_by_xpath(xpath)
		clickable_elems = [elem for elem in elems if elem.is_enabled() and elem.is_displayed()]
		if len(clickable_elems) > 0:
			return clickable_elems
		return False
