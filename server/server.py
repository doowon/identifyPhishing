import SocketServer
import MySQLdb
import urllib
import urllib2
import socket
import os
import subprocess
import datetime
import re
import tornado.ioloop
import tornado.web

from urlparse import urlparse
from HTMLParser import HTMLParser
from BeautifulSoup import BeautifulSoup
from google import search


class MainHandler(tornado.web.RequestHandler):
	def post(self):
		score = self.get_argument('score','')
		url = self.get_argument('url','')
		if url == "about:blank":
			self.write(score)
		else:
			print "URL: " + url + ", Score: " + score
			retScore = main(url, int(score))
			print "Return Score: " + str(retScore)
			self.write(str(retScore))
			print "Server is listening....."

application = tornado.web.Application([
	(r"/", MainHandler),
])

def main(url, pScore):
	score = pScore;
	parsedUrl = urlparse(url)
	print parsedUrl
	protocol = parsedUrl.scheme
	domain = parsedUrl.netloc
	# protocol = "http"
	# domain = "wellsfargo.com"
	# url = "http://wellsfargo.com"
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
	sizeCSS = approach4_getSizeOfCSS(domain, soup, headers) #size of css
	password = approach4_getSizeOfPasswordField(soup, headers) #size + maxlength

	if lookupInBlackList(url): #Looking for the domain in blacklist
		score += 20;
		print "The request domain is already existed"
		print "Phishing webiste"
	elif lookupInWhiteList(domain, numImg,sizeCSS,title, password): #Looking for the fingerprint in whitelist
		score += 10
		print "Domain exists in whitelist"
	else:
		print "Do our approaches"
		score += approach1(protocol)
		score += approach2(ip)
		score += approach3(domain, 3)
		
		score += approach5(domain)
		score += approach6(domain)
		
		print "(main) total score: " + str(score)
		# print "Insert the result to DB"
		#insertRecord(domain, score)

	return score


def insertRecord(domain, score):
	sql = "INSERT INTO phishing (domain,score) VALUES (\"" + domain + "\",\"" + str(score) + "\")"
	dbConn(sql)
	return

def insertRecordToWhitelist(domain, numImage, sizeCSS, title, password):
	con = MySQLdb.connect(host = "172.16.59.129", user = "dw", passwd = "asdf", db = "phishing")
	cursor = con.cursor()
	cursor.execute("""INSERT INTO whitelist (num_image, size_css, title, password) VALUES (%s,%s,%s,%s)""", (str(numImage) ,str(sizeCSS), title, str(password)))
	con.commit()
	con.close()

def lookupInBlackList(domain):
	con = MySQLdb.connect(host = "172.16.59.129", user = "dw", passwd = "asdf", db = "phishing")
	cursor = con.cursor()
	cursor.execute("""SELECT * FROM blacklist WHERE domain = %s""", domain)
	print domain
	row = cursor.fetchone()

	if row is None:
		return False

	print "Result: " + str(tuple(row)) #result
	
	cursor.close()
	con.close()
	
	return True

def lookupInWhiteList(domain, numImage, sizeCSS, title, password):
	con = MySQLdb.connect(host = "172.16.59.129", user = "dw", passwd = "asdf", db = "phishing")
	cursor = con.cursor()
	cursor.execute("""SELECT * FROM whitelist WHERE num_image = %s AND size_css = %s AND title = %s AND password = %s""", (str(numImage) ,str(sizeCSS), title, str(password)))
	row = cursor.fetchone()

	if row is None:
		print "Not exists"
		return False

	# print "Result: " + str(tuple(row)) #result
	# print tuple(row)[5] , domain
	tmpDomain = "www."
	tmpDomain += tuple(row)[5]
	# print tmpDomain
	if (tuple(row)[5] == domain) or (tmpDomain == domain):
		return False

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
	domain = domain.replace("www.","")
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
def approach4_getSizeOfCSS(domain, soup, headers):
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
						addr = 'http://' + domain + parsedUrl.path
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
		# url2[1] = url2[1].replace('/','',1)
		print "(approach5) " + url2[1] + " " + domain
		if domain.find("www.") != -1:
			if url2[1] != domain: 
				print "google search +1"
				return 1
			else:
				return 0
		else:
			if url2[1] != "www." + domain:
				print "google search +1"
				return 1
			else:
				return 0


"""
whois kbstratr.com | grep -i "Creation Date"
"""
def approach6(domain):
	now = datetime.datetime.now()
	domain = domain.replace("www.","")
	# exe = "whois " + domain + "| grep -i \"Creation Date\""
	exe = "whois "+ domain + " | grep -i \"Creation Date\""
	print exe
	p = subprocess.Popen(exe, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	lines = p.stdout.readlines()
	retval = p.wait()
	print lines
	if len(lines) > 0:
		line = lines[0]
		tokens = line.split()
		date = tokens[2].split("-")

		print "(Approach6) This domain was regsitered in " + date[2]

		if str(now.year) == date[2]:
			print "(Approach6) This domain was regsitered in this year"
			return 1
	
	return 0 

if __name__ == "__main__":
	print "Server is listening....."
	application.listen(8888)
	tornado.ioloop.IOLoop.instance().start()
	# main("https://www.facebook.com",0)