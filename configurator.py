import os
import subprocess
import squid_conf


# SETTINGS
IPV6_QUANTITY: int = 0
PORTS_BEGIN: int = 0
ALLOW_IPS: list[str] = []
APPLICATIONS = [
    "ufw",
    "nano",
    "dnsutils",
    "squid"
]


# CONFIGURATOR WILL DO IT HIMSELF
FIRST_IPV6: str = ""


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


def get_range_ipv6() -> list[str]:
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
    boss_ip: str = ""
    http_port: str = ""
    acl_port_localport: str = ""
    tcp_outgoing_address: str = ""

    for ip in ALLOW_IPS:
        boss_ip += f"acl localnet src {ip}\n"

    range_ipv6 = get_range_ipv6()
    for i in range(len(range_ipv6)):
        http_port += f"http_port {PORTS_BEGIN+i}\n"
        acl_port_localport += f"acl port{i} localport {PORTS_BEGIN+i}\n"
        tcp_outgoing_address += f"tcp_outgoing_address {range_ipv6[i]} port{i}\n"

    with open("/etc/squid/squid.conf", "w") as f:
        f.write(squid_conf.get_conf(boss_ip=boss_ip,
                                    http_port=http_port,
                                    acl_port_localport=acl_port_localport,
                                    tcp_outgoing_address=tcp_outgoing_address))


@error_handler
def restart_squid():
    os.system("systemctl restart squid")


def get_ipv6_for_squid_conf():
    """Добавить определение первого ipv6"""
    FIRST_IPV6 = "first_ipv6"


def configurate_server():
    install_applications()
    check_network_status()
    enable_dns_via_ipv6()
    get_ipv6_for_squid_conf() # TODO: CREATE FUNCTION!!!
    add_new_ipv6_in_interfaces()
    restart_network()
    check_new_ipv6_in_network()
    edit_squid_conf()
    restart_squid()


if __name__ == '__main__':
    configurate_server()
