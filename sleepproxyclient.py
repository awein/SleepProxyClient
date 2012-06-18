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
import subprocess

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
	ipArr = args.SPC_IP.rsplit(".")
	if (len(ipArr) != 4) :
		print "Invalid SPC_IP - exiting"
		sys.exit(1)
	
	ipArr.reverse()
	ipInv = ".".join(ipArr)
	ipArr.reverse()
		
	host_local = args.SPC_Hostname + ".local"
	host = args.SPC_Hostname
	
	
	#	create update request
	update = dns.update.Update("")
	
	# add some host stuff
	update.add(ipInv + '.in-addr.arpa', TTL_short, dns.rdatatype.PTR, host_local)
	update.add(host_local, TTL_short, dns.rdatatype.A,  args.SPC_IP)
	
	#	add services	
	for service in discoverServices(args.SPC_IP) :
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
	
	
	
	
	

def discoverServices(ip):
# discover all currently announced local services

	services = []
	cmd = "avahi-browse --all --resolve --parsable --no-db-lookup --terminate 2>/dev/null | grep ';IPv4;' | grep ';" + ip + ";'"
	
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

#optional args
	parser.add_argument('-TTL', action='store', type=int, help='TTL for the update in seconds. Client will be woken up after this period.', default=TTL_long)
	parser.add_argument('-DEVICE_MODEL', action='store', help='The device-model to send (_device-info._tcp.local).', default=DEVICE_MODEL)
	
	return parser.parse_args()


main()