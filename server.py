from User import *
from video import *
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
authenticator.add_user("a", "a", "user")
video_manager = VideoManager()


def handle_user_client_request(user_socket, user):
    while True:
        command = user_socket.recv(1024).decode()
        if command.startswith("send_file"):
            file_name = command.split()[1]
            data = "ready"
            user_socket.send(data.encode())
            recv_file = open('server_file/' + file_name, 'wb')
            video_port = int(user_socket.recv(1024).decode().split()[1])
            rcv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            rcv_socket.connect((addr[0], video_port))
            file_to_recv = rcv_socket.recv(4096)
            while file_to_recv:
                print("Receiving...")
                recv_file.write(file_to_recv)
                file_to_recv = rcv_socket.recv(4096)
            recv_file.close()
            print("File recv or converted sucessfully.")
            video_manager.videos.append(Video(user.username, file_name))
            rcv_socket.close()
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
        elif command.startswith("show all videos"):
            send_list_of_videos(user_socket)
        elif command.startswith("show video detail"):
            video_name = command.split()[3]
            send_video_details(user_socket, video_name)
        elif command.startswith("like"):
            video_name = command.split()[1]
            try:
                video_manager.like_video(video_name, user.username)
                user_socket.send("The video has successfully liked".encode())
            except VideoException as e:
                user_socket.send(str(e).encode())
        elif command.startswith("dislike"):
            video_name = command.split()[1]
            try:
                video_manager.dislike_video(video_name, user.username)
                user_socket.send("The video has successfully disliked".encode())
            except VideoException as e:
                user_socket.send(str(e).encode())
        elif command.startswith("dislike"):
            video_name = command.split()[1]
            try:
                video_manager.dislike_video(video_name, user.username)
                user_socket.send("The video has successfully disliked".encode())
            except VideoException as e:
                user_socket.send(e.encode())
        elif command.startswith("help"):
            user_socket.send("send_file\nplay\nlogout\nshow all videos\nshow video detail\nlike\ndislike".encode())


def accept_admin(command, manager):
    username = command.split()[2]
    try:
        for admin in manager.admin_requests:
            if username == admin.username:
                manager.admin_requests.remove(admin)
                authenticator.add_user(admin.username, admin.password, admin.type)
                return "admin is successfully accepted"
    except UsernameAlreadyExists:
        return "username already exist"

    return "invalid username"


def handle_manager_request(user_socket, manager):
    while True:
        command = user_socket.recv(1024).decode()
        if command.startswith("show all requests"):
            res = "These are all requests:\n"
            for user in manager.admin_requests:
                res += user.username + "\n"
            user_socket.send(res.encode())
        elif command.startswith("accept admin"):
            user_socket.send(accept_admin(command, manager).encode())
        elif command.startswith("help"):
            user_socket.send("show all requests\naccept admin\nlogout\nshow all videos\nshow video detail\n".encode())
        elif command.startswith("show all videos"):
            send_list_of_videos(user_socket)
        elif command.startswith("show video detail"):
            video_name = command.split()[3]
            send_video_details(user_socket, video_name)
        else:
            user_socket.send("invalid command".encode())


def handle_admin_request(user_socket, admin):
    while True:
        command = user_socket.recv(1024).decode()
        if command.startswith("help"):
            user_socket.send("logout\nshow all videos\n".encode())
        elif command.startswith("show all videos"):
            send_list_of_videos(user_socket)


def send_list_of_videos(user_socket):
    res = ""
    for video in video_manager.videos:
        res += video.name + "\n"
    user_socket.send(res.encode())


def get_details(video):
    res = ""
    res += f'likes: {len(video.likes)}\n'
    res += f'dislikes: {len(video.dislike)}\nComments:\n'
    for comment in video.comments:
        res += comment + "\n"
    res += 'limitations:\n'
    for limits in video.limitations:
        res += limits + "\n"

    return res


def send_video_details(user_socket, file_name):
    for video in video_manager.videos:
        if video.name == file_name:
            user_socket.send(get_details(video).encode())
            return
    user_socket.send("video doesn't exist".encode())


def handle_request(user_socket, user_addr):
    while True:
        command = user_socket.recv(1024).decode()
        if command.startswith("register_user"):
            try:
                username = command.split()[1]
                password = command.split()[2]
                authenticator.add_user(username, password, "user")
                user = authenticator.login(username, password)
                user_socket.send("successful".encode())
                handle_user_client_request(user_socket, user)
            except UsernameAlreadyExists:
                user_socket.send("username already exist".encode())
        elif command.startswith("register_admin"):
            try:
                username = command.split()[1]
                password = command.split()[2]
                authenticator.send_admin_reg_req(username, password, "admin")
                user_socket.send("Admin registration request has sent to manager.".encode())
            except UsernameAlreadyExists:
                user_socket.send("username already exist".encode())
        elif command.startswith("login"):
            try:
                username = command.split()[1]
                password = command.split()[2]
                user = authenticator.login(username, password)
                user_socket.send("successful".encode())
                if user.type == "user":
                    handle_user_client_request(user_socket, user)
                elif user.type == "manager":
                    handle_manager_request(user_socket, user)
                else:
                    handle_admin_request(user_socket, user)
            except AuthException:
                user_socket.send("wrong username or password".encode())
        elif command.startswith("help"):
            user_socket.send("login\nregister_user\nregister_admin\nshow all videos\nshow video detail\n".encode())
        elif command.startswith("show all videos"):
            send_list_of_videos(user_socket)
        elif command.startswith("show video detail"):
            video_name = command.split()[3]
            send_video_details(user_socket, video_name)
        else:
            user_socket.send("invalid command".encode())


while True:
    client_socket, addr = server_socket.accept()
    print('Connection from:', addr)
    # handle_request(client_socket,addr)
    thread = Thread(target=handle_request, args=(client_socket, addr,))
    thread.start()
