#!/bin/bash

export PATH=/root/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export LANG=en_US.utf8

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#
# spc.sh - SleepProxyClient
#
# Send DNS Update-request to all discovered SleepProxys
# service definitions are read from the services file
#
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

if [ $# -ne 1 ]
then
	echo "usage: $0 iface"
	echo " - iface: A network interface with valid Hardware and IPv4 address."
	exit 1
fi

SCRIPTDIR=`dirname $0`

IFACE=$1

ifconfig "$IFACE" >/dev/null
if [ $? -ne 0 ]
then
	echo "Invalid interface specified: $IFACE"
	exit 1
fi

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
	
#	logger "SPC: -SPS_IP \"$IP\" -SPS_Port \"$PORT\" -SPC_MAC \"$MAC_ADDR\" -SPC_Hostname \"$HOSTNAME\" -SPC_IP \"$IP_ADDR\""
	python $SCRIPTDIR/spc.py -SPS_IP "$IP" -SPS_Port "$PORT" -SPC_MAC "$MAC_ADDR" -SPC_Hostname "$HOSTNAME" -SPC_IP "$IP_ADDR" -SPC_Services "$SCRIPTDIR/services"

done <<< "$PROXY_LIST"

logger "sleep initiated"
