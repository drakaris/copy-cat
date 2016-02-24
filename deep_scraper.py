import time
from lxml import html
import requests
import json
from selenium import webdriver

# Helper methods
def clothing_scraper(browser,links):
	# Iterate through links
	for link in links:
		browser.get(link)
		print link

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
elements = browser.find_elements_by_xpath('//*[@id="js-header__nav"]/li[2]/ul/li/a')

for e in elements:
	scrape_list['clothing'].append(e.get_attribute('href'))

# Populate menu list for accessories
elements = browser.find_elements_by_xpath('//*[@id="js-header__nav"]/li[6]/ul/li/a')

for e in elements:
	scrape_list['accessories'].append(e.get_attribute('href'))

# Call clothing scraper
clothing_scraper(browser, scrape_list['clothing'])

browser.quit()