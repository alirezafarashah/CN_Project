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
is_logged_in = True


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
    while not is_logged_in:
        command = input("login/register_user/register_admin: ")
        if command.startswith("register_user"):
            username = input("username: ")
            password = input("password: ")
            client_socket.send(("register " + username + " " + password).encode())
            result = client_socket.recv(1024).decode()
            if result.startswith("success"):
                is_logged_in = True
            else:
                print(result)
        elif command.startswith("register_admin"):
            # TODO
            pass
        elif command.startswith("login"):
            username = input("username: ")
            password = input("password: ")
            client_socket.send(("login " + username + " " + password).encode())
            result = client_socket.recv(1024).decode()
            if result.startswith("success"):
                is_logged_in = True
            else:
                print(result)
        else:
            print("invalid command")

    command = input("please enter command: ")
    if command.startswith("send_file"):
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
