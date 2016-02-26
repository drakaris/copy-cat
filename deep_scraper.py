import time
from datetime import datetime
from selenium import webdriver
from py2neo import Graph,Node,Relationship,watch
from lxml import html
import requests


# Helper methods
def product_scrape(label,x):
	# Accepts URL returns graph node
	# Data structure schema
	metadata = {
	'name' : '',
	'brand' : '',
	'price' : '',
	'url' : '',
	'image' : [],
	'about' : [],
	'features' : [''],
	'tags' : [''],
	'Boobs' : [''],
	'Tummy' : [''],
	'Hips' : [''],
	'occasions' : [''],
	'collections' : [''],
	'personalities' : [''],
	'related_body_shapes' : [''],
	'related_outfits_count' : ''
	}

	exclusion_list = {
	'p' : ['','Style code:'],
	'a' : ['','womens','shop-by','outfits']
	}

	# Load global graph variable
	global graph

	# Load product page
	r = requests.get(x)

	# Construct DOM trees
	domTree = html.fromstring(r.content)
	tree = domTree.getroottree()

	# Extract product name
	name = domTree.xpath('//*[@id="js-item_middle"]/h5/text()')
	print name[0].strip()
	metadata['name'] = name[0].strip()

	# Extract product brand
	brand = domTree.xpath('//*[@id="js-item_middle"]/h1/a/text()')
	print '\t> Brand: ' + brand[0].strip()
	metadata['brand'] = brand[0].strip()

	# Extract product price
	price = domTree.xpath('//*[@id="item_price"]/h5/text()')
	print '\t> Price: ' + price[0].strip()
	metadata['price'] = price[0].strip()

	# Store product url
	metadata['url'] = x
	print '\t> URL: ' + metadata['url']

	# Extract product images
	image = list(set(domTree.xpath('//*[@id="js-container"]/div[1]/div[1]/div[2]//img/@src')))
	print '\t> Image(s): ' + str(len(image))
	metadata['image'] = image

	# Extract product description
	about = domTree.xpath('//*[@id="tab0"]//p/text()')
	for i in range(0,len(about)):
		about[i] = about[i].strip()
	for rem in exclusion_list['p']:
		about.remove(rem)
	print '\t> About: ' + str(len(about)) + ' paragraph(s)'
	metadata['about'] = about

	# Extract product features
	features = list(set(domTree.xpath('//*[@id="tab0"]//li/text()')))
	print '\t> Feature(s): ' + str(len(features))
	if len(features):
		metadata['features'] = features
	else:
		metadata['features'] = 'None'

	# Extract product tags
	tags = list(set(domTree.xpath('//*[@id="tab0"]/div[3]//a/text()')))
	for i in range(0,len(tags)):
		tags[i] = tags[i].strip()
	print '\t> Tag(s): ' + str(len(tags))
	if len(tags):
		metadata['tags'] = tags
	else:
		metadata['tags'] = 'None'

	# Extract product body shapes
	body_data = domTree.xpath('//div[@class="input--circle checked"]')
	for e in body_data:
		body_part = 'string(' + tree.getpath(e.getparent().getparent().getparent().getparent().getprevious()) + ')'
		body_part =  domTree.xpath(body_part).strip()
		tag = 'string(' + tree.getpath(e.getnext()) + ')'
		tag =  domTree.xpath(tag).strip()
		metadata[body_part].append(tag)
	print '\t> Boobs: ' + str(metadata['Boobs'])
	print '\t> Tummy: ' + str(metadata['Tummy'])
	print '\t> Hips: ' + str(metadata['Hips'])

	# Extract additional product metadata
	links = list(set(domTree.xpath('//*[@id="tab1"]//a/@href')))
	for link in links:
		link_digested = link.split('/')
		for x in exclusion_list['a']:
			try:
				link_digested.remove(x)
			except:
				continue
		if link_digested[0] == 'body_shape':
			metadata['related_body_shapes'].append(link_digested[1])
		if link_digested[0] == 'occasion':
			metadata['occasions'].append(link_digested[1])
		if link_digested[0] == 'personality':
			metadata['personalities'].append(link_digested[1])
		if link_digested[0] == 'collection':
			metadata['collections'].append(link_digested[1])
	print '\t> Related body fits: ' + str(len(metadata['related_body_shapes']))
	print '\t> Occasion(s): ' + str(len(metadata['occasions']))
	print '\t> Personality(s): ' + str(len(metadata['personalities']))
	print '\t> Collection(s): ' + str(len(metadata['collections']))

	# Extract number of related outfits
	n_outfits = domTree.xpath('//*[@id="js-complete_the_look__index"]/text()')
	for i in range(0,len(n_outfits)):
		n_outfits[i] = n_outfits[i].strip()
		n = n_outfits[i].split(' ')
	if len(n_outfits):
		n_outfits = n[2]
	else:
		n_outfits = 0
	print '\t> Related outfits: ' + str(n_outfits)
	metadata['related_outfits_count'] = n_outfits

	# Find url under given label
	node = graph.find_one(label,'url',metadata['url'])

	# Iterate through metadata
	for m in metadata:
		node.properties[m] = metadata[m]
	node.labels.add('Products')
	print 'Pushing ' + metadata['url']
	node.push()

