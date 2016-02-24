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

def scrape_clothing(url):
	global browser

	# Load page
	browser.get(url)

	# Toggle all products - off
	browser.find_element_by_xpath('//*[@id="js-filtered_items"]/div[1]/div/div[2]/div[1]/div/ul/li[2]/a').click()

	filters = browser.find_elements_by_xpath('//*[@id="js-filters"]//span')
	for f in filters:
		print f.text

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

scrape_clothing(scrape_list['clothing'][0])