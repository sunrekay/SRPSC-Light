import os
import uuid
import subprocess
import squid_conf


# SETTINGS
IPV6_QUANTITY: int = 0
PORTS_BEGIN: int = 0
ALLOW_IPS: list = []
APPLICATIONS = [
    "ufw",
    "nano",
    "dnsutils",
    "squid"
]


# CONFIGURATOR WILL DO IT HIMSELF
FIRST_IPV6: str = ""
USERS_PASSWORDS: list = []


class NetworkUnreachable(Exception):
    """У сервера отсутствует доступ к ipv6"""
    pass


class ErrorNoNewIPV6(Exception):
    """
    После перезагрузки добавились НЕ ВСЕ или вообще
    НЕ ДОБАВИЛИСЬ НОВЫЕ - IPV6
    """
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
    first_ipv6 = FIRST_IPV6.split(":")
    start_number_hex = first_ipv6[-1]
    start_number = int(start_number_hex, 16)
    end_number = start_number + IPV6_QUANTITY
    range_ipv6: list = []
    for i in range(start_number+1, end_number):
        new_ipv6 = first_ipv6
        new_ipv6[-1] = str(hex(i)).replace("0x", "")
        range_ipv6.append(":".join(new_ipv6))
    return range_ipv6


@error_handler
def add_new_ipv6_in_interfaces():
    interfaces: str = ""

    with open("/etc/network/interfaces", "r") as f:
        interfaces = f.read()

    range_ipv6 = get_range_ipv6()
    for ipv6 in range_ipv6:
        interfaces += f"iface ens3 inet6 static\n" \
                      f"    address {ipv6}\n" \
                      f"    netmask 32\n"

    with open("/etc/network/interfaces", "w") as f:
        f.write(interfaces)


@error_handler
def restart_network():
    os.system("ifdown ens3 && ifup ens3")


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

    range_ipv6 = get_range_ipv6()
    for i in range(len(range_ipv6)):
        http_port += f"http_port {PORTS_BEGIN+i}\n"
        acl_port_localport += f"acl port{i} localport {PORTS_BEGIN+i}\n"
        tcp_outgoing_address += f"tcp_outgoing_address {range_ipv6[i]} port{i}\n"
        users += f"acl test{i}_user proxy_auth {USERS_PASSWORDS[i].split(':')[0]}\n"
        http_access += f"http_access allow test{i}_user port{i}\n"

    with open("/etc/squid/squid.conf", "w") as f:
        f.write(squid_conf.get_conf(http_port=http_port,
                                    acl_port_localport=acl_port_localport,
                                    tcp_outgoing_address=tcp_outgoing_address,
                                    users=users,
                                    http_access=http_access))


@error_handler
def restart_squid():
    os.system("systemctl restart squid")


def get_ipv6_for_squid_conf():
    global FIRST_IPV6
    console = subprocess.run(["ip", "addr"],
                             stdout=subprocess.PIPE)
    output = str(console)
    ens3 = output[output.find("ens3"):]
    inet6 = ens3[ens3.find("inet6")+5:]
    first_ipv6 = inet6[: inet6.find("/")]
    FIRST_IPV6 = first_ipv6.strip()


@error_handler
def install_apache2_utils():
    os.system("apt-get install apache2-utils")


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
    install_apache2_utils()
    add_users_passwords_in_passwd()
    restart_squid()


if __name__ == '__main__':
    configurate_server()
