import pyodbc
import yaml
from interfaces.DatabaseConnector import DatabaseConnector


class AzureDatabase(DatabaseConnector):
    __driver = '{SQL Server}'
    # __driver = '{ODBC Driver 17 for SQL Server}'

    def __init__(self, servername: str, username: str, password: str, databasename: str):
        self.__serverName = servername
        self.__username = username
        self.__password = password
        self.__databasename = databasename
        # print(f"{self.__serverName}, {self.__username}, {self.__password}, {self.__databasename}")

    def connect(self):
        connection_string = f"DRIVER={self.__driver};SERVER={self.__serverName};PORT=1433;DATABASE=" \
                           f"{self.__databasename};UID={self.__username};PWD={self.__password}"
        print(connection_string)
        with pyodbc.connect(connection_string) as conn:
            print("MI SONO CONNESSO")
            with conn.cursor() as cursor:
                cursor.execute("SELECT TOP 3 name, collation_name FROM sys.databases")
                row = cursor.fetchone()
                while row:
                    print(str(row[0]) + " " + str(row[1]))
                    row = cursor.fetchone()


if __name__ == '__main__':
    with open("config.yml") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
        # print(config["AzureDatabase"])

        database = AzureDatabase(*[config["AzureDatabase"][key] for key in config["AzureDatabase"]])
        # print(database)
        database.connect()
        # database.top()
