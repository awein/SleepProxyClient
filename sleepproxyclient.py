#
# This file is part of SleepProxyClient.
#
# @license   http://www.gnu.org/licenses/gpl.html GPL Version 3
# @author    Andreas Weinlein <andreas.dev@weinlein.info>
# @copyright Copyright (c) 2012 Andreas Weinlein
#
# SleepProxyClient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# SleepProxyClient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SleepProxyClient. If not, see <http://www.gnu.org/licenses/>.

import dns.update
import dns.query
import dns.rdtypes
import dns.rdata
import dns.edns
import dns.rrset
from dns.exception import DNSException

import argparse
import struct
import sys
import subprocess
import netifaces
import socket

#
#	A Python Wake On Demand client implementation (SleepProxyClient)
#


# The device-model to send (_device-info._tcp.local).
# can be overwritten by specifying the corresponding argument!
DEVICE_MODEL = "RackMac"

# TTL for sleep client.
# A Wake-On-Lan-Packet will be sent after this period.
# can be overwritten by specifying the corresponding argument!
TTL_long = 7200 # 2 h

# TTL is used for some records (2min)
# should NOT be changed
TTL_short = 120


def main() :
	
	args = readArgs()
	
	
	# check interfaces 
	sysIfaces = netifaces.interfaces()
	
	interfaces = args.interfaces
	if args.interfaces == "all" :
		interfaces = sysIfaces
	
	for iface in interfaces : 
		if iface not in sysIfaces :
			print "Invalid interface specified: " + iface 
		elif "lo" not in iface:
			try:
#			print iface
				sendUpdateForInterface(iface)
			except: # catch *all* exceptions
				print "Unexpected error: ", sys.exc_info()
	
	
def sendUpdateForInterface(interface) :

	## get all available sleep proxies
	proxies = discoverSleepProxies(interface)
	if (len(proxies) == 0) :
		print "No sleep proxy available for interface: " + interface
		return
	
	addrs = netifaces.ifaddresses(interface)

	ip4Addr = addrs[netifaces.AF_INET][0]['addr']
	if ":" in interface : # handle virtual interfaces
		hwAddr = netifaces.ifaddresses(interface.rsplit(':')[0])[netifaces.AF_LINK][0]['addr']
	else:
		hwAddr = addrs[netifaces.AF_LINK][0]['addr']

	#prepare IP and a reversed IP
	ip4Arr = ip4Addr.rsplit(".")
	ip4ArrInv = ip4Arr[:]
	ip4ArrInv.reverse()
	ip4Inv = ".".join(ip4ArrInv)

	
		
	host = socket.gethostname() 
	host_local = host + ".local"
		
	#	create update request
	update = dns.update.Update("")
	
	# add some host stuff
	update.add(ip4Inv + '.in-addr.arpa', TTL_short, dns.rdatatype.PTR, host_local)
	update.add(host_local, TTL_short, dns.rdatatype.A,  ip4Addr)
	
	#	add services	
	for service in discoverServices(ip4Addr) :
		type = service[0] + ".local"
		type_host = host + "." + type
		port = service[1]
	
		# Add the service
	 	txtrecord = ""
		if (len(service) == 2 or service[2] == "") : 
			txtrecord = chr(0)
		else :
			for i in range(2,len(service)) :
					txtrecord += " " + service[i]					
	
		update.add(type_host, TTL_long, dns.rdatatype.TXT, txtrecord)
		update.add('_services._dns-sd._udp.local', TTL_long, dns.rdatatype.PTR, type + ".local")
		update.add(type, TTL_long, dns.rdatatype.PTR, type_host)
		update.add(type_host, TTL_short, dns.rdatatype.SRV, "0 0 " + port + " " + host_local)
	
	
	# add device info
	update.add(host + '._device-info._tcp.local.', TTL_long, dns.rdatatype.TXT, "model=" + DEVICE_MODEL + " state=sleeping")
	
	
	#	add edns options
	
	# http://files.dns-sd.org/draft-sekar-dns-ul.txt
	# 2: Lease Time in seconds  
	leaseTimeOption = dns.edns.GenericOption(2, struct.pack("!L", 7200))
	
	# http://tools.ietf.org/id/draft-cheshire-edns0-owner-option-00.txt
	# 4: edns owner option (MAC addr for WOL Magic packet)
	cleanMAC = hwAddr.replace(":", "")
	ownerOption = dns.edns.GenericOption(4, ("0000" + cleanMAC).decode('hex_codec'))
	
	# 1: use edns
	# 2: Z (TTL) 
	# 3: payload size
	update.use_edns(0, TTL_long, 1440, None, [leaseTimeOption, ownerOption])
	
	#print update	
	
	
	# send request to all proxies
	for proxy in proxies :
		try:
			errStr = "Unable to register with SleepProxy " + proxy['ip'] + ":" + proxy['port']

			response = dns.query.udp(update, proxy['ip'], timeout=10, port=int(proxy['port']))
			#print response

			rcode = response.rcode()
			if rcode != dns.rcode.NOERROR:
				print errStr
				print response
			
		except DNSException, e:
			print errStr
			print e



def discoverServices(ip):
# discover all currently announced local services

	services = []
	cmd = "avahi-browse --all --resolve --parsable --no-db-lookup --terminate 2>/dev/null | grep '=;.*;IPv4;' | grep ';" + ip + ";'"
	
	p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	for line in p.stdout.readlines():
	    lineArr = line.rsplit(";")

			# check length
	    if (len(lineArr) < 10) :
	    	p.terminate()
	    	break
	    	
	    #extract service details
	    if (lineArr[7] == ip) :
	    	service = lineArr[4]
	    	port = lineArr[8]
	    	txtRecords = lineArr[9].replace('" "', ';').replace('\n', '').replace('"', '').rsplit(';')
	    	services.append([service, port] + txtRecords)

	retval = p.wait()
	return services



def discoverSleepProxies(interface):
# discover all available Sleep Proxy Servers

	proxies = []
#	cmd = "avahi-browse --resolve --parsable --no-db-lookup --terminate _sleep-proxy._udp 2>/dev/null | grep '=;" + interface + ";IPv4;'" # causes truoble for eth0:1 interfaces
	cmd = "avahi-browse --resolve --parsable --no-db-lookup --terminate _sleep-proxy._udp 2>/dev/null | grep '=;.*;IPv4;'"
	
	p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	for line in p.stdout.readlines():
			lineArr = line.rsplit(";")

			# check length
			if (len(lineArr) < 10) :
				p.terminate()
				break

			ip = lineArr[7]
			port = lineArr[8]
			proxies.append({ "ip" : ip, "port" : port})

	retval = p.wait()
	return proxies
	

def readArgs() :
# parse arguments
	global DEVICE_MODEL
	global TTL_long
		
	parser = argparse.ArgumentParser(description='SleepProxyClient')
	parser.add_argument('--interfaces', nargs='+', action='store', help="A list of network interfaces to use, seperated by ','", default="all")
	parser.add_argument('--ttl', action='store', type=int, help='TTL for the update in seconds. Client will be woken up after this period.', default=TTL_long)
	parser.add_argument('--device-model', action='store', help='The device-model to send (_device-info._tcp.local).', default=DEVICE_MODEL)
	
	result = parser.parse_args()
		
	# update some global vars 
	DEVICE_MODEL = result.device_model
	TTL_long = result.ttl
	
	return result


main()