import SocketServer
import MySQLdb
import urllib
import urllib2
import socket
import os
import subprocess
import datetime
import re

from urlparse import urlparse
from HTMLParser import HTMLParser
from BeautifulSoup import BeautifulSoup
from google import search


def main():
	#dbConn("SELECT VERSION()")
	score = 0;
	protocol = "http"
	domain = "wellsfargo.com"
	url = "http://wellsfargo.com"
	#geting ip of the domain
	ip = socket.gethostbyname(domain)
	print "IP: " + ip

	#getting fingerprint of the domain
	user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1309.0 Safari/537.17)" # Or any valid user agent from a real browser
	headers = {"User-Agent": user_agent}
	req = urllib2.Request(url, headers=headers)
	res = urllib2.urlopen(req)
	soup = BeautifulSoup(res)

	title = approach4_getTitle(soup, headers)
	numImg = approach4_getNumOfImg(soup, headers)
	sizeCSS = approach4_getSizeOfCSS(soup, headers) #size of css
	password = approach4_getSizeOfPasswordField(soup, headers) #size + maxlength

	if lookupInBlackList(domain): #Looking for the domain in blacklist
		print "The request domain is already existed"
		print "Phishing webiste"
	elif lookupInWhiteList(numImg,sizeCSS,title, password): #Looking for the fingerprint in whitelist
		print "Domain exists in whitelist"
	else:
		print "Do our approaches"
		#score += approach1(protocol)
		#score += approach2(ip)
		#score += approach3(domain, 10)
		
		# score += approach5(domain)
		# approach6(domain)
		
		print "(main) total score: " + str(score)
		print "Insert the result to DB"
		#insertRecord(domain, score)

	return


def insertRecord(domain, score):
	sql = "INSERT INTO phishing (domain,score) VALUES (\"" + domain + "\",\"" + str(score) + "\")"
	dbConn(sql)
	return

def insertRecordToWhitelist(numImage, sizeCSS, title, password):
	con = MySQLdb.connect(host = "172.16.59.129", user = "dw", passwd = "asdf", db = "phishing")
	cursor = con.cursor()
	cursor.execute("""INSERT INTO whitelist (num_image, size_css, title, password) VALUES (%s,%s,%s,%s)""", (str(numImage) ,str(sizeCSS), title, str(password)))
	con.commit()
	con.close()

def lookupInBlackList(domain):
	con = MySQLdb.connect(host = "172.16.59.129", user = "dw", passwd = "asdf", db = "phishing")
	cursor = con.cursor()
	cursor.execute("""SELECT * FROM blacklist WHERE domain = %s""", domain)
	row = cursor.fetchone()

	if row is None:
		return False

	print "Result: " + str(tuple(row)) #result
	
	cursor.close()
	con.close()
	
	return True

def lookupInWhiteList(numImage, sizeCSS, title, password):
	con = MySQLdb.connect(host = "172.16.59.129", user = "dw", passwd = "asdf", db = "phishing")
	cursor = con.cursor()
	cursor.execute("""SELECT * FROM whitelist WHERE num_image = %s AND size_css = %s AND title = %s AND password = %s""", (str(numImage) ,str(sizeCSS), title, str(password)))
	row = cursor.fetchone()

	if row is None:
		return False

	print "Result: " + str(tuple(row)) #result
	
	cursor.close()
	con.close()
	
	return True

"""
check if the ssl is established
"""
def approach1(protocol):
	if protocol == "http":
		print "(Approach1) ssl is not established " + "\t\t +1"
		return 1
	
	return 0

"""
Location of IP
It uses ipinfodb
"""
def approach2(ip):
	url = "http://api.ipinfodb.com/v3/ip-city/?key=476453055e1d18ce2238f38f310cd99a138e995bece3fcf692666de6bb5f9438&ip=" + ip
	response = urllib.urlopen(url).read()
	tokens = response.split(";")
	print "(Approach2) IP locates in " + tokens[3]
	print "(Approach2) IP locates in " + tokens[4]

	if tokens[3] != "US" and tokens[4] != "UNITED STATES":
		print "(Approach2) +1"
		return 1
	else:
		return 0

