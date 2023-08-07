from mysql.connector import connect, Error
from settings import DB_AUTH


def create_proxy_counter_row(ip: str, geo: str):
    try:
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
