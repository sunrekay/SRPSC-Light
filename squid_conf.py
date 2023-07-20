def get_conf(boss_ip: str,
             http_port: str,
             acl_port_localport: str,
             tcp_outgoing_address: str):
    return f"""
acl localnet src 0.0.0.1-0.255.255.255	# RFC 1122 "this" network (LAN)
acl localnet src 10.0.0.0/8		# RFC 1918 local private network (LAN)
acl localnet src 100.64.0.0/10		# RFC 6598 shared address space (CGN)
acl localnet src 169.254.0.0/16 	# RFC 3927 link-local (directly plugged) machines
acl localnet src 172.16.0.0/12		# RFC 1918 local private network (LAN)
acl localnet src 192.168.0.0/16		# RFC 1918 local private network (LAN)
acl localnet src fc00::/7       	# RFC 4193 local private network range
acl localnet src fe80::/10      	# RFC 4291 link-local (directly plugged) machines

acl SSL_ports port 443
acl Safe_ports port 80		# http
acl Safe_ports port 21		# ftp
acl Safe_ports port 443		# https
acl Safe_ports port 70		# gopher
acl Safe_ports port 210		# wais
acl Safe_ports port 1025-65535	# unregistered ports
acl Safe_ports port 280		# http-mgmt
acl Safe_ports port 488		# gss-http
acl Safe_ports port 591		# filemaker
acl Safe_ports port 777		# multiling http

http_access deny !Safe_ports

http_access allow localhost manager
http_access deny manager

include /etc/squid/conf.d/*.conf

http_access allow localnet
http_access allow localhost

via off

{boss_ip}

{http_port}

{acl_port_localport}

{tcp_outgoing_address}

# And finally deny all other access to this proxy
http_access deny all

# Squid normally listens to port 3128
http_port 3128
"""
