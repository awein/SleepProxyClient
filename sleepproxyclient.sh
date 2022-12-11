#!/bin/bash
#
# This file is part of SleepProxyClient.
#
# @license   http://www.gnu.org/licenses/gpl.html GPL Version 3
# @author    Andreas Weinlein <andreas.dev@weinlein.info>
# @copyright Copyright (c) 2012-2022 Andreas Weinlein
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


# get defaults
. /etc/default/sleepproxyclient


IF_OPT=""
if [ "$SPC_INTERFACES" != "" ]
then
	IF_OPT="--interfaces $SPC_INTERFACES"
fi

LEASE_TIME_OPT=""
if [ "$SPC_LEASE_TIME" != "" ]
then
	LEASE_TIME_OPT="--lease-time $SPC_LEASE_TIME"
fi

LOGFILE_OPT=""
if [ "$SPC_LOGFILE" != "" ] ; then
	LOGFILE_OPT="--logfile '$SPC_LOGFILE'"
fi

DEBUG_OPT=""
if [ "$SPC_DEBUG" != "" ] ; then
	DEBUG_OPT="--debug"
fi

SCRIPTDIR=`dirname $0`

if [ "$SPC_DEBUG" != "" ] ; then
	set -x
fi
python3 $SCRIPTDIR/sleepproxyclient.py $IF_OPT $LEASE_TIME_OPT $LOGFILE_OPT $DEBUG_OPT
