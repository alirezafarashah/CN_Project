import socket
from threading import Thread

proxy_IP = "localhost"
proxy_PORT = 20000

proxy_password = "1234"

server_IP = "localhost"
server_PORT = 10050
proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print('Socket created')
proxy_socket.bind((proxy_IP, proxy_PORT))
print('Socket bind complete')
proxy_socket.listen(5)
print('proxy server is running...')


def proxy(admin_socket, admin_address):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((server_IP, server_PORT))
    while True:
        command = admin_socket.recv(1024).decode()
        server_socket.send(command.encode())
        admin_socket.send(server_socket.recv(1024))


while True:
    s, addr = proxy_socket.accept()
    print('Connection from:', addr)
    if addr == ('127.0.0.1', 10051):
        new_password = s.recv(1024).decode()
        proxy_password = new_password
        print("changed password")
    else:
        print("fuck")
        password = s.recv(1024).decode()
        if password == proxy_password:
            s.send("successful connection".encode())
            thread = Thread(target=proxy, args=(s, addr,))
            thread.start()
        else:
            print("hello")
            s.send("wrong password".encode())
