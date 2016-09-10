#!/usr/bin/env python3

from socket import AF_INET, SOCK_STREAM, socket
from threading import Thread
from os import remove


def receive_server():
    with socket(AF_INET, SOCK_STREAM) as sock:
        sock.bind(('', 60124))
        sock.listen(5)
        while True:
            connection, address = sock.accept()
            file_to_receive = connection.recv(4096).decode('utf-8', 'replace')
            while '\n' not in file_to_receive:
                file_to_receive += connection.recv(4096).decode('utf-8',
                                                                'replace')
            file_to_receive = file_to_receive.split('\n')[0]
            connection.close()
            connection, address = sock.accept()
            with open(file_to_receive, 'wb') as file_to_receive:
                data = connection.recv(4096)
                while data:
                    file_to_receive.write(data)
                    data = connection.recv(4096)
            connection.close()


def send_server():
    with socket(AF_INET, SOCK_STREAM) as sock:
        sock.bind(('', 60123))
        sock.listen(5)
        while True:
            connection, address = sock.accept()
            file_to_send = connection.recv(4096).decode('utf-8', 'replace')
            while '\n' not in file_to_send:
                file_to_send += connection.recv(4096).decode('utf-8', 'replace')
            file_to_send = file_to_send.split('\n')[0]
            if ' ' in file_to_send:
                args = file_to_send.split(' ')
                file_to_send = args[0]
                delete = args[1] == '-r'
            else:
                delete = False
            try:
                with open(file_to_send, 'rb') as data:
                    connection.sendall(data.read())
            except:
                print('socket_file_server.py: could not open file:',
                      file_to_send)
            else:
                try:
                    if delete:
                        remove(file_to_send)
                except:
                    print('socket_file_server.py: could not delete file:',
                          file_to_send)
            finally:
                connection.close()

Thread(target=receive_server).start()
Thread(target=send_server).start()
