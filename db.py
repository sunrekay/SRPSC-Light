from mysql.connector import connect, Error
from configurator import DB_AUTH


def get_all_proxy():
    try:
        with connect(
                host=DB_AUTH["host"],
                user=DB_AUTH["user"],
                password=DB_AUTH["password"]
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("USE google_bots_monitoring;")
                cursor.execute(f"SELECT * FROM proxy;")
                result = cursor.fetchall()
        return result
    except Error as e:
        print(e)
        return ()


def send_proxy(ip: str, port: str, login: str, password: str, status: str = "yes"):
    try:
        with connect(
                host=DB_AUTH["host"],
                user=DB_AUTH["user"],
                password=DB_AUTH["password"]
        ) as connection:
            with connection.cursor() as cursor:
                new_proxy: tuple = (ip, port, login, password, status)
                db_proxies = get_all_proxy()

                if new_proxy in db_proxies:
                    return True

                cursor.execute("USE google_bots_monitoring;")
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