"""
Check if the domain has many servers
"""
def approach3(domain, num):
	score = 0;
	ip = socket.gethostbyname(domain)
	i = 0
	for i in range(num):
		ip2 = socket.gethostbyname(domain)
		print ip
		if ip == ip2:
			score += 1
		ip = ip2

	if score >= (num * 0.8):
		print "(Approach3) it has only one server \t\t +1"
		return 1
	else:
		return 0

"""
Fingerprint of url

def approach4(url):

	user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1309.0 Safari/537.17)" # Or any valid user agent from a real browser
	headers = {"User-Agent": user_agent}
	req = urllib2.Request(url, headers=headers)
	res = urllib2.urlopen(req)
	soup = BeautifulSoup(res)
	
	title = approach4_getTitle(soup)
	numImg = approach4_getNumOfImg(soup)
	size = approach4_getSizeOfCSS(soup) #size of css
	total = approach4_getSizeOfPasswordField(soup) #size + maxlength

	# insertRecordToWhitelist(numImg, size, title, total)

	return
"""

"""
To get title of html
"""
def approach4_getTitle(soup, headers):
	title = soup.title.string
	print "Title: ", title
	
	return title

"""
To get number of images in html
"""
def approach4_getNumOfImg(soup, headers):
	lists = soup.findAll('img')
	numImage = len(lists)
	print "The number of images:" , len(lists)

	return len(lists)

"""
To get size of CSS in html
"""
def approach4_getSizeOfCSS(soup, headers):
	#size of css
	size = 0
	for css in soup.findAll('link'):
		if css.has_key('rel') and css.has_key('type'):
			if 'stylesheet' == css['rel'] and 'text/css' == css['type']:
				link = css['href']
				parsedUrl = urlparse(link)
				if parsedUrl.scheme is not '' :
					res = urllib2.urlopen(urllib2.Request(link, headers=headers))
					cssSoup = BeautifulSoup(res)
					size  += len(cssSoup.text)
				else:
					if parsedUrl.netloc is not '':
						addr = 'http://' + parsedUrl.netloc + parsedUrl.path
					else:
						addr = url + parsedUrl.path
					print addr
					res = urllib2.urlopen(urllib2.Request(addr, headers=headers))
					cssSoup = BeautifulSoup(res)
					size  += len(cssSoup.text)
	
	print "Size of CSS: " + str(size)

	return size

"""
To get size + maxlength of password field
"""
def approach4_getSizeOfPasswordField(soup, headers):
	total = 0
	lists = soup.findAll('input',{'type':"password"})
	if len(lists) > 0:
		if lists[0].has_key('size'):
			total += int(lists[0]['size'])
		if lists[0].has_key('maxlength'):
			total += int(lists[0]['maxlength'])
		print "Size + maxlength: " + str(total)

	return total

"""
google search
reference: https://github.com/MarioVilas/google/blob/master/google.py

"""
def approach5(domain):
	keyword = "\"" + domain + "\""
	for url in search(keyword, stop=1):
		url2 = url.split("://")
		url2[1] = url2[1].replace('/','',1)
		print url2[1] + " " + domain
		if url2 is not domain:
			return 1
	else:
		return 0

"""
whois kbstratr.com | grep -i "Creation Date"
"""
def approach6(domain):
	now = datetime.datetime.now()
	# exe = "whois " + domain + "| grep -i \"Creation Date\""
	exe = "whois kbstratr.com | grep -i \"Creation Date\""
	p = subprocess.Popen(exe, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	lines = p.stdout.readlines()
	#retval = p.wait()
	line = lines[0]
	tokens = line.split()
	date = tokens[2].split("-")
	print "(Approach6) This domain was regsitered in " + date[2]

	if str(now.year) == date[2]:
		return 1
	
	return 0 

# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
	def __init__(self, *args, **kwargs):
		HTMLParser.HTMLParser.__init__(self, *args, **kwargs)
		self.title = False
	
	def handle_starttag(self, tag, attrs):
		if tag == "title":
			self.title = True
			print "Encountered a start tag:", tag

	def handle_endtag(self, tag):
		if tag == "title":
			self.title = False
			print "Encountered an end tag :", tag

	def handle_data(self, data):
		if self.title:
			print "Encountered some data  :", data

if __name__ == "__main__":
    main()