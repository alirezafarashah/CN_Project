# importing libraries
import socket
import cv2
import pickle
import struct
import imutils

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_ip = 'localhost'
port = 10050
client_socket.connect((host_ip, port))
is_logged_in = False


def receive_video(rcv_socket, addr):
    payload_size = struct.calcsize("Q")
    data = b""
    while True:
        while len(data) < payload_size:
            packet = rcv_socket.recv(4 * 1024)
            if not packet: break
            data += packet
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]
        while len(data) < msg_size:
            data += rcv_socket.recv(4 * 1024)
        frame_data = data[:msg_size]
        data = data[msg_size:]
        frame = pickle.loads(frame_data)
        cv2.imshow("Receiving...", frame)
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
    rcv_socket.close()
    cv2.destroyAllWindows()
    print("closed")


while True:
    command = input()
    if command.startswith("help"):
        client_socket.send("help".encode())
        result = client_socket.recv(1024).decode()
        print(result)
    elif command.startswith("register_user"):
        username = input("username: ")
        password = input("password: ")
        client_socket.send(("register_user " + username + " " + password).encode())
        result = client_socket.recv(1024).decode()
        print(result)
    elif command.startswith("register_admin"):
        username = input("username: ")
        password = input("password: ")
        client_socket.send(("register_admin " + username + " " + password).encode())
        result = client_socket.recv(1024).decode()
        print(result)
    elif command.startswith("login"):
        username = input("username: ")
        password = input("password: ")
        client_socket.send(("login " + username + " " + password).encode())
        result = client_socket.recv(1024).decode()
        print(result)
    elif command.startswith("send_file"):
        file_name = command.split()[1]
        data = "send_file " + file_name
        client_socket.send(data.encode())
        message = client_socket.recv(1024).decode()
        if message.startswith("ready"):
            tosend_file = open(file_name, 'rb')
            Filetosend = tosend_file.read(4069)
            while (Filetosend):
                print('Sending your file...')
                client_socket.send(Filetosend)
                Filetosend = tosend_file.read(4096)
            tosend_file.close()
            print("File sended sucessfully\n clossing...")
            break
        else:
            print("error")
            break
    elif command.startswith("play"):
        client_socket.send(command.encode())
        result = client_socket.recv(1024).decode()
        if result.startswith("ready"):
            video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            video_socket.bind(("localhost", 0))
            video_socket.listen()
            port = video_socket.getsockname()[1]
            client_socket.send(("port: " + str(port)).encode())
            while True:
                rcv_socket, addr = video_socket.accept()
                receive_video(rcv_socket, addr)
                rcv_socket.close()
                video_socket.close()
                break
    elif command.startswith("show all requests"):
        client_socket.send("show all requests".encode())
        res = client_socket.recv(1024).decode()
        print(res)
    elif command.startswith("accept admin"):
        username = input("username: ")
        client_socket.send(("accept admin" + " " + username).encode())
        res = client_socket.recv(1024).decode()
        print(res)
    elif command.startswith("show all videos"):
        client_socket.send(command.encode())
        res = client_socket.recv(1024).decode()
        print(res)
    elif command.startswith("show video detail"):
        video_name = input("video_name: ")
        client_socket.send((command + " " + video_name).encode())
        res = client_socket.recv(1024).decode()
        print(res)
    elif command.startswith("like"):
        video_name = input("video_name: ")
        client_socket.send((command + " " + video_name).encode())
        res = client_socket.recv(1024).decode()
        print(res)
    elif command.startswith("dislike"):
        video_name = input("video_name: ")
        client_socket.send((command + " " + video_name).encode())
        res = client_socket.recv(1024).decode()
        print(res)
    else:
        print("invalid command2")
