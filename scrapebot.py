import requests
import json
from lxml import html
from py2neo import Graph,Node,Relationship,watch

class scrapeBot:
	# Main class
	# Variable declaration
	base_url = 'http://www.birdsnest.com.au'
	graph = Graph("http://neo4j:test@localhost:7474/db/data")
	endpoints = {}

	# Methods
	def __init__(self):
		# Area for NodeJs terminal dashboard

		# Try loading categories & filters
		if self.populate_categories():
			print '> Populating Categories'
			if self.populate_filters():
				print '> Populating Filters'
				print '> Cleaning Filters'
				self.cleanFilters()
				#self.collect_outfits()
				#self.collect_products()
				print '> Building Hierarchy'
				if self.buildHierarchy():
					# Traverse Hierarchy
					if self.traverseHierarchy():
						# Scrape Hierarchy
						self.scrapeHierarchy()
					else:
						# Report error to dashboard
						print '> Error traversing hierarchy'
				else:
					# Report error to dashboard
					print '> Error building hierarchy'
			else:
				# Report error to dashboard
				print '> Error loading filters'
		else:
			# Report error to dashboard
			print '> Error loading categories'

	def populate_categories(self):
		url_categories = 'http://www.birdsnest.com.au/api/v1/categories'
		self.categories = json.loads(requests.get(url_categories).text)
		if self.categories['head']['code'] == 200:
			return True
		else:
			return False

	def populate_filters(self):
		url_filters = 'http://www.birdsnest.com.au/api/v1/filters'
		self.filters = json.loads(requests.get(url_filters).text)
		if self.categories['head']['code'] == 200:
			return True
		else:
			return False

	def cleanFilters(self):
		junk = ['Brand','Gift Type','Level3','Price','Rating','Size','Status']

		for key in junk:
			if key in self.filters['body']:
				del self.filters['body'][key]

	def build_query(self,url,attribute,index):
		return url + '&' + attribute + '=' + str(index)

	def append_o(self,data):
		return str('o_' + str(data))

	def get_href(self,data,domTree):
		return str(self.base_url + domTree.xpath('//*[@id="%s"]/a/@href' % data)[0])

	def parse_outfits(self,outfit_data):
		# Load DOM tree
		domTree = html.fromstring(outfit_data['body']['objects'])

		# Iterate through outfit data
		for outfit in outfit_data['body']['outfits']:
			outfit['id'] = self.append_o(outfit['id'])
			outfit['href'] = self.get_href(outfit['id'],domTree)

			# Pass outfit to outfit scraper method
			print 'Scraping ' + outfit['name']
			self.outfit_scrape(outfit)

	def collect_outfits(self):
		# Query API for outfits
		url = 'http://www.birdsnest.com.au/womens/outfits?level=1513'
		# Request headers
		header = {
		'Accept' : 'application/json'
		}

		# Start while loop to iterate pages
		switch = 1
		# Variables for query building
		index = 1
		attribute = 'page'

		while switch:
			# Build query for page(s)
			print 'Building query'
			query = self.build_query(url,attribute,index)
			# Process query
			outfit_data = json.loads(requests.get(query,headers = header).text)

			# Load HTMl objects from outfit data
			if outfit_data['head']['code'] == 200:
				if len(outfit_data['body']['outfits']) > 0:
					print 'Parsing outfits'
					self.parse_outfits(outfit_data)
					index = index + 1
				else:
					switch = 0
			else:
				print ''

		print 'Done collecting outfits'

	def outfit_scrape(self,outfit):
	# Data structure for scraped data
		metadata = {
			'name' : '',
			'id' : '',
			'about' : '',
			'url' : '',
			'image' : '',
			'products' : [],
			'Boobs' : [],
			'Tummy' : [],
			'Hips' : [],
			'related_body_shapes' : [],
			'occasions' : [],
			'personalities' : [],
			'collections' : []
		}

		exclusion_list = ['','womens','shop-by','outfits']

		# Process data from outfit object
		metadata['id'] = outfit['id']
		metadata['name'] = outfit['name']
		url = outfit['href']

		r = requests.get(url)
		domTree = html.fromstring(r.content)

		tree = domTree.getroottree()

		about = list(set(domTree.xpath('//*[@id="tab0"]/text()')))
		for i in range(0,2):
			about[i] = about[i].strip()
		about.remove('')

		# Store outfit description
		metadata['about'] = about

		# Store outfit URL
		metadata['url'] = url

		# Store outfit image
		metadata['image'] = list(set(domTree.xpath('//*[@id="js-container"]/div[3]/div[1]//img/@src')))

		# Store contituent product data
		metadata['products'] = list(set(domTree.xpath('//div[@class="item_grid_member"]//a/@href')))

		body_data = domTree.xpath('//div[@class="input--circle checked"]')

		for e in body_data:
			body_part = 'string(' + tree.getpath(e.getparent().getparent().getparent().getparent().getprevious()) + ')'
			body_part =  domTree.xpath(body_part).strip()
			tag = 'string(' + tree.getpath(e.getnext()) + ')'
			tag =  domTree.xpath(tag).strip()
			metadata[body_part].append(tag)

		# Get all hyperlinks present in 'tab1' for processing
		href = domTree.xpath('//div[@id="tab1"]//a/@href')

		# Process href for additional metadata
		for link in href:
			#print link
			link_digested = link.split('/')
			for x in exclusion_list:
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

		# Write metadata to graph
		self.outfit_write(metadata)

	def outfit_write(self,metadata):

		# Handle empty list values in metadata
		for m in metadata:
			if not metadata[m]:
				metadata[m].append('Null')

		data = Node.cast(metadata)
		data.labels.add("Outfits")
		watch("httpstream")
		try:
			self.graph.create(data)
		except:
			f = open("outfit_error.log","a")
			f.write(metadata['url'] + '\n')
			f.close()

	# Product data extraction method
	def product_details(self,outfit_node):
		watch("httpstream")
		print '[Exploring] ' + outfit_node.properties['name']
		for z in outfit_node.properties['products']:
			# Check for product node in db
			t = self.graph.find_one('Products','url',self.base_url + z)
			if t:
				check = self.graph.match_one(outfit_node,'HAS',t)
				if check:
					continue
				else:
					rel = Relationship(outfit_node, "HAS", t)
					self.graph.create(rel)
			else:
				# Generate product node, pass url for scrape, returns graph node
				product_node = self.product_scrape(self.base_url + z)
				rel = Relationship(outfit_node, "HAS", product_node)
				self.graph.create(rel)

	# Product scrape method
	def product_scrape(self,x):
		# Accepts URL returns graph node
		# Data structure schema
		metadata = {
		'name' : '',
		'brand' : '',
		'price' : '',
		'url' : '',
		'image' : [],
		'about' : [],
		'features' : [],
		'tags' : [],
		'Boobs' : [],
		'Tummy' : [],
		'Hips' : [],
		'occasions' : [],
		'collections' : [],
		'personalities' : [],
		'related_body_shapes' : [],
		'related_outfits_count' : ''
		}

		exclusion_list = {
		'p' : ['','Style code:'],
		'a' : ['','womens','shop-by','outfits']
		}

		# Load product page
		r = requests.get(x)

		# Construct DOM trees
		domTree = html.fromstring(r.content)
		tree = domTree.getroottree()

		# Extract product name
		name = domTree.xpath('//*[@id="js-item_middle"]/h5/text()')
		print name[0].strip()
		metadata['name'] = name[0].strip()

		# Extract product ID from URL
		id_data = x.split('/')
		id_data = id_data[len(id_data) - 1].split('-')[0]
		print '\t> ID: ' + id_data
		metadata['id'] = int(id_data)

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
		metadata['features'] = features

		# Extract product tags
		tags = list(set(domTree.xpath('//*[@id="tab0"]/div[3]//a/text()')))
		for i in range(0,len(tags)):
			tags[i] = tags[i].strip()
		print '\t> Tag(s): ' + str(len(tags))
		metadata['tags'] = tags

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

		# Cast metadata to node
		node = Node.cast(metadata)
		node.labels.add('Products')

		# Return node
		return node

	def collect_products(self):
		for x in self.graph.find('Outfits'):
			# Pass graph node as x
			self.product_details(x)

	def buildHierarchy(self):
		self.hierarchy = {}

		applicable_categories = {
		'0' : '1516',
		'1' : '1661'
		}

		for key in applicable_categories:
			data = applicable_categories[key]
			self.hierarchy['%s' % data] = self.categories['body']['hierarchy'][0]['1513'][int(key)]['%s' % data]
		#print self.hierarchy
		return True

	def buildEndpoints(self,key):
		keyName = self.getKeyName(int(key)).lower()
		self.endpoints[keyName] = self.base_url + '/womens/%s?' % keyName

	def getKeyName(self,key):
		for category in self.categories['body']['categories']:
			if category['id'] == key:
				return category['name']

	def traverseHierarchy(self):
		# Start traversing hierarchy
		for key in self.hierarchy:
			for k in self.hierarchy[key]:
				 # Build endpoints
				 self.buildEndpoints(k.keys()[0])
		return True

	def scrapeHierarchy(self):
		# Scrape Hierarchy
		switch = 1
		for key in self.hierarchy:
			label = self.getKeyName(int(key))
			for k in self.hierarchy[key]:
				type = self.getKeyName(int(k.keys()[0]))
				self.processHierarchy(label,key,type,k.keys()[0])

	def formatFilters(self,filters):
		# Temporary structures
		updatedFilters = []
		filters_keys = filters.keys()
		# Iterate through filter list
		for key in self.filters['body'].keys():
			for filter in self.filters['body'][key]:
				if str(filter['id']) in filters_keys and filters[str(filter['id'])] != 0:
					x = {}
					x['name'] = filter['name']
					x['id'] = filter['id']
					x['type'] = key
					x['amount'] = filters[str(filter['id'])]
					updatedFilters.append(x)
		return updatedFilters

	def processHierarchy(self,label,label_key,type,type_key):
		# Get endpoint for type
		endpoint = self.endpoints[type.lower()]
		level_id = type_key
		page = 1
		header = {
		'Accept' : 'application/json'
		}

		# Add attributes to endpoint
		endpoint = endpoint + 'level_id=' + level_id
		# Request endpoints without any filters
		data = json.loads(requests.get(endpoint + '&page=' + str(page), headers = header).text)
		# Format and clean returned filters
		formattedFilters = self.formatFilters(data['body']['filters'])
		# Apply filters for new item list
		for filter in formattedFilters:
			print endpoint
			self.deepScrape(endpoint,filter['id'],filter['name'],filter['type'],label,type)

	def updateProductNode(self,node,filter_type,filter_name,type):
		if node.properties[filter_type]:
			node.properties[filter_type].append(filter_name)
		else:
			node.properties[filter_type] = []
			node.properties[filter_type].append(filter_name)
		if node.properties['sub_category']:
			node.properties['sub_category'] = type
		else:
			node.properties['sub_category'] = []
			node.properties['sub_category'].append(type)
		# Return updated node
		return node

	def deepScrape(self,endpoint,filter_id,filter_name,filter_type,label,type):
		# Single filter is applied, scrape associated data only
		watch("httpstream")
		page = 1
		header = {
		'Accept' : 'application/json'
		}
		print 'Applying filter : ' + filter_name
		while True:
			endpoint = endpoint + '&filters=' + str(filter_id) + '&page=' + str(page)
			# Query endpoint
			data = json.loads(requests.get(endpoint, headers = header).text)
			# Scrape and paginate through results
			print 'Page [%d/%d]' % (page,data['body']['counts']['pages'])
			# Check if product exists based on id
			for item in data['body']['catalogue_items']:
				z = self.graph.find_one('Products','id',int(item['item_id']))
				if z:
					# Product exists, insert only filters
					print 'Updating product : %d' % item['item_id']
					node = self.updateProductNode(z,filter_type,filter_name,type)
					print 'Applying label : %s' % label
					node.labels.add(label)
					self.graph.create(node)
				else:
					# Product doesn't exist, scrape and then insert filters
					print 'Scraping item : %d' % item['item_id']
					node = self.product_scrape(self.base_url + item['link'])
					node = self.updateProductNode(node,filter_type,filter_name,type)
					print 'Applying label : %s' % label
					node.labels.add(label)
					self.graph.create(node)

			# Pagination condition check
			if page < data['body']['counts']['pages']:
				page = page + 1
				continue
			else:
				break


# Check if file is executed directly
if __name__ == "__main__":
	x = scrapeBot()
