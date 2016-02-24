import time
from lxml import html
import requests
import json
from selenium import webdriver

# Helper methods
def populate_menu(item,xpath):
	# Declare global variables
	global scrape_list

	elements = browser.find_elements_by_xpath(xpath)

	for e in elements:
		scrape_list[item].append(e.get_attribute('href'))

# Scrape structure
scrape_list = {
	'clothing' : [],
	'accessories' : []
}

# Initiate Firefox driver
browser = webdriver.Firefox()

# Set wait limit for page load
browser.implicitly_wait(15)

# Load target page
browser.get("http://www.birdsnest.com.au")

# Populate menu list for clothing
populate_menu('clothing','//*[@id="js-header__nav"]/li[2]/ul/li/a')

# Populate menu list for accessories
populate_menu('accessories','//*[@id="js-header__nav"]/li[6]/ul/li/a')

print scrape_list

browser.quit()