from py2neo import Graph,Node,Relationship,watch
from lxml import html
import requests

# Product scrape method
def product_scrape(x):
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

# Product data extraction method
def product_details(outfit_node):
	global graph
	
	print '[Exploring] ' + outfit_node.properties['name']
	for z in outfit_node.properties['products']:
		# Check for product node in db
		t = graph.find_one('Products','url',base_url + z)
		if t:
			check = graph.match_one(outfit_node,'HAS',t)
			if check:
				continue
			else:
				rel = Relationship(outfit_node, "HAS", t)
				graph.create(rel)
		else:
			# Generate product node, pass url for scrape, returns graph node
			product_node = product_scrape(base_url + z)
			rel = Relationship(outfit_node, "HAS", product_node)
			graph.create(rel)

# Global variables
graph = Graph("http://neo4j:$haringan1208!@localhost:7474/db/data")
base_url = 'http://www.birdsnest.com.au'

# Main program logic
watch('httpstream')
print 'test'

for x in graph.find('Outfits'):
	# Pass graph node as x
	product_details(x)