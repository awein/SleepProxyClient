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
import struct

import argparse
import sys

#
#	A Python Wake On Demand client implementation (SleepProxyClient)
#


# The device-model to send (_device-info._tcp.local).
# can be overwritten by specifying the corresponding argument!
DEVICE_MODEL="RackMac"

# TTL for sleep client.
# A Wake-On-Lan-Packet will be sent after this period.
# can be overwritten by specifying the corresponding argument!
TTL_long=7200 # 2 h

# TTL is used for some records (2min)
# should NOT be changed
TTL_short=120


def main():
	args = readArgs()
	
	#prepare IP and a reversed IP
	ip_arr = args.SPC_IP.rsplit(".")
	if (len(ip_arr) != 4) :
		print "Invalid SPC_IP - exiting"
		sys.exit(1)
	
	ip_inv= ip_arr[3] + "." + ip_arr[2] + "." + ip_arr[1] + "." + ip_arr[0]
	
	
	host_local = args.SPC_Hostname + ".local"
	host = args.SPC_Hostname
	
	
	#	create update request
	update = dns.update.Update("")
	
	# add some host stuff
	update.add(ip_inv + '.in-addr.arpa', TTL_short, dns.rdatatype.PTR, host_local)
	update.add(host_local, TTL_short, dns.rdatatype.A,  args.SPC_IP)
	
	#	add services	
	for service in readServices(args.SPC_Services) :
		type = service[0] + ".local"
		type_host = host + "." + type
		port = service[1]
	
		# Add the service
	 	txtrecord = ""
		if (len(service) == 2) : 
			txtrecord = chr(0)
		else :
			for i in range(2,len(service)) :
				txtrecord += " "
				txtrecord += service[i]	
	
		update.add(type_host, args.TTL, dns.rdatatype.TXT, txtrecord)
		update.add('_services._dns-sd._udp.local', args.TTL, dns.rdatatype.PTR, type + ".local")
		update.add(type, args.TTL, dns.rdatatype.PTR, type_host)
		update.add(type_host, TTL_short, dns.rdatatype.SRV, "0 0 " + port + " " + host_local)
	
	
	# add device info
	update.add(host + '._device-info._tcp.local.', args.TTL, dns.rdatatype.TXT, "model=" + args.DEVICE_MODEL)
	

	
	#	add edns options
	
	# http://files.dns-sd.org/draft-sekar-dns-ul.txt
	# 2: Lease Time in seconds  
	leaseTimeOption = dns.edns.GenericOption(2, struct.pack("!L", 7200))
	
	# http://tools.ietf.org/id/draft-cheshire-edns0-owner-option-00.txt
	# 4: edns owner option (MAC addr for WOL Magic packet)
	cleanMAC = args.SPC_MAC.replace(":", "")
	ownerOption = dns.edns.GenericOption(4, ("0000" + cleanMAC).decode('hex_codec'))
	
	# 1: use edns
	# 2: Z (TTL) 
	# 3: payload size
	update.use_edns(0, args.TTL, 1440, None, [leaseTimeOption, ownerOption])
	


	# send request
	response = dns.query.udp(update, args.SPS_IP, timeout=10, port=args.SPS_Port)
	
	



def readServices(filepath):
		# Read services to announce from file.

 	SERVICES = []

	file = open(filepath, 'r')
	
	for line in file :
	  # check if the line contains a service definition
		if not line.startswith("_"):
			continue
	  
		line = line.strip()
		SERVICE_ARR = line.rsplit(" ")
		if len(SERVICE_ARR) < 2 :
			print "Invalid service definition: " + line
		else:
			SERVICES.append(SERVICE_ARR)					
	
	file.close()
	return SERVICES



def readArgs():
# parse arguments

	parser = argparse.ArgumentParser(description='SleepProxyClient')
	parser.add_argument('-SPS_IP', action='store', required=True,
                   help='IP of the SleepProxyServer')
	parser.add_argument('-SPS_Port', action='store', type=int, required=True, help='Port of the SleepProxyServer')
	parser.add_argument('-SPC_MAC', action='store', required=True,
                   help='The MAC-Address of the client')
	parser.add_argument('-SPC_IP', action='store', required=True,
                   help='The IP-Address of the client')
	parser.add_argument('-SPC_Hostname', action='store', required=True,
                   help='The clients hostname')
	parser.add_argument('-SPC_Services', action='store', required=True,
                   help='The clients services as filepath')
                   
#optional args
	parser.add_argument('-TTL', action='store', type=int, help='TTL for the update in seconds. Client will be woken up after this period.', default=TTL_long)
	parser.add_argument('-DEVICE_MODEL', action='store', help='The device-model to send (_device-info._tcp.local).', default=DEVICE_MODEL)
	
	return parser.parse_args()


main()