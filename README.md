# Surendoy Remote Proxy-Server Configurator

__SRPSС__ is a software that allows to remotely configure a vps as a proxy server with __more than 1000 ipv6-addresses__ to use.

## How it works?
__SRPSC__ connects to the vps, prepares the network interface and adds new ipv6. Next, it downloads and build squid-4.10 from the source files, creates a squid.conf file and uploads it, then runs squid.

Returns a list of strings with data for connecting to the proxy.

## How to choose a vps?
__VPS Requirement:__
  - Ubuntu 20.04
  - Ipv6 subnet access
  - Ports are not blocked

__Verified hosters:__
 - [4vps.su](https://4vps.su/)
 - [pq.hosting](https://pq.hosting/)
 - ...

## Important
The average vps configuration time is __40-60 minutes__.

It is necessary to __reinstall the OS on the vps__, in case the __program is stopped during execution__.
