import time
from datetime import datetime
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

def scrape(key,url):
	# Global variables
	global browser

	# Filters to be scraped
	filter_list = {
	'clothing' : ['Style','Colour','Body Shape','Features','Occasion','Personality','Collection','Fashion Collection'],
	'accessories' : ['Style','Colour','Body Shape','Features','Occasion','Personality','Collection','Fashion Collection']
	}

	# Current selected tags structure
	product_cache = {
	'tag' : '',
	'value' : '',
	'products' : []
	}

	# Load page
	browser.get(url)

	# Toggle all products - off
	browser.find_element_by_xpath('//*[@id="js-filtered_items"]/div[1]/div/div[2]/div[1]/div/ul/li[2]/a').click()

	# Find first filter element and close by clicking

	browser.find_element_by_xpath('//*[@id="js-filters"]/div[1]/div/div[1]').click()
	
	# Get all filter DOM sections
	filters_elements = browser.find_elements_by_class_name('js-filter-section')
	
	for filters in filters_elements:
		# Check if filter is required
		if filters.get_attribute('data-displayname') in filter_list[key]:
			# Store data-displayname in product cache as tag
			product_cache['tag'] = filters.get_attribute('data-displayname')
			# Click to expand filter options
			filters.find_element_by_class_name('twisty_title').click()
			# Get list of filter labels
			filter_labels = filters.find_elements_by_tag_name('label')
			for label in filter_labels:
				while(1):
					# Check for shadow-filter on parent
					parent_class_list = label.find_element_by_xpath('..').get_attribute('class').split()
					if 'shadow-filter' in parent_class_list:
						print 'Ignoring label'
						break
					# Check for NoneType label
					if label.get_attribute('data-name') is None:
						break
					# Paginate index
					paginate_index = 1
					repeat = 0
					# Apply label
					try:
						time.sleep(2)
						label.click()
						time.sleep(4)
					except Exception as e:
						h = open("logs/deep_retry.log","a")
						h.write('[' + str(datetime.now()) + '] ' + url + '\n')
						h.close()

						f = open("logs/deep_error.log","a")
						f.write('[' + str(datetime.now()) + '] ' + 'Unable to click label' + '\n')
						f.close()
					else:
						# Wait for label to apply
						print 'Filter applied'
						# Store data-name in product cache as value
						try:
							product_cache['value'] = label.get_attribute('data-name')
							label_count = int(label.find_element_by_class_name('item_count').text.strip("()"))
						except Exception as e:
							h = open("logs/deep_retry.log","a")
							h.write('[' + str(datetime.now()) + '] ' + url + '\n')
							h.close()

							f = open("logs/deep_error.log","a")
							f.write('[' + str(datetime.now()) + '] ' + e.message + '\n')
							f.close()
						# Get product url with pagination
						while(1):
							product_container = browser.find_element_by_id('items')
							product_list = product_container.find_elements_by_class_name('catalogue-item__a')
							for product_item in product_list:
								try:
									product_cache['products'].append(product_item.get_attribute('href'))
								except Exception as e:
									h = open("logs/deep_retry.log","a")
									h.write('[' + str(datetime.now()) + '] ' + url + '\n')
									h.close()

									f = open("logs/deep_error.log","a")
									f.write('[' + str(datetime.now()) + '] ' + e.message + '\n')
									f.close()

							# Move to next page
							try:
								if paginate_index == 1:
									browser.find_element_by_xpath('//*[@id="js-filtered_items"]/div[1]/div/div[2]/div[2]/div/div/span/a').click()
									print 'Navigated to page 2'
									time.sleep(4)
								else:
									browser.find_element_by_xpath('//*[@id="js-filtered_items"]/div[1]/div/div[2]/div[2]/div/div/span[2]/a').click()
									print 'Navigated to page ' + (paginate_index + 1)
									time.sleep(4)
							except Exception as e:
								print 'End of pages'
								break
							else:
								paginate_index = paginate_index + 1
						
						print 'Tag : ' + product_cache['tag']
						print 'Value : ' + product_cache['value']
						print 'Count : ' + str(len(product_cache['products']))
						print '\n'

						# Perform consitency check
						if len(product_cache['products']) == label_count:
							repeat = 0
						else:
							repeat = 1
							print 'Inconsistent data'
						
						# Refresh product cache
						print 'Refreshing product cache'
						del product_cache['products'][:]

						# Unapply label
						label.click()
						# Wait for label to unapply
						print 'Reverting filter'
						time.sleep(3)
					# Perform consitency check
					if repeat == 0:
						break
					else:
						return 1

# Scrape structure
scrape_list = {
	'clothing' : [],
	'accessories' : []
}

# Base url
base_url = 'http://www.birdsnest.com.au/women/'
# Scrape exclusion
scrape_exclude_list = ['lifestyle']

# Initiate Firefox driver
browser = webdriver.Firefox()

# Set wait limit for page load
browser.implicitly_wait(7)

# Load target page
browser.get("http://www.birdsnest.com.au")

# Populate menu list for clothing
populate_menu('clothing','//*[@id="js-header__nav"]/li[2]/ul/li/a')

# Populate menu list for accessories
populate_menu('accessories','//*[@id="js-header__nav"]/li[6]/ul/li/a')

#while scrape(scrape_list['accessories'][0]):
#	continue

for key in scrape_list:
	for k in scrape_list[key]:
		#print key + ' => ' + k
		for e in scrape_exclude_list:
			if k == base_url + e:
				# Skip and continue
				continue
			else:
				while scrape(key,k):
					continue
