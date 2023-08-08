import os
import random

import db
import uuid
import requests
import subprocess
import squid_conf
from settings import IPV6_QUANTITY, PORTS_BEGIN,\
                     APPLICATIONS, NETWORK_NAME, DB_AUTH


IPV4: str = ""
IPV6: str = ""
IPV6_RANGE: list = []
USERS_PASSWORDS: list = []


class ConfiguratorError(Exception):
    pass


class NetworkUnreachable(ConfiguratorError):
    pass


class ErrorNoNewIPV6(ConfiguratorError):
    pass


def error_handler(func):
    def _wrapper(*args, **kwargs):
        try:
            print(f"{str(func.__name__).upper()}... ", end="")
            func(*args, **kwargs)
            print("SUCCESS")

        except Exception as error:
            print("ERROR")
            raise error

    return _wrapper


@error_handler
def install_applications():
    for application in APPLICATIONS:
        os.system(f"apt install {application}")
    os.system("apt-get install apache2-utils")


@error_handler
def check_network_status():
    console_output = subprocess.run(["dig", "suip.biz", "@2001:4860:4860::8888", "AAAA"],
                                    stdout=subprocess.PIPE)
    if "network unreachable" in str(console_output):
        raise NetworkUnreachable("У сервера отсутствует доступ к ipv6")


@error_handler
def enable_dns_via_ipv6():
    with open("/etc/resolv.conf", "w") as f:
        f.write("nameserver 2001:4860:4860::8888\n"
                "nameserver 2001:4860:4860::8844\n"
                "nameserver 8.8.8.8\n"
                "nameserver 8.8.4.4")


def get_range_ipv6():
    global IPV6_RANGE

    if IPV6_RANGE:
        return IPV6_RANGE

    first_ipv6 = IPV6.split(":")
    start_number_hex = first_ipv6[-1]
    start_number = int(start_number_hex, 16)
    end_number = start_number + IPV6_QUANTITY

    range_ipv6: list = []
    for i in range(start_number+1, end_number):
        new_ipv6 = first_ipv6.copy()
        new_ipv6[4] = str(hex(random.randint(1000, 12999))).replace("0x", "")

        for _ in range(3):
            new_ipv6.insert(4, str(hex(random.randint(1000, 12999))).replace("0x", ""))
        new_ipv6.pop(-1)

        range_ipv6.append(":".join(new_ipv6))

    IPV6_RANGE = range_ipv6
    return IPV6_RANGE


@error_handler
def add_new_ipv6_in_interfaces():
    with open("/etc/network/interfaces", "r") as f:
        interfaces = f.read()

    range_ipv6 = get_range_ipv6()
    for ipv6 in range_ipv6:
        interfaces += f"iface {NETWORK_NAME} inet6 static\n" \
                      f"    address {ipv6}\n" \
                      f"    netmask 32\n"

    with open("/etc/network/interfaces", "w") as f:
        f.write(interfaces)


@error_handler
def restart_network():
    os.system(f"ifdown {NETWORK_NAME} && ifup {NETWORK_NAME}")


@error_handler
def check_new_ipv6_in_network():
    console_output = subprocess.run(["ip", "addr"],
                                    stdout=subprocess.PIPE)
    range_ipv6 = get_range_ipv6()
    for ipv6 in range_ipv6:
        if ipv6 not in str(console_output):
            raise ErrorNoNewIPV6


@error_handler
def edit_squid_conf():
    http_port: str = ""
    acl_port_localport: str = ""
    tcp_outgoing_address: str = ""
    users: str = ""
    http_access: str = ""
    auth_data: list = []

    range_ipv6 = get_range_ipv6()
    for i in range(len(range_ipv6)):
        http_port += f"http_port {PORTS_BEGIN+i}\n"
        acl_port_localport += f"acl port{i} localport {PORTS_BEGIN+i}\n"
        tcp_outgoing_address += f"tcp_outgoing_address {range_ipv6[i]} port{i}\n"
        users += f"acl test{i}_user proxy_auth {USERS_PASSWORDS[i].split(':')[0]}\n"
        http_access += f"http_access allow test{i}_user port{i}\n"
        auth_data.append(f"{IPV4}:{PORTS_BEGIN+i}:{USERS_PASSWORDS[i]}")

    with open("/etc/squid/squid.conf", "w") as f:
        f.write(squid_conf.get_conf(http_port=http_port,
                                    acl_port_localport=acl_port_localport,
                                    tcp_outgoing_address=tcp_outgoing_address,
                                    users=users,
                                    http_access=http_access))

    with open("auth", "w") as f:
        f.write("\n".join(auth_data))


@error_handler
def restart_squid():
    os.system("systemctl restart squid")


def get_ipv6_for_squid_conf():
    global IPV4
    global IPV6
    console = subprocess.run(["ip", "addr"],
                             stdout=subprocess.PIPE)
    output = str(console)
    ens3 = output[output.find(NETWORK_NAME):]
    inet6 = ens3[ens3.find("inet6")+5:]
    first_ipv6 = inet6[: inet6.find("/")]
    IPV6 = first_ipv6.strip()
    inet = ens3[ens3.find("inet")+4:]
    IPV4 = inet[:inet.find("/")].strip()


@error_handler
def create_users_passwords():
    global USERS_PASSWORDS

    for i in range(IPV6_QUANTITY):
        user: str = f"user_{str(uuid.uuid4()).split('-')[4]}"
        password: str = f"pass_{str(uuid.uuid4()).split('-')[4]}"

        USERS_PASSWORDS.append(f"{user}:{password}")


@error_handler
def add_users_passwords_in_passwd():
    os.system(f"htpasswd -cb /etc/squid/passwd {USERS_PASSWORDS[0].split(':')[0]} "
              f"{USERS_PASSWORDS[0].split(':')[1]}")

    for i in range(1, IPV6_QUANTITY):
        os.system(f"htpasswd -b /etc/squid/passwd {USERS_PASSWORDS[i].split(':')[0]} "
                  f"{USERS_PASSWORDS[i].split(':')[1]}")


@error_handler
def send_proxy_in_db():
    if not DB_AUTH['host']:
        return

    db.create_proxy_counter_row(ip=IPV4)

    db.create_expiration_date_row(ip=IPV4)

    for i in range(IPV6_QUANTITY-1):
        db.send_proxy(ip=IPV4,
                      port=f"{PORTS_BEGIN+i}",
                      login=USERS_PASSWORDS[i].split(':')[0],
                      password=USERS_PASSWORDS[i].split(':')[1])


def configurate_server():
    install_applications()
    check_network_status()
    enable_dns_via_ipv6()
    get_ipv6_for_squid_conf()
    add_new_ipv6_in_interfaces()
    restart_network()
    check_new_ipv6_in_network()
    create_users_passwords()
    edit_squid_conf()
    add_users_passwords_in_passwd()
    send_proxy_in_db()
    restart_squid()


if __name__ == '__main__':
    configurate_server()
