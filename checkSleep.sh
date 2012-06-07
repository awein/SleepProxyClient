#!/bin/bash

export PATH=/root/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export LANG=en_US.utf8

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#
# checkSleep
#
# execute SleepProxyClient and pm-suspend if two runs after each other are positive
#
#	Creteria:
#		- no user logged in (remote + local) 
#		- no non-local active tcp connections
#
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#used to check for a previous successfull run
TMPFILE="/tmp/checkSleep"

#value will be returned. 0 if the creteria was fullfilled
RET=0

# network interface to use
IFACE="eth0"

SCRIPT_DIR=$(dirname $0)

# run SleepProxyClient
function doSleep {
	logger "checkSleep: initiating sleep"
	bash $SCRIPT_DIR/spc.sh "$IFACE"
	pm-suspend
	logger "checkSleep: awake!"
}

# check the creteria
function doCheck {

	RESULT=0

	# check for logged in user
	USERS=`who | wc -l`
	if [ $USERS -gt 0 ]
	then
#		echo "Active users: $USERS"
		RESULT=1
	fi


	# check if no non-local connection is active
	CONNS=`netstat -tn | grep -v "127.0.0.1" | grep "ESTABLISHED" | wc -l`
	if [ $CONNS -gt 0 ]
	then
#		echo "Active connections: $CONNS"
		RESULT=1
	fi

	return $RESULT
}

doCheck
if [ $? -eq 0 ]
then
	# we only want to go to sleep if two successive doCheck runs were successfull 
	# check whether the previous run created the file to signal success 
	if [ -e "$TMPFILE" ]
	then
		# cleanup
		rm -f "$TMPFILE"
		
		# initiate sleep
		doSleep
	else
		# mark run as positive
		touch "$TMPFILE"
	fi
else
	rm -f "$TMPFILE"
	RET=1
fi

exit $RET
