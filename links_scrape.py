import time
from selenium import webdriver

# Helper methods
def outfit_data_iterator(outfits):
	for data in outfits:
		outfit_div_extract(data)
	return 0

def outfit_div_extract(data):
	link = data.find_element_by_tag_name('a').get_attribute('href')
	name = data.find_element_by_tag_name('p').text
	print name + ' > ' + link
	
	f = open("links.txt","a")
	f.write(link + '\n')
	f.close
	return 0

# Logic control variables
paginate_index = 1

# Initiate Firefox driver
browser = webdriver.Firefox()

# Set wait limit for page load
browser.implicitly_wait(15)

# Load target page
browser.get("http://www.birdsnest.com.au/womens/outfits")

# Change mode to paginated results
browser.find_element_by_xpath('//*[@id="js-filtered_items"]/div[1]/div/div[2]/div[1]/div/ul/li[2]/a').click()

# Retrieve outfit urls
print 'Page : ' + '[' + str(paginate_index) + ']'
data_iterator(browser.find_elements_by_class_name('outfit'))

# Perform pagination
while(1):
	try:
		if paginate_index == 1:
			browser.find_element_by_xpath('//*[@id="js-filtered_items"]/div[1]/div/div[2]/div[2]/div/div/span/a').click()
		else:
			browser.find_element_by_xpath('//*[@id="js-filtered_items"]/div[1]/div/div[2]/div[2]/div/div/span[2]/a').click()
			
	except:
		print "End of pages"
		break
	else:
		paginate_index = paginate_index + 1
		print 'Page : ' + '[' + str(paginate_index) + ']'
		time.sleep(2)
		outfit_data_iterator(browser.find_elements_by_class_name('outfit'))

# Quit browser
browser.quit()