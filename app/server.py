"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports
from _datetime import datetime


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)
        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                new_login = decoded.replace("login:", "").replace("\r\n", "")
                for client in self.server.clients:
                    if new_login == client.login:
                        self.transport.write(
                            f"Логин {new_login} занят, попробуйте другой".encode()
                        )
                        self.transport.close()
                        break
                else:
                    self.login = new_login
                    self.transport.write(
                        f"Привет, {self.login}!".encode()
                    )
                    self.send_history(self.server.history)
            else:
                #Пока не ввел логин не может отправлять сообщения
                self.transport.write(
                    f"Представтесь, пожалуйста".encode()
                )
        else:
            self.send_message(decoded)

    def add_message_to_history(self, message):
        #Сохраняем не болше 10 сообщений
        if len(self.server.history) == 10:
            self.server.history.pop(0)
        time = datetime.today().strftime("%d.%m.%Y %H:%M:%S")
        self.server.history.append(f"{time} {message} \r\n")

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()

        for client in self.server.clients:
            #пока пользователь не ввел логин, он не получает сообщения
            if (client.login != self.login) and (not client.login is None):
                client.transport.write(encoded)

        self.add_message_to_history(f"{format_string}")

    def send_history(self, history: list):
        if len(history) == 0:
            self.transport.write(
                "Сообщений нет.".encode()
            )
        else:
            #Чтобы пользователь знал, когда были отправлены последние сообщения
            time = datetime.today().strftime("%d.%m.%Y %H:%M:%S")
            self.transport.write(
                f"Время сервера {time} \r\nПоследние сообщения:\r\n".encode()
            )
            for message in history:
                self.transport.write(message.encode())

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