def database_insert(key,product_cache):
	# Neo4j settings
	global graph

	# Append extra_ to product tag
	product_cache['tag'] = str('extra_' + product_cache['tag'])

	# Set 'key' as label
	label = key

	# Set watcher for db requests
	watch("httpstream")

	# Search for nodes based on url under Products
	for url in product_cache['products']:
		format = url.split('#')
		url = format[0]
		node = graph.find_one('Products','url',url)
		if node:
			# This means node exists, add properties and push
			print 'Pushing ' + url
			# Check if property already exists
			if node.properties[product_cache['tag']]:
				# Append to existing property
				temp = node.properties[product_cache['tag']]
				temp.append(product_cache['value'])
				node.properties[product_cache['tag']] = list(temp)
				print node.properties[product_cache['tag']]
			else:
				# Create property
				node.properties[product_cache['tag']] = list(product_cache['value'])
				print node.properties[product_cache['tag']]
			# Add 'key' as label
			node.labels.add(label)
			node.push()
		else:
			# This means node doesn not exist, create and insert
			print 'Creating ' + url
			tmp = Node()
			tmp.properties[product_cache['tag']] = []
			tmp.properties[product_cache['tag']].append(product_cache['value'])
			tmp.properties['url'] = url
			tmp.labels.add(label)
			graph.create(tmp)

			# Call scrape function to scrape remaining data
			product_scrape(label,url)


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
							f.write('[' + str(datetime.now()) + '] ' + 'Label/Label count error' + '\n')
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
									f.write('[' + str(datetime.now()) + '] ' + 'Product url append error' + '\n')
									f.close()

							# Move to next page
							try:
								if paginate_index == 1:
									browser.find_element_by_xpath('//*[@id="js-filtered_items"]/div[1]/div/div[2]/div[2]/div/div/span/a').click()
									print 'Navigated to page 2'
									time.sleep(4)
								else:
									browser.find_element_by_xpath('//*[@id="js-filtered_items"]/div[1]/div/div[2]/div[2]/div/div/span[2]/a').click()
									print 'Navigated to next page '
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
							#### Database insertion logic goes here ####
							database_insert(key,product_cache)
							
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

# Graph init
graph = Graph("http://neo4j:test@localhost:7474/db/data")

# Base url
base_url = 'http://www.birdsnest.com.au/womens/'
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

#while scrape('accessories',scrape_list['accessories'][7]):
#	continue

for key in scrape_list:
	for k in scrape_list[key]:
		for e in scrape_exclude_list:
			if k == base_url + e:
				continue
			else:
				while scrape(key,k):
					continue
