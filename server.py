from User import *
from video import *
from ticket import Ticket
# importing libraries
import socket
import cv2
import pickle
import struct
import sys
from threading import Thread
import os
import time

REQ_RATE = 2
CONNECTION_RATE = 2

proxy_IP = "localhost"
proxy_PORT = 20000

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
authenticator.add_user("a", "a", "admin")
authenticator.add_user("b", "b", "user")
video_manager = VideoManager()
tickets = {}


def handle_user_client_request(user_socket, user, number_of_req, start_time):
    while True:
        command = user_socket.recv(1024).decode()
        if check_ddos(number_of_req, start_time):
            user_socket.send("limit".encode())
            user_socket.close()
            return
        if command.startswith("send_file"):
            file_name = command.split()[1]
            if user.strike >= 2:
                data = "You cannot upload video"
                user_socket.send(data.encode())
                continue
            data = "ready"
            user_socket.send(data.encode())
            recv_file = open('server_file/' + file_name, 'wb')
            video_port = int(user_socket.recv(1024).decode().split()[1])
            rcv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            rcv_socket.connect((addr[0], video_port))
            file_to_recv = rcv_socket.recv(4096)
            number_of_chunks = 1
            while file_to_recv and number_of_chunks < 12800:
                print("Receiving...")
                recv_file.write(file_to_recv)
                file_to_recv = rcv_socket.recv(4096)
                number_of_chunks += 1
            recv_file.close()
            if number_of_chunks >= 12800:
                print("more than 50MB")
            else:
                print("File recv or converted sucessfully.")
                video_manager.videos.append(Video(user.username, file_name))
            rcv_socket.close()
        elif user_socket and command.startswith("play"):
            play_vid(command, user_socket)
            # file_name = command.split()[1]
            # vid = cv2.VideoCapture('server_file/' + file_name)
            # print("opened")
            # user_socket.send("ready to send".encode())
            # video_port = int(user_socket.recv(1024).decode().split()[1])
            # video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # video_socket.connect((addr[0], video_port))
            # while vid.isOpened():
            #     img, frame = vid.read()
            #     a = pickle.dumps(frame)
            #     message = struct.pack("Q", len(a)) + a
            #     try:
            #         video_socket.sendall(message)
            #     except:
            #         print("client disconnected")
            #         break
            #     key = cv2.waitKey(1) & 0xFF
            #     if key == ord('q'):
            #         break
            #     print("sending...")
            # video_socket.close()
        elif command.startswith("show all videos"):
            send_list_of_videos(user_socket)
        elif command.startswith("show video detail"):
            video_name = command.split()[3]
            send_video_details(user_socket, video_name)
        elif command.startswith("like"):
            video_name = command.split()[1]
            try:
                video_manager.like_video(video_name, user.username)
                user_socket.send("The video has been successfully liked".encode())
            except VideoException as e:
                user_socket.send(str(e).encode())
        elif command.startswith("dislike"):
            video_name = command.split()[1]
            try:
                video_manager.dislike_video(video_name, user.username)
                user_socket.send("The video has been successfully disliked".encode())
            except VideoException as e:
                user_socket.send(str(e).encode())
        elif command.startswith("comment"):
            video_name = command.split()[1]
            comment = user_socket.recv(1024).decode()
            try:
                video_manager.add_comment(video_name, comment, user.username)
                user_socket.send("Your comment has been successfully registered".encode())
            except VideoException as e:
                user_socket.send(str(e).encode())
        elif command.startswith("show sent tickets"):
            user_socket.send(show_sent_tickets(user, user.sent_tickets).encode())
        elif command.startswith("show tickets"):
            res = show_tickets(user, user.sent_tickets)
            user_socket.send(res.encode())
        elif command.startswith("logout"):
            user_socket.send("You have successfully logged out".encode())
            return
        elif command.startswith("add message to ticket"):
            try:
                ticket_id = int(command.split()[4])
                message = user_socket.recv(1024).decode()
                add_message_to_ticket(ticket_id, message, user)
                user_socket.send("Successful".encode())
            except Exception as e:
                user_socket.send(str(e).encode())
        elif command.startswith("change ticket status"):
            ticket_id = int(command.split()[3])
            status = command.split()[4]
            try:
                change_ticket_status(ticket_id, status,user)
                user_socket.send("Successful".encode())
            except Exception as e:
                user_socket.send(str(e).encode())
        elif command.startswith("create new ticket"):
            message = user_socket.recv(1024).decode()
            create_new_ticket(message, user.username, "server")
            user_socket.send("Successful".encode())
        elif command.startswith("help"):
            user_socket.send(
                "send_file\nplay\ncreate new ticket\nadd message to ticket\nshow sent tickets\nshow tickets\nlogout\nshow all videos\nshow video "
                "detail\nlike\ndislike\ncomment\nlogout".encode())


def play_vid(command, user_socket):
    file_name = command.split()[1]
    if not os.path.exists('server_file/' + file_name):
        print("doesn't exists")
        user_socket.send("file not found".encode())
        return
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


