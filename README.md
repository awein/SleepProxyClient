# A SleepProxyClient implementation

## About
Wake on Demand (http://support.apple.com/kb/HT3774) is great.
It enables an unused device to go to sleep, while keeping the announced mDNS (multicast DNS) services alive.
Just access one of the services and the device will be woken up automatically.

These scripts enables your non-Apple-devices, e.g. a server or NAS, to save energy by going to sleep while not in use.
The Sleep Proxy Server will wake the device using Wake on LAN (WOL), as soon as a port matching an announced service is accessed. See http://en.wikipedia.org/wiki/Bonjour_Sleep_Proxy for more details.

### Requirements
To get this running, a Sleep Proxy Server on your local network is required. If present, it will announce itself via mDNS as `_sleep-proxy._udp`. 
Such a server is included in many Apple devices like its network products "Time Capsule" and "AirPort Express". But an Apple TV or any Mac running 10.6 or above can be turned into a sleep proxy server too. 

### Status
SleepProxyClient is pretty stable and ready for everyday use.
Please report issues to make it even more stable.


## Setup / Installation
### Requirements

 - python3
 - dnspython (http://www.dnspython.org)
 - and other useful python modules
 - avahi-browse (to discover the Sleep Proxy Server and local services)
 - systemd-sleep (pm-utils or similar power management tools can be used as well)

In addition, the host needs to support Wake on LAN.

### Installation
SleepProxyClient works out of the box on Debian/Ubuntu.
It's quite easy to install SleepProxyClient on other Linux distributions and UNIX/BSD systems too.

#### Debian / Ubuntu
Download the package from releases page and install it using `dpkg -i sleepproxyclient_<version>_all.deb`.
Issues due to missing dependencies can be resolved using `apt --fix-broken install`.

#### Other operating systems
SleepProxyClient was tested on Linux but should work on other operating systems too.  
The only Linux specific dependency (`systemd-sleep`) should be easily replaceable by other OS-specific power management tools like `apmd` on BSD.
Just ensure the suspend-script (`sleepproxyclient.sh`) is called before suspending the system.

### Configuration
#### Services
All locally announced services will be discovered via `avahi-browse` automatically - there is no need for manual configuration of services.

#### Setup auto-sleep
Create your own, or use the included `checkSleep.sh` script.
The `checkSleep.sh` script needs to be called periodically to be able to suspend the host by it's own.
This can be achieved by various means, e.g. by creating a cron job via crontab:
```
*/8 * * * * /bin/bash /usr/share/sleepproxyclient/scripts/checkSleep.sh
```

This job causes `checkSleep.sh` to be called every 8 minutes. Since two successfully calls are required to suspend the host, it will take at least 16 minutes until the host will enter suspend.

#### Tuning some parameters
Some more parameters can be adjusted to fit your needs:

- List of network interfaces  
	By default, all interfaces are used. Use the related option to adjust this behavior.

- Lease time (Time to live)  
	The lease time (or TTL) controls the life time of the mDNS announcement. The host running SleepProxyClient will be woken up be the Sleep Proxy Server after this period to allow it to renew the announcement. The default value is 2 hours.

These settings can be configured via `/etc/default/sleepproxyclient` or the `--lease-time` option.
	
### What's inside

- `sleepproxyclient.py`  
  The actual Sleep Proxy Client implementation.

- `00_sleepproxyclient`    
	This hook will be installed to `/usr/lib/systemd/system-sleep/` and called by `systemd-sleep` before going to sleep. This script calls `sleepproxyclient.sh` which will then call `sleepproxyclient.py`.

- `checkSleep.sh`   
  Is an example script, to show how to actually suspend the host. It does some checks - to determine if the host is currently in use or not - and will suspend the host after two successful calls. Suspend is initiated through `systemctl suspend`. This script is designed to be periodically called using a cron job.
  Any other custom / more advanced checks can be used as well. Just ensure to suspend the host using `systemctl suspend` to activate SleepProxyClient.
