# A SleepProxyClient implementation

## About

Wake on Demand (http://support.apple.com/kb/HT3774) is great.
It enables an unused device to go to sleep while keeping it's announced MDNS (Zeroconf) services alive and will be woken up on access again.

These scripts enables your Linux server to save energy by going to sleep if it's currently not in use.
But it will be instantly woken up again by the SleepProxyServer using Wake on Lan (WOL) if one of it's services is requested. See http://en.wikipedia.org/wiki/Bonjour_Sleep_Proxy for more details.

### Requierments
To get this running, a SleepProxyServer on your local network is required. If present, it will announce itself via MDNS as <code>_sleep-proxy._udp</code>. 
Such a server is included in many Apple devices like its network products "Time Capsule" and "AirPort Express". But an Apple TV or any Mac running 10.6 or above can be turned into a sleep proxy server too.

### Status
The latest relase of SleepProxyClient is 0.4.

Please report issues to make it even more stable to use.


## Setup / Install

### Requirements

 - python
 - dnspython (http://www.dnspython.org)
 - avahi-browse (to discover the sleep proxy and local services)
 - pm-utils (pm-suspend has to be used to suspend the host to trigger these scripts)
 
 These dependencies can be easy installed on Debian/Ubuntu using the following command:
 <pre>apt-get install python python-dnspython python-argparse python-netifaces python-ipy python-support avahi-utils pm-utils</pre>
 
In addition it has to be possible to wake the host via Wake on LAN from sleep.
 
### Install

On Debian/Ubuntu just install the deb-package available from the repository:
  1. Get and add the public key for this repo:
<code>echo '-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1.4.10 (GNU/Linux)

mQENBFAzpncBCAC9cHXeCixyiA1H7pYV1WvEiBuUOA3xeu1uOWAVWRZhQkJq/V/x
TyZPgT3k43zdNlkEqXG8VdS7w0SARx3zkhHxOz//w7F1hPd4Z0VtfvjaB4YeryM/
tcoTo2DIRPG4NThUdqgFcfFlRSy47wFcLLozCusBsQnLR5StfQlNtgBVVn9HhpeQ
cb/BVeK3wJbv7S4hYFKsC5yoseOKmezr51B2lNEDbtZV4Bg6K4lC14Zh4wgEsWUl
1uz6bClnmybGbp7LElWK/53Bw0iIMZk2A0ZOtMu/U7CQtrSQMD3rHhQ53Gj/zZpc
+9suLpLRR7Sdk876ATljqMBDiouUom86Lde3ABEBAAG0LEFuZHJlYXMgV2Vpbmxl
aW4gPGFuZHJlYXMuZGV2QHdlaW5sZWluLmluZm8+iQE+BBMBAgAoBQJQM6Z3AhsD
BQkDwmcABgsJCAcDAgYVCAIJCgsEFgIDAQIeAQIXgAAKCRAC20Bcw6YK1z8uB/wI
uqm4/tPofrsLgZY1qq7K0rT6yq99yYH/10ge8SNPr8tptbiLGheSmjjr7Z9T8D0S
kiYXR48xR/kQutxv4TfKOgAD7G8Q9LnqGkgJjJGd7xcP+wbAjEgRZuHgrJ28YE3f
r1xgnvAkTT7oQXuqESu/MT4DwK5FUpDuuZ47cWLptbZK1HaF8zZKl8WFC8P2XhXC
RVft7nHHna0OvdOFvvbKErd0S4un9rEGDNBKJQeXA6Puy8LPGm7A1y1CC+IsrAJx
5QtBmQ1DYUSFNfplfBXer+J0qpOwzGEH0N4O/bEGqgApbK3c3aJBpLcdt3VtW/Bj
f1TvkowRmPkuyVP2h+K+
=KeW0
-----END PGP PUBLIC KEY BLOCK-----' | apt-key add -</code>

  2. Add the following line to your <code>sources.list</etc>:
<code>
deb http://repo.weinlein.info unstable main
</code>

  3. Update apt and install the package
<code>
apt-get update
apt-get install sleepproxyclient
</code>

### Configuration

#### Services

All locally announced services will be discovered via avahi-browse. There is no manual configuration needed anymore.

#### Setup auto-sleep

Create your own or use the included <code>checkSleep.sh</code> script.
The checkSleep script needs to be called periodically to be able to suspend the host by it's own.
This can be done by creating a cronjob via crontab:
<pre>*/8 * * * * /bin/bash /usr/share/sleepproxyclient/scripts/checkSleep.sh</pre>

This job causes the checkSleep.sh to be called every 8 minutes. Since two successfully calls are required to suspend the host it will take at least 16 minutes until the suspend is done.

#### Tuning some parameters

Some more parameters can be adjusted to fit your needs:

- List of network interfaces    
	By default all interfaces are used. This can be changed by enabling this option.

- TTL (Time to live)   
	The TTL controls the life time of the mDNS announcement. After this period the sleep client will be woken up be the sleep proxy server again. The default value is 2 hours.

- Device Model   
	The device model to be announced can also be changed. (The small icon besides the servers name within the finder sidebar). It defaults to "RackMac".

These settings can be configured via <code>/etc/default/sleepproxyclient</code>
	
### What's inside

- 00_sleepproxyclient
	This hook will be installed to <code>/etc/pm/sleep.d/</code> and called by pm-utils before going to sleep. This script will call sleepproxyclient.sh and is actually calling the sleepproxyclient scripts.

- checkSleep.sh   
 Is an example script to show how to actually suspend the host. It does some checks to determine if the host is currently in use or not. It will suspend the host after two successfully calls by <code>pm-suspend</code>. This script is designed to be periodically called by a cronjob.
	To be able to do some more advanced checks take a look at other projects like https://github.com/OMV-Plugins/autoshutdown/. Just configure them to call <code>pm-suspend</code> instead of <code>shutdown</code> to activate your SleepProxyClient.


## Support this project

Just support this project by contributing some code, creating issues or just by clicking the flattr-button - Thanks!

<a href="http://flattr.com/thing/713748/aweinSleepProxyClient-on-GitHub" target="_blank">
<img src="http://api.flattr.com/button/flattr-badge-large.png" alt="Flattr this" title="Flattr this" border="0" /></a>