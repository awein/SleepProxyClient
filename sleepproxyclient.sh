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
# sleepproxycclient.sh - SleepProxyClient
#
# Send DNS Update-request to all discovered SleepProxys
#
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# get defaults
. /etc/default/sleepproxyclient


IF_OPT=""
if [ "$SPC_INTERFACES" != "" ]
then
	IF_OPT="--interfaces $SPC_INTERFACES"
fi

TTL_OPT=""
if [ "$SPC_TTL" != "" ]
then
	TTL_OPT="--ttl $SPC_TTL"
fi

DEBUG_OPT=""
if [ "$SPC_DEBUG" != "" ] ; then
	DEBUG_OPT="--debug"
fi

SCRIPTDIR=`dirname $0`

if [ "$SPC_DEBUG" != "" ] ; then
	echo "calling: python $SCRIPTDIR/sleepproxyclient.py $IF_OPT $TTL_OPT $DEBUG_OPT"
fi
python $SCRIPTDIR/sleepproxyclient.py $IF_OPT $TTL_OPT $DEBUG_OPT
