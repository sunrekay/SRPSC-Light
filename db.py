from mysql.connector import connect, Error
from datetime import datetime
import requests


from settings import DB_AUTH


class ErrorGetCountryCode(Exception):
    pass


def current_yyyy_mm_dd():
    return f"{datetime.now().year}-{datetime.now().month}-{datetime.now().day}"


def get_country_code(ip: str, attempt: int = 0):
    if attempt > 3:
        raise ErrorGetCountryCode

    try:
        response = requests.get(f"http://ip-api.com/json/{ip}?lang=ru")
        ip_data = response.json()
        return ip_data["countryCode"]

    except KeyError:
        return get_country_code(ip=ip, attempt=attempt+1)


def create_proxy_counter_row(ip: str):
    try:
        geo = get_country_code(ip=ip)
        with connect(
                host=DB_AUTH["host"],
                user=DB_AUTH["user"],
                password=DB_AUTH["password"]
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("USE proxy_shop;")
                cursor.execute(f"INSERT INTO proxy_counter VALUES "
                               f"('{ip}',"
                               f" '{geo}',"
                               f" 0"
                               ");")
                connection.commit()
        return True
    except Error as e:
        print(e)
        return False

    
def send_proxy(ip: str, port: str, login: str, password: str, status: str = "yes"):
    try:
        with connect(
                host=DB_AUTH["host"],
                user=DB_AUTH["user"],
                password=DB_AUTH["password"]
        ) as connection:
            with connection.cursor() as cursor:

                cursor.execute("USE proxy_shop;")
                cursor.execute(f"INSERT INTO proxy VALUES "
                               f"('{ip}',"
                               f" '{port}',"
                               f" '{login}',"
                               f" '{password}',"
                               f" '{status}'"
                               ");")
                connection.commit()
        return True
    except Error as e:
        print(e)
        return False


def create_expiration_date_row(ip: str, day_to_die: int = 30, current_date: str = current_yyyy_mm_dd()):
    """
    current_date: str = "yyyy-mm-dd"
    """
    try:
        with connect(
                host=DB_AUTH["host"],
                user=DB_AUTH["user"],
                password=DB_AUTH["password"]
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("USE proxy_shop;")
                cursor.execute(f"INSERT INTO expiration_date VALUES "
                               f"('{ip}',"
                               f" '{current_date}',"
                               f" {day_to_die}"
                               ");")
                connection.commit()
        return True
    except Error as e:
        print(e)
        return False