def handle_manager_request(user_socket, manager, number_of_req, start_time):
    while True:
        command = user_socket.recv(1024).decode()
        if check_ddos(number_of_req, start_time):
            user_socket.send("limit".encode())
            user_socket.close()
            return
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
        elif command.startswith("logout"):
            user_socket.send("You have successfully logged out".encode())
            return
        elif command.startswith("set password"):
            new_password = command.split()[2]
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((HOST_IP, 10051))
            s.connect((proxy_IP, proxy_PORT))
            s.send(new_password.encode())
            s.close()
            user_socket.send("You have successfully changed password".encode())
        elif command.startswith("show sent tickets"):
            response = show_sent_tickets(manager, manager.received_tickets)
            user_socket.send(response.encode())
        elif command.startswith("show tickets"):
            response = show_tickets(manager, manager.received_tickets)
            user_socket.send(response.encode())

        elif command.startswith("add message to ticket"):
            ticket_id = int(command.split()[4])
            message = user_socket.recv(1024).decode()
            try:
                add_message_to_ticket(ticket_id, message, manager)
                user_socket.send("Successful".encode())
            except Exception as e:
                user_socket.send(str(e).encode())
        else:
            user_socket.send("invalid command".encode())


def show_tickets(user, tickets_user):
    res = "These are all tickets:\n"
    for ticket_id in tickets_user:
        ticket = tickets[ticket_id]
        res += f'Ticket_id: {ticket_id}\n'
        if ticket.status == "closed":
            res += "\nstatus = closed \n"
        for i in range(0, len(ticket.message_sender)):
            res += f'\nsender: {ticket.message_sender[i]}'
        for i in range(0, len(ticket.message_receiver)):
            res += f'\nreciever: {ticket.message_receiver[i]}'
        res += "\n"
    return res


def show_sent_tickets(user, tickets_user):
    res = "These are sent tickets:\n"
    for ticket_id in tickets_user:
        ticket = tickets[ticket_id]
        res += f'Ticket_id: {ticket_id}\n'
        if ticket.status != "closed":
            continue
        for i in range(0, len(ticket.message_sender)):
            res += f'\nsender: {ticket.message_sender[i]}'
        for i in range(0, len(ticket.message_receiver)):
            res += f'\nreciever: {ticket.message_receiver[i]}'
        res += "\n"
    return res


def add_message_to_ticket(ticket_id, message, user):
    ticket = tickets[ticket_id]
    if ticket.status == "closed":
        raise Exception("This ticket is closed")
    if user.type != "manager" and ticket_id in user.sent_tickets:
        ticket.message_sender.append(message)
    elif user.type != "user" and ticket_id in user.received_tickets:
        ticket.message_receiver.append(message)
    else:
        raise Exception("You don't have access to this ticket")


def create_new_ticket(message, sender_user_name, receiver):
    ticket = Ticket(message, sender_user_name, receiver)
    tickets[ticket.id] = ticket
    user = authenticator.users[sender_user_name]
    if user.type == "admin" and receiver == "manager":
        user.sent_tickets.append(ticket.id)
        authenticator.users[receiver].received_tickets.append(ticket.id)
    elif user.type == "user" and receiver == "server":
        user.sent_tickets.append(ticket.id)
        for user in authenticator.users.values():
            if user.type == "admin":
                user.received_tickets.append(ticket.id)
    else:
        raise Exception("Invalid sender and receiver")


def change_ticket_status(ticket_id, status, user):
    if status == "closed" or status == "pending" or status == "solved":
        ticket = tickets[ticket_id]
        if (ticket.receiver == "server" and user.type == "admin") or (ticket.sender == user.username):
            ticket.status = status
        else:
            raise Exception("You don't have access to change this ticket status")
    else:
        raise Exception("Invalid status")


