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
			if self.populate_filters():
				self.collect_outfits()
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
			outfit_scrape(outfit)

	def collect_outfits(self):
		# Query API for outfits
		url = 'http://www.birdsnest.com.au/womens/outfits?level=1513'
		# Request headers
		header = {
		'Accept' : 'application/json'
		}
		# Variables for query building
		index = 1
		attribute = 'page'
		# Build query for page(s)
		query = self.build_query(url,attribute,index)
		# Process query
		outfit_data = json.loads(requests.get(query,headers = header).text)

		# Load HTMl objects from outfit data
		if outfit_data['head']['code'] == 200:
			self.parse_outfits(outfit_data)
		else:
			print ''

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




# Check if file is executed directly
if __name__ == "__main__":
	x = scrapeBot()