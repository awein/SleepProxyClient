# A SleepProxyClient implementation (Wake on Demand)

## About

Wake on Demand (http://support.apple.com/kb/HT3774) is great.
It enables an unused device to go to sleep while keeping it's announced MDNS (Zeroconf) services alive and will be woken up on access again.

These scripts enables your Linux server to do save energy by going to sleep if it's unused.
If one of it/s services will be requested it will be woken up by Wake on Lan (WOL) by the SleepProxyServer. See http://en.wikipedia.org/wiki/Bonjour_Sleep_Proxy for more details.


### Requierments
A SleepProxyServer on your network is required an will announce itself via MDNS (_sleep-proxy._udp). 
Such a server is included in many Apple devices like its network products Time Capsule and AirPort Express. But also an Apple TV or any Mac can be turned into a sleep proxy server.

## Setup / Install

### Requirements

 - python
 - dnspython (http://www.dnspython.org)
 - avahi-browse (to find the sleep proxy)
 
 To install the required stuff on Debian/Ubuntu:
 <pre>apt-get install python python-dnspython avahi-utils</pre>

### Configuration

#### Setup auto-sleep

#### Custom services

#### Tuning some parameters


