# A SleepProxyClient implementation

## About

Wake on Demand (http://support.apple.com/kb/HT3774) is great.
It enables an unused device to go to sleep while keeping the announced MDNS (Zeroconf) services alive.
Just access one of the services and the device will be woken up again.

These scripts enables your Non-Apple server to save energy by going to sleep if it's currently not in use.
But it will be instantly woken up again by the SleepProxyServer using Wake on Lan (WOL) if one of it's services is requested. See http://en.wikipedia.org/wiki/Bonjour_Sleep_Proxy for more details.

### Requirements
To get this running, a SleepProxyServer on your local network is required. If present, it will announce itself via MDNS as <code>_sleep-proxy._udp</code>. 
Such a server is included in many Apple devices like its network products "Time Capsule" and "AirPort Express". But an Apple TV or any Mac running 10.6 or above can be turned into a sleep proxy server too.

### Status
The latest release of SleepProxyClient is 0.6 (2012-08-27).

Please report issues to make it even more stable to use.


## Setup / Install

### Requirements

 - python
 - dnspython (http://www.dnspython.org)
 - and other usefull python modules
 - avahi-browse (to discover the sleep proxy and local services)
 - pm-utils or similar power management tools

 In addition it has to be possible to wake the host via Wake on LAN from sleep.
 
### Install

#### Linux
On Debian/Ubuntu just install the deb-package available from the repository:

  * Get and add the public key for this repo:

```
echo '-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1.4.10 (GNU/Linux)
 
mQENBFAzopoBCACoGg5JRZifLTUQE6C+OVZq3bjZSK3BX5bYC8xkL+NohUDM2hy3
ORkEVqMClp69VagfnoETsiI67QD3KMVm8gcRdsZ+Sz3gkiiSWkSCYBehZw9w1/xA
KJ6Fd7O6WG3Ejs0VTPONxPIZs5LISBqXlj4ihePWXSjni6ct/dRWrhsZpQ7wXa/p
QudsGio04C2MvN/+YK5PqVT2Xs2nD3V0YuNTUWC5QrCABDZaM5p4uN+kPgw5qQV2
Mx72QkxaRptkNQTuCvuZjRXLGV0rft6sdRjMcY4HJTAeCcX1KAbEsfjmPguAv/bt
KGPzuQPNs8CrS63Hc8mEAtH84Wb7gVRILUaVABEBAAG0HUFuZHJlYXMgVyA8ZGV2
QHdlaW5sZWluLmluZm8+iQE4BBMBAgAiBQJQM6KaAhsDBgsJCAcDAgYVCAIJCgsE
FgIDAQIeAQIXgAAKCRD6HdaF+2KzrF5nB/wJp8FAS4KLEbxcDIJuPFDT0RWCVVfB
yH3Y0tcpXGBiPtIp7He1fc7YX/81jR5ixUcHylTjf5kXu9QBVvpZSiwBfjBLGdYL
k6023z6vIEeKx1MwLEUF8MU0cvAdzD3uSZaZBYtPhvPl50kWu8X1/R+4ZWUCytPJ
4QF0KeVPytQTY9wa1/2bb3+9XKjrSri3YUE4otrktV4C8Q/3RXFOXSbbigocAqRw
d9WTGNsjsBgUV/URjhZib2ILByHUd9fiRpTeIYBnYxVw6m4zzHEeXgHcCeZbYAAu
ReINqCI1KGAimDnscrAgIaRydI9Hc7/ca+ZTnJMbxNS1qmWxw27FQ9bMmQENBFAz
pncBCAC9cHXeCixyiA1H7pYV1WvEiBuUOA3xeu1uOWAVWRZhQkJq/V/xTyZPgT3k
43zdNlkEqXG8VdS7w0SARx3zkhHxOz//w7F1hPd4Z0VtfvjaB4YeryM/tcoTo2DI
RPG4NThUdqgFcfFlRSy47wFcLLozCusBsQnLR5StfQlNtgBVVn9HhpeQcb/BVeK3
wJbv7S4hYFKsC5yoseOKmezr51B2lNEDbtZV4Bg6K4lC14Zh4wgEsWUl1uz6bCln
mybGbp7LElWK/53Bw0iIMZk2A0ZOtMu/U7CQtrSQMD3rHhQ53Gj/zZpc+9suLpLR
R7Sdk876ATljqMBDiouUom86Lde3ABEBAAG0LEFuZHJlYXMgV2VpbmxlaW4gPGFu
ZHJlYXMuZGV2QHdlaW5sZWluLmluZm8+iQE+BBMBAgAoBQJQM6Z3AhsDBQkDwmcA
BgsJCAcDAgYVCAIJCgsEFgIDAQIeAQIXgAAKCRAC20Bcw6YK1z8uB/wIuqm4/tPo
frsLgZY1qq7K0rT6yq99yYH/10ge8SNPr8tptbiLGheSmjjr7Z9T8D0SkiYXR48x
R/kQutxv4TfKOgAD7G8Q9LnqGkgJjJGd7xcP+wbAjEgRZuHgrJ28YE3fr1xgnvAk
TT7oQXuqESu/MT4DwK5FUpDuuZ47cWLptbZK1HaF8zZKl8WFC8P2XhXCRVft7nHH
na0OvdOFvvbKErd0S4un9rEGDNBKJQeXA6Puy8LPGm7A1y1CC+IsrAJx5QtBmQ1D
YUSFNfplfBXer+J0qpOwzGEH0N4O/bEGqgApbK3c3aJBpLcdt3VtW/Bjf1TvkowR
mPkuyVP2h+K+
=kSu4
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
