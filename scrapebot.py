import requests
import json
from lxml import html
from py2neo import Graph,Node,Relationship,watch

class scrapeBot:
	# Main class
	# Variable declaration
	base_url = 'http://www.birdsnest.com.au'
	graph = Graph("http://neo4j:test@localhost:7474/db/data")
	
	# Methods
	def __init__(self):
		# Area for NodeJs terminal dashboard

		# Try loading categories & filters
		if self.populate_categories():
			print 'Populating Categories'
			if self.populate_filters():
				print 'Populating Filters'
				#self.collect_outfits()
				self.collect_products()
			else:
				# Report error to dashboard
				print ''
		else:
			# Report error to dashboard
			print ''

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
				product_node = self.product_scrape(base_url + z)
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
		n_outfits = n[2]
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


# Check if file is executed directly
if __name__ == "__main__":
	x = scrapeBot()