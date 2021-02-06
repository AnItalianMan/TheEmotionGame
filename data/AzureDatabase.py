import pyodbc
import yaml
from interfaces.DatabaseConnector import DatabaseConnector


class AzureDatabase(DatabaseConnector):
    class __AzureDatabase(DatabaseConnector):
        __driver = '{SQL Server}'

        def __init__(self, servername: str, username: str, password: str, databasename: str):
            self.__serverName = servername
            self.__username = username
            self.__password = password
            self.__databasename = databasename
            self.__connection_string = f"DRIVER={self.__driver};SERVER={self.__serverName};PORT=1433;DATABASE=" \
                                       f"{self.__databasename};UID={self.__username};PWD={self.__password}"
            # print(f"{self.__serverName}, {self.__username}, {self.__password}, {self.__databasename}")

        def get_data(self, chat_id):
            with pyodbc.connect(self.__connection_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM theemotiongame WHERE theemotiongame.ChatID='{chat_id}'")
                    row = cursor.fetchone()
                    if row is not None:
                        print(f"ROW: {row}")
                        giocatore = {
                            'ChatID': str(row[0]),
                            'nickname': str(row[1]),
                            'giocate': str(row[2]),
                            'vinte': str(row[3])
                        }
                        # print(giocatore)
                        return giocatore
                    return None

        def top(self):
            with pyodbc.connect(self.__connection_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"SELECT TOP 3 * FROM theemotiongame ORDER BY vinte DESC")
                    giocatori = []
                    for row in cursor.fetchall():
                        giocatori.append({
                            'ChatID': str(row[0]),
                            'nickname': str(row[1]),
                            'giocate': str(row[2]),
                            'vinte': str(row[3])
                        })
                    # print(giocatore)
                    return giocatori

        def register(self, chat_id, nickname):
            with pyodbc.connect(self.__connection_string) as conn:
                with conn.cursor() as cursor:
                    try:
                        cursor.execute(
                            f"INSERT INTO dbo.theemotiongame(ChatID, nickname, giocate, vinte) VALUES('{chat_id}', '{nickname}', '{0}', '{0}')")
                        return True
                    except Exception as ex:
                        return False

        def add_partita_giocata(self, chat_id, vinta=False):
            if vinta:
                vinte = 1
            else:
                vinte = 0

            with pyodbc.connect(self.__connection_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        f"UPDATE theemotiongame SET giocate = giocate + 1, vinte = vinte + {vinte} WHERE ChatID = '{chat_id}'")
                    print("INSERIMENTO ESEGUITO CON SUCCESSO")

        def delete(self, chat_id):
            with pyodbc.connect(self.__connection_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"DELETE FROM theemotiongame WHERE theemotiongame.chatID='{chat_id}'")

                    print("INSERIMENTO ESEGUITO CON SUCCESSO")

        def __execute_query(self, query):
            with pyodbc.connect(self.__connection_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    return cursor.fetchall()

    instance = None

    def __init__(self, servername: str, username: str, password: str, databasename: str):
        if AzureDatabase.instance is None:
            AzureDatabase.instance = AzureDatabase.__AzureDatabase(servername, username, password, databasename)

    def get_data(self, chat_id):
        return AzureDatabase.instance.get_data(chat_id)

    def top(self):
        return AzureDatabase.instance.top()

    def register(self, chat_id, nickname):
        return AzureDatabase.instance.register(chat_id, nickname)

    def add_partita_giocata(self, chat_id, vinta=False):
        return AzureDatabase.instance.add_partita_giocata(chat_id, vinta)

    def delete(self, chat_id):
        return AzureDatabase.instance.delete(chat_id)


if __name__ == '__main__':
    with open("config.yml") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
        # print(config["AzureDatabase"])

        database = AzureDatabase(*[config["AzureDatabase"][key] for key in config["AzureDatabase"]])
        database.delete(1000)
        # giocatori = database.top()
        # database.get_data(0)
        #
        # for giocatore in giocatori:
        #     print(giocatore)
        # database.top()
