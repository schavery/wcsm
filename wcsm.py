"""
wcsm stands for Web Change Stop Motion
This script is designed to watch your directory for file modifications
and will then make a request to the uris you define to save those modifications
to html files.
Then, once you've done your work and saved a bunch of flat files, you can
render these captures as images and then stitch them together with ffmpeg
to create a little movie of the creation of a website!

Summer 2014
Steve Avery
MIT license.
"""

import argparse
import base64
import hashlib
import imghdr
import os
import re
import sys
import time
import urllib3
import urlparse
from bs4 import BeautifulSoup
from os import path as op
from watchdog.events import RegexMatchingEventHandler
from watchdog.observers import Observer

# TODOS:

# pip it
# logs
# some changes are invisible; want to throw these away


# output dir structure
# <outdir>
#		/uri[0]
#			/time0.html
#			/time1.html
#			...
#		/uri[1]
#			...
#		...


class WebGetter(object):
	def __init__(self, options):
		# set up debounce interval in millis
		# might need fine tuning for different applications
		self.debounce_interval = 1000
		self.thistime = 0
		self.lasttime = 0

		# no duplicate uris
		uniqueset = set(options.fetch)
		self.urilist = list(uniqueset)

		# find or create directories for output
		self.outdirname = op.abspath(options.output)
		for uri in self.urilist:
			name = self.pathfromuri(uri)
			outpath = op.normpath(self.outdirname + '/' + name)
			if not op.exists(outpath):
				os.makedirs(outpath)

		# prepare urls for fetching.
		self.http = urllib3.PoolManager()

		for uri in self.urilist:
			req = self.http.request('GET', uri)
			if req.status != 200:
				raise RunTimeError('Net error:\nStatus: ' + req.status + '\n' \
									 + 'Requested URI: ' + uri)

		# are we good to go now?
		print 'Ready to watch...'


	def pathfromuri(self, uri):
		""" transform the uri into a simple directory name """
		address = urlparse.urlparse(uri)
		base = address.netloc

		if address.path != '':
			path = re.sub('/', '_', address.path)
			base += path

		if address.query != '':
			query = re.sub('&', '-', address.query)
			base += '+' + query

		return base


	def grab(self):
		if self.debounce():
			name = str(time.time()).split('.')[0] + '.html'
			for uri in self.urilist:
				basepath = op.normpath(self.outdirname + '/' + self.pathfromuri(uri)  + '/')

				req = self.http.request('GET', uri)
				flat = str(self.inline(req.data, uri))

				# if the file is exactly the same, don't save it again
				thishash = hashlib.md5(flat).hexdigest()
				oldfiles = os.listdir(basepath)
				goahead = False
				if len(oldfiles) > 0:
					oldfiles.sort()
					mostrecent = oldfiles[-1]
					fcontents = open(op.normpath(basepath + '/' + mostrecent), 'r')
					pasthash = hashlib.md5(fcontents.read()).hexdigest()
					if pasthash != thishash:
						goahead = True
				else:
					# no files exist yet
					goahead = True

				if goahead:
					uridir = self.pathfromuri(uri)
					path = self.outdirname + '/' + uridir + '/' + name
					fhandle = open(op.normpath(path), 'w')
					fhandle.write(flat)
					fhandle.close()


	def debounce(self):
		"""don't go fetching pages too frequently"""
		self.thistime = int(time.time() * 1000)
		if (self.thistime - self.lasttime) > self.debounce_interval:
			self.lasttime = self.thistime
			return True
		else:
			return False


	def inline(self, htmldata, uri):
		"""	make the output files much more manageable
			deficiencies to address are:
			images hosted elsewhere - become base64 encoded and embedded
			stylesheets likewise hosted elsewhere - change to style and embedded
		"""
		soup = BeautifulSoup(htmldata)

		imglist = soup.select('img')
		for img in imglist:
			if hasattr(img, 'src'):
				ref = img['src']
				srcuri = urlparse.urlparse(ref)

				# test for data uri already
				if srcuri.scheme == 'data':
					continue

				imgraw = self.getexternalresource(ref, uri)
				imgtype = imghdr.what('ignored', imgraw)
				img64 = base64.b64encode(imgraw)
				img['src'] = 'data:image/' + imgtype + ';base64,' + img64


		linklist = soup.select('link[rel="stylesheet"]')
		for link in linklist:
			if hasattr(link, 'href'):
				ref = link['href']
				styles = self.getexternalresource(ref, uri)

				del link['rel']
				del link['href']

				link.name = 'style'
				link.string = styles
				link['type'] = 'text/css'


		# get the scripts coming from this domain only
		# we don't care about external libraries
		domain = urlparse.urlparse(uri).netloc
		scriptlist = soup.select('script')
		for script in scriptlist:
			if hasattr(script, 'src'):
				ref = script['src']
				parsedref = urlparse.urlparse(ref)
				if domain == parsedref.netloc or \
					parsedref.netloc == '':
					scriptcontents = self.getexternalresource(ref, uri)

					del script['src']
					script.string = scriptcontents

		return soup


	def getexternalresource(self, path, uri):
		"""handle arbitrary paths, and return the resource data"""
		absolute = urlparse.urljoin(uri, path)
		req = self.http.request('GET', absolute)
		if req.status == 200 or req.status == 304: # xxx
			return req.data



class EventHandler(RegexMatchingEventHandler):
	def __init__(self, wg, options):
		super(EventHandler, self).__init__(options.regex)
		self.ignore = op.abspath(options.output)
		self.webgetter = wg


	def on_any_event(self, event):
		# don't do anything for events that are in the output dir
		emittedpath = op.split(event.src_path)
		while len(emittedpath[0]) >= len(self.ignore):
			if emittedpath[0] != self.ignore:
				emittedpath = op.split(emittedpath[0])
			else:
				return

		self.webgetter.grab()



if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Capture updates to a web site as you edit the files.',
										epilog='Consider using a & after the command to run it in the background. \
												Example: python ' + sys.argv[0] + ' <uri> &')

	parser.add_argument('-i', '--input', metavar='<dir>', default=os.getcwd(),
						help='The directory to watch for file changes. Defaults to PWD')
	parser.add_argument('-o', '--output', metavar='<dir>', default=op.normpath(os.getcwd() + '/wcsm'),
						help='Output dir for the generated files. Defaults to ./wcsm')
	parser.add_argument('-r', '--regex', metavar='<regex>', nargs='+', default=[r".*\.(css|js|html|rb|php)$"],
						help='Add a regex, or list of regexes, to match files to watch for changes. \
								Defaults to \".*\\.(css|js|html|rb|php)$\"')
	parser.add_argument('fetch', metavar='<uri>', nargs='+',
						help='Add uris to fetch changes from.')

	args = parser.parse_args()


	webgetter = WebGetter(args)
	eventh = EventHandler(webgetter, args)

	observer = Observer()
	observer.schedule(eventh, op.abspath(args.input), recursive=True)
	observer.start()

	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		print '\nCleaning up...'
		observer.stop()

	observer.join()

