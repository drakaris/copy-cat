from py2neo import Graph,Node,Relationship,watch
from lxml import html
import requests
import json

def outfit_write_to_db(metadata):
	global graph
	
	# Handle empty list values in metadata
	for m in metadata:
		if not metadata[m]:
			metadata[m].append('Null')

	data = Node.cast(metadata)
	data.labels.add("Outfits")
	watch("httpstream")
	try:
		graph.create(data)
	except:
		f = open("data_dump/error.log","a")
		f.write(metadata['url'] + '\n')
		f.close()

def outfit_scrape(url):
	# Data structure for scraped data
	metadata = {
		'name' : '',
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

	# Store outfit name
	name = domTree.xpath('//*[@id="js-container"]/div[2]/h1/text()')
	metadata['name'] = name[0].strip()

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
	#print metadata
	outfit_write_to_db(metadata)

	#global graph
	#data = Node.cast(metadata)

# Global Neo4j declaration
graph = Graph("http://neo4j:$haringan1208!@localhost:7474/db/data")

# Main program section
#f = open("data_dump/links.txt","r")
#file_contents = [data.rstrip('\n') for data in f]
#f.close()

#for url in file_contents:
#	print '[Scraping] ' + url
#	outfit_scrape(url)

outfit_scrape('http://www.birdsnest.com.au/womens/outfits/taking-care-of-business-1')