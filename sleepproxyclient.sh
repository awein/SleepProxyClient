#!/bin/bash
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

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#
# spc.sh - SleepProxyClient
#
# Send DNS Update-request to all discovered SleepProxys
# service definitions are read from the services file
#
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

export LANG=en_US.utf8

if [ $# -lt 1 ]
then
	echo "usage: $0 iface [TTL]"
	echo " - iface: A network interface with valid Hardware and IPv4 address."
	exit 1
fi

IFACE=$1

TTL_OPT=""
if [ $# -ge 2 ]
then
	TTL_OPT="-TTL=$2"
fi


ifconfig "$IFACE" >/dev/null
if [ $? -ne 0 ]
then
	echo "Invalid interface specified: $IFACE"
	exit 1
fi

SCRIPTDIR=`dirname $0`
#CONFIGDIR=`dirname $0`
CONFIGDIR="/etc/sleepproxyclient"

MAC_ADDR=`ifconfig $IFACE | awk '/HWaddr/ { print $5 }'`
IP_ADDR=`ifconfig $IFACE | awk '/inet addr:/ { print $2 }' | cut -d : -f2`

HOSTNAME=`hostname`

PROXY_LIST=`avahi-browse-domains -atprd "local" 2>/dev/null | grep "^=.*_sleep-proxy._udp" | cut -d ';' -s -f7-9  | uniq`

while read line
do
	ARR=(${line//;/ })
	HOST="${ARR[0]}"
	IP="${ARR[1]}"
	PORT="${ARR[2]}"
	
#	logger "SPC: -SPS_IP \"$IP\" -SPS_Port \"$PORT\" -SPC_MAC \"$MAC_ADDR\" -SPC_Hostname \"$HOSTNAME\" -SPC_IP \"$IP_ADDR\" $TTL_OPT"
	python $SCRIPTDIR/spc.py -SPS_IP "$IP" -SPS_Port "$PORT" -SPC_MAC "$MAC_ADDR" -SPC_Hostname "$HOSTNAME" -SPC_IP "$IP_ADDR" -SPC_Services "$CONFIGDIR/services" $TTL_OPT

done <<< "$PROXY_LIST"
