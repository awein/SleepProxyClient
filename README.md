# A SleepProxyClient implementation

## About

Wake on Demand (http://support.apple.com/kb/HT3774) is great.
It enables an unused device to go to sleep while keeping the announced MDNS (Zeroconf) services alive.
Just access one of the services and the device will be woken up again.

These scripts enables your Non-Apple server (or NAS) to save energy by going to sleep if it's currently not in use.
But it will be instantly woken up again by the SleepProxyServer using Wake on Lan (WOL) if one of it's services is requested. See http://en.wikipedia.org/wiki/Bonjour_Sleep_Proxy for more details.

### Requirements
To get this running, a SleepProxyServer on your local network is required. If present, it will announce itself via MDNS as <code>_sleep-proxy._udp</code>. 
Such a server is included in many Apple devices like its network products "Time Capsule" and "AirPort Express". But an Apple TV or any Mac running 10.6 or above can be turned into a sleep proxy server too.

### Status
SleepProxyClient is pretty stable and ready for everyday use.
Please report issues to make it even more stable.


## Setup / Install

### Requirements

 - python
 - dnspython (http://www.dnspython.org)
 - and other usefull python modules
 - avahi-browse (to discover the sleep proxy and local services)
 - pm-utils or similar power management tools

 In addition it has to be possible to wake the host via Wake on LAN from sleep.
 
### Install

SleepProxyClient works out of the box on Debian/Ubuntu.
It should be quite easy to install SPC on other Linux distributions and UNIX/BSD systems too.

#### Linux
On Debian/Ubuntu just install the deb-package available from the repository:

  * Get and add the public key for this repo:

```
echo '-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1.4.12 (GNU/Linux)

mQINBFQB8swBEACxZT6StXBncZpc5mFyxIW8iGAFtcvBP+D3QD2cr6krFWTjYNdZ
0a79dA1IypgGxUdLeBVTiSsHFV3FJm4i1WLO2cVTMCUyrH5ENTC1GYPVP7BnVmhM
1ue2jWhkmSzSwbt6+VR2Bkix7mAiCqbkbxEkKT6BVeE9tC1UEJT4QxRUtNttgRc4
LTtbIkIX74HDfAI87F/ByC5naS/PEf4ufr6V29tF1DLQ7GPslW7VGtCl9SWZ4Jeb
GJV56BpHaIikJKT5+cgpEV1aFix/okqRVL8q2y98kVLHG9VYJJkuZV/sq45Hic5h
+tc46MWSGeJlnJBqKS3gNJZ3K/XBCpuUiRjjjl92h0UJwh+Fy3hM0kn24jofcK58
OgjsCtrR1K4qmFeZBGPq1/0opSgo6xNiqc5eu/2JX822UnNT82HoEhome3Dfvyl9
p5o3/Fqyu1YhDYshPT8i5Ia3hxJUJog0V+caDydEqznhNHBKG6oO28g8Rpzhk/Os
XDFsPCx/Dk50nFhXEWtVAd/OzVkoWLs+xPkrSQ7wDeKdNfY3Gx4ALWEwdvWQdxck
yt3PiGVmun22TWYQWvc2AH/jLAm8C2EhhQ+5/AxVg5Ad1gLQiMjO2dC4ScOQfnAV
rYG77iV5Qf19ncv4UyOfCBwNi4caungTCjmKuHwR5nP8wmC53JlhJJRH0wARAQAB
tCxBbmRyZWFzIFdlaW5sZWluIDxhbmRyZWFzLmRldkB3ZWlubGVpbi5pbmZvPokC
PgQTAQIAKAUCVAHyzAIbAwUJCWYBgAYLCQgHAwIGFQgCCQoLBBYCAwECHgECF4AA
CgkQC5m/qshiim9D8RAAhsX9shL9hTd/DC+NmzLdmW/JZqscqveAf7R07tE3ssqQ
mJt8s/ekSDpZSFYYdicRxHYr+OnXUrGUvZWXC8+hx06ay+tP0620QZSapi90nNhg
Zs0YLWgDx7vho8ZE+YkN7Hs9WXmkYL9mZvbtEP9qwi9dtfenb9N5e8HN5lHfdMFi
rQT6vGEdZUVURUv70JnZ1BU+J9FxMRM/RdJAiblzFQ1VDpO7BBS47lJZ3f2tHIsh
fbT4u7XFAPujki6Gu4EVbiU8Dau40d9Wk+YZ4z0OsHQm5IvTuNLl1c3A4ZE68iDd
dgybbDnRjd8j+431d+t1oXRVCjKfiTsZbCAualsjVELYKCojliCOcoiRPEdi5L+6
1lcn3crKU1fUEKq0z2xyHiNSwPkNscjBC1nOtejlGnUQUGPOOvhRzAVXMLPbFJaD
hr1QEQ60S+bVK7EaWu/nwQqcn3sUXDpqamdYWRKLZBZK8D5JNsGt6QVCOVuE9ml1
bjSzyxcpKfbvtnEcqz69yLR/Kn+lwcibWJ7EHoXndJ4JGttMCv9usxqb3EqnHT9j
c5lKkRHAJM729vs9Vrfl0LdLcUhc7lPkeMZXYtZ0L/SmihWzltjUT3sFLlC9W9Cn
Xk9evVBI5pglqBnLfBTbMTal7tZGIdl/ObxUxajP2T81dZ1E6OKSx/tswmqUALg=
=lRed
-----END PGP PUBLIC KEY BLOCK-----' | apt-key add -
```

  * Add the repository

```bash
echo 'deb http://repo.weinlein.info unstable main' >>/etc/apt/sources.list
```

  * Update apt and install the package

```bash
apt-get update
apt-get install sleepproxyclient
```

#### Other operating systems

SleepProxyClient was tested on Linux but should work on other operating systems too.  
The only Linux specific dependency `pm-utils` should be easily replaceable by other OS-specific power management tools like `apmd` on BSD.
Just ensure the suspend-script (`sleepproxyclient.sh`) is called before suspending the system.


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

These settings can be configured via <code>/etc/default/sleepproxyclient</code>
	
### What's inside

- 00_sleepproxyclient    
	This hook will be installed to <code>/etc/pm/sleep.d/</code> and called by pm-utils before going to sleep. This script will call sleepproxyclient.sh and is actually calling the sleepproxyclient scripts.

- checkSleep.sh   
 Is an example script to show how to actually suspend the host. It does some checks to determine if the host is currently in use or not. It will suspend the host after two successfully calls by <code>pm-suspend</code>. This script is designed to be periodically called by a cronjob.
	To be able to do some more advanced checks take a look at other projects like https://github.com/OMV-Plugins/autoshutdown/. Just configure them to call <code>pm-suspend</code> instead of <code>shutdown</code> to activate your SleepProxyClient.


## Support this project

Support this project by contributing some code, creating issues or by clicking the flattr-button - Thanks!

<a href="http://flattr.com/thing/713748/aweinSleepProxyClient-on-GitHub" target="_blank">
<img src="http://api.flattr.com/button/flattr-badge-large.png" alt="Flattr this" title="Flattr this" border="0" /></a>
