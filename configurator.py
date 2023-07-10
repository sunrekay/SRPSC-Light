import os
import subprocess

from settings import APPLICATIONS


class NetworkUnreachable(Exception):
    """У сервера отсутствует доступ к ipv6"""
    pass


def logger(func):
    def _wrapper(*args, **kwargs):
        print(f"==================== {str(func.__name__).upper()} ====================")
        func(*args, **kwargs)
    return _wrapper


@logger
def install_applications():
    for application in APPLICATIONS:
        os.system(f"apt install {application}")


@logger
def check_network_status():
    console_output = subprocess.run(["dig", "suip.biz", "@2001:4860:4860::8888", "AAAA"],
                                    stdout=subprocess.PIPE)
    if "network unreachable" in str(console_output):
        raise NetworkUnreachable


@logger
def enable_dns_via_ipv6():
    with open("/etc/resolv.conf", "w") as f:
        f.write("nameserver 2001:4860:4860::8888\n"
                "nameserver 2001:4860:4860::8844\n"
                "nameserver 8.8.8.8\n"
                "nameserver 8.8.4.4")


def configurate_server():
    install_applications()
    #check_network_status()
    enable_dns_via_ipv6()


if __name__ == '__main__':
    configurate_server()