def handle_admin_request(user_socket, admin, number_of_req, start_time):
    print("admin mode")
    while True:
        command = user_socket.recv(1024).decode()
        number_of_req += 1
        if check_ddos(number_of_req, start_time):
            user_socket.send("limit".encode())
            user_socket.close()
            return
        if command.startswith("help"):
            user_socket.send(
                "admin logout\nadmin create new ticket\nadmin add message to ticket\nadmin show tickets\nadmin show sent "
                "tickets\nshow all videos\nadd limitation\ndelete video\n".encode())
        elif command.startswith("show all videos"):
            send_list_of_videos(user_socket)
        elif command.startswith("show video detail"):
            video_name = command.split()[3]
            send_video_details(user_socket, video_name)
        elif command.startswith("logout"):
            user_socket.send("You have successfully logged out".encode())
            return
        elif command.startswith("add limitation"):
            video_name = command.split()[2]
            user_socket.send("ready".encode())
            limit = user_socket.recv(1024).decode()
            try:
                video_manager.add_detail(video_name, limit, admin.username)
                user_socket.send("Your limitation has been successfully added".encode())
            except VideoException as e:
                user_socket.send(str(e).encode())
        elif command.startswith("delete video"):
            try:
                video_name = command.split()[2]
                video = video_manager.delete_video(video_name)
                user = authenticator.users[video.uploader]
                user.strike += 1
                user_socket.send("The video has been deleted successfully".encode())
            except VideoException as e:
                user_socket.send(str(e).encode())
        elif command.startswith("admin show sent tickets"):
            response = "Received tickets:\n"
            response += show_sent_tickets(admin, admin.received_tickets)
            response += "Sent tickets:\n"
            response += show_sent_tickets(admin, admin.sent_tickets)
            user_socket.send(response.encode())
        elif command.startswith("admin show tickets"):
            response = "Received tickets:\n"
            response += show_tickets(admin, admin.received_tickets)
            response += "Sent tickets:\n"
            response += show_tickets(admin, admin.sent_tickets)
            user_socket.send(response.encode())
        elif command.startswith("admin add message to ticket"):
            ticket_id = int(command.split()[5])
            user_socket.send("message: ".encode())
            message = user_socket.recv(1024).decode()
            try:
                add_message_to_ticket(ticket_id, message, admin)
                user_socket.send("Successful".encode())
            except Exception as e:
                user_socket.send(str(e).encode())
        elif command.startswith("admin change ticket status"):
            ticket_id = int(command.split()[4])
            status = command.split()[5]
            try:
                change_ticket_status(ticket_id, status, admin)
                user_socket.send("Successful".encode())
            except Exception as e:
                user_socket.send(str(e).encode())
        elif command.startswith("admin create new ticket"):
            user_socket.send("message: ".encode())
            message = user_socket.recv(1024).decode()
            create_new_ticket(message, admin.username, "manager")
            user_socket.send("Successful".encode())
        elif command.startswith("remove strike"):
            try:
                user_name = command.split()[2]
                user = authenticator.users[user_name]
                user.strike = 0
                user_socket.send("User's strike has been successfully removed".encode())
            except KeyError as e:
                user_socket.send("wrong user name".encode())
        else:
            user_socket.send("invalid command".encode())


def send_list_of_videos(user_socket):
    res = "These are list of videos\n"
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


def handle_request(user_socket, user_addr, start_time):
    number_of_req = 0
    while True:
        command = user_socket.recv(1024).decode()
        number_of_req += 1
        if check_ddos(number_of_req, start_time):
            user_socket.send("limit".encode())
            user_socket.close()
            return
        if command.startswith("register_user"):
            try:
                username = command.split()[1]
                password = command.split()[2]
                authenticator.add_user(username, password, "user")
                user = authenticator.login(username, password)
                user_socket.send("successful".encode())
                handle_user_client_request(user_socket, user, number_of_req, start_time)
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
        elif command.startswith("login_admin"):
            try:
                username = command.split()[1]
                password = command.split()[2]
                user = authenticator.login(username, password)
                user_socket.send("successful".encode())
                handle_admin_request(user_socket, user, number_of_req, start_time)
            except AuthException:
                user_socket.send("wrong username or password".encode())

        elif command.startswith("login"):
            try:
                username = command.split()[1]
                password = command.split()[2]
                user = authenticator.login(username, password)
                if user.type == "user":
                    user_socket.send("successful".encode())
                    handle_user_client_request(user_socket, user, number_of_req, start_time)
                elif user.type == "manager":
                    user_socket.send("successful".encode())
                    handle_manager_request(user_socket, user, number_of_req, start_time)
                else:
                    user_socket.send("admin must use login_admin command".encode())

            except AuthException:
                user_socket.send("wrong username or password".encode())

        elif command.startswith("help"):
            user_socket.send(
                "login\nlogin_admin\nproxy\nregister_user\nregister_admin\nshow all videos\nshow video detail\n".encode())
        elif command.startswith("show all videos"):
            send_list_of_videos(user_socket)
        elif command.startswith("show video detail"):
            video_name = command.split()[3]
            send_video_details(user_socket, video_name)
        elif user_socket and command.startswith("play"):
            play_vid(command, user_socket)
        else:
            user_socket.send("invalid command".encode())


def check_ddos(num_req, start_time):
    if num_req <= 5:
        return False
    if REQ_RATE < num_req / (time.time() - start_time):
        print("ddos detected")
        return True
    return False


def check_ddos2(addr):
    global ip_dicts
    if ip_dicts[addr][0] < 2:
        return False
    if (ip_dicts[addr][0] - 2) / (time.time() - ip_dicts[addr][1]) > CONNECTION_RATE:
        print((ip_dicts[addr][0] - 2) / (time.time() - ip_dicts[addr][1]))
        print("ddos detected type 2")
        return True
    return False


ip_dicts = {}

while True:
    client_socket, addr = server_socket.accept()
    if addr not in ip_dicts.keys():
        ip_dicts[addr] = [0, time.time()]
    ip_dicts[addr][0] += 1
    if not check_ddos2(addr):
        print('Connection from:', addr)
        time_now = time.time()
        thread = Thread(target=handle_request, args=(client_socket, addr, time_now,))
        thread.start()
