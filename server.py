from User import *

# importing libraries
import socket
import cv2
import pickle
import struct
import sys
from threading import Thread

users = {}

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_name = socket.gethostname()
HOST_IP = "localhost"
PORT = 10050
print('Socket created')
server_socket.bind((HOST_IP, PORT))
print('Socket bind complete')
server_socket.listen(5)
print('Socket now listening')

authenticator = Authenticator()
authorizer = Authorizer(authenticator)
authenticator.add_user("manager", "supreme_manager#2022", "manager")


def handle_request(user_socket, user_addr):
    while True:
        command = user_socket.recv(1024).decode()
        if command.startswith("send_file"):
            file_name = command.split()[1]
            data = "ready"
            user_socket.send(data.encode())
            recv_file = open('server_file/' + file_name, 'wb')
            file_to_recv = user_socket.recv(4096)
            while file_to_recv:
                print("Receiving...")
                recv_file.write(file_to_recv)
                file_to_recv = user_socket.recv(4096)
            print("File recv or converted sucessfully.")
            return
        elif user_socket and command.startswith("play"):
            file_name = command.split()[1]
            vid = cv2.VideoCapture('server_file/' + file_name)
            print("opened")
            user_socket.send("ready to send".encode())
            video_port = int(user_socket.recv(1024).decode().split()[1])
            video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            video_socket.connect((addr[0], video_port))
            while vid.isOpened():
                img, frame = vid.read()
                a = pickle.dumps(frame)
                message = struct.pack("Q", len(a)) + a
                try:
                    video_socket.sendall(message)
                except:
                    print("client disconnected")
                    break
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                print("sending...")
            video_socket.close()

        elif command.startswith("register_user"):
            try:
                username = command.split()[1]
                password = command.split()[2]
                authenticator.add_user(username, password, "user")
                authenticator.login(username, password)
                user_socket.send("successful".encode())
            except UsernameAlreadyExists:
                user_socket.send("username already exist".encode())

        elif command.startswith("login"):
            try:
                username = command.split()[1]
                password = command.split()[2]
                authenticator.login(username, password)
                user_socket.send("successful".encode())
            except InvalidUsername or InvalidPassword:
                user_socket.send("wrong username or password".encode())


while True:
    client_socket, addr = server_socket.accept()
    print('Connection from:', addr)
    # handle_request(client_socket,addr)
    thread = Thread(target=handle_request, args=(client_socket, addr,))
    thread.start()
