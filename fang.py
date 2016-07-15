#!/usr/bin/python
# This file is part of Fang.
#
# Copyright(c) 2010-2011 Simone Margaritelli
# evilsocket@gmail.com
# http://www.evilsocket.net
#
# This file may be licensed under the terms of of the
# GNU General Public License Version 2 (the ``GPL'').
#
# Software distributed under the License is distributed
# on an ``AS IS'' basis, WITHOUT WARRANTY OF ANY KIND, either
# express or implied. See the GPL for the specific language
# governing rights and limitations.
#
# You should have received a copy of the GPL along with this
# program. If not, go to http://www.gnu.org/licenses/gpl.html
# or write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

import getopt, sys, os, urllib, urllib2, re, urlparse, os, threading, signal
from optparse import OptionParser, OptionGroup 

class Service(threading.Thread):
	def __init__ ( self, type, url, regex, exit_on_match, hash ):
		threading.Thread.__init__(self)
		
		self.type  		     = type
		self.url   		     = url
		self.hash		       = hash if hash != None else ""
		self.regex 		     = regex.replace( '{HASH}', self.hash )
		self.args  		     = {}
		self.name  		     = urlparse.urlparse(url)[1]
		self.exit_on_match = exit_on_match
		
		if self.type == 'POST':
			self.args = self.__parseArgs()
			
	def run( self ):	
		global cracked
		
		cleartext = self.__crack(self.hash)
		if cleartext != None:
			print "!!!\tThe plaintext of %s is '%s' (found on %s)" % ( self.hash, cleartext, self.name )
			if self.exit_on_match == True:
				os.kill( os.getpid(), signal.SIGTERM )
			
	def __crack( self, hash ):
		data = ''
		try:
			if self.type == 'GET':
				url  = self.url.replace( '{HASH}', hash )
				data = self.__exec_get(url) 
			else:
				url  = self.url.replace( '{HASH}', hash )	
				args = self.args
				for name,value in args.iteritems():
					args[name] = value.replace( '{HASH}', hash )
				data = self.__exec_post(url,args)		
		except:
			pass
			
		return self.__xtract_data(data)
			
	def __xtract_data( self, data ):
		m = re.search( self.regex, data )
		return m.group(1) if m is not None else None
		
	def __exec_get( self, url ):
		headers = {'User-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:33.0) Gecko/20100101 Firefox/35.0'}	
		return urllib2.urlopen(urllib2.Request(url, None, headers)).read()
		
	def __exec_post( self, url, data ):
		headers = {'User-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:33.0) Gecko/20100101 Firefox/35.0'}
		return urllib2.urlopen(urllib2.Request(url, urllib.urlencode(data), headers)).read()
			
	def __parseArgs( self ):
		m = re.search( "([^\[]+)\[([^\]]+)\]", self.url )
		self.url = m.group(1)
		params   = m.group(2)
		params	 = params.split(',')
		args	 = {}
		
		for param in params:
			(k,v) = param.split(':')
			args[k] = v
			
		return args

try:
	print "\n\tFang 1.2 - A multi service threaded Hash cracker.\n \
\tCopyleft Simone Margaritelli <evilsocket@gmail.com>\n \
\thttp://www.evilsocket.net\n\thttp://www.backbox.org\n";
               
	parser = OptionParser( usage = "usage: %prog [options] [--hash <hash>]\n\n" +
                                   "EXAMPLES:\n" +
                                   "  %prog --hash 7815696ecbf1c96e6894b779456d330e\n" +
                                   "  %prog --threads 10 --exit-first --hash 7815696ecbf1c96e6894b779456d330e\n" +
                                   "  %prog --input hashlist.txt\n" +
                                   "  %prog --list" )

	parser.add_option( "-H", "--hash",       action="store", 	    dest="hash",		      default=None,  help="The hash to crack, mandatory." )
	parser.add_option( "-t", "--threads",    action="store", 	    dest="threads",       default=10,    help="Specify how many threads to use, default 10." )
	parser.add_option( "-e", "--exit-first", action="store_true", dest="exit_on_first", default=False, help="Stop execution upon first positive match." )
	parser.add_option( "-i", "--input",      action="store",      dest="input",         default=None,  help="Read a list of hashes from the given file." )
	parser.add_option( "-p", "--proxy",	 action="store", 	dest ="proxy", default=None,help="Define a proxy (default: None)")

	(o,args) = parser.parse_args()
    
	conf     = open( "fang.conf", "rt" ) 
	services = []
	hashes   = []
	if o.proxy!= None:
		# define proxy stuff
		proxy = urllib2.ProxyHandler({'http': str(o.proxy)})
		opener = urllib2.build_opener(proxy)
		opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:33.0) Gecko/20100101 Firefox/35.0')]
		opener.addheaders = [('Content-Type', 'text/plain')]
		urllib2.install_opener(opener)
	else:
		pass
	if o.input != None:
		o.exit_on_first = False
		hashlist 				= open( o.input, "rt" ) 
		for line in hashlist:
			md5 = line.rstrip()
			if md5 != '':
				hashes.append(md5)		
				
	elif o.hash != None:
		hashes.append( o.hash )
		
	else:
		parser.error( "No hash specified!" )

	for line in conf:
		( type, url, regex ) = line.rstrip().split('|')
		for md5_hash in hashes:
			services.append( Service( type, url, regex, o.exit_on_first, md5_hash ) )
				
	conf.close()

	i = 0
	for si, service in enumerate(services):	
		print "Searching for '%s' on %s ..." % ( service.hash, service.name )
		service.start()
		i += 1
		if i >= o.threads or si >= len(services):
			service.join()
			i = 0
				
except IOError as e:
	print e
except:
	raise
