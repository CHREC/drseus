#!/usr/bin/env python3
"""
Copyright (c) 2018 NSF Center for Space, High-performance, and Resilient Computing (SHREC)
University of Pittsburgh. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided
that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, 
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
OF SUCH DAMAGE.
"""


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
                        print('socket_file_server.py: deleted file:',
                              file_to_send)
                except:
                    print('socket_file_server.py: could not delete file:',
                          file_to_send)
            finally:
                connection.close()

Thread(target=receive_server).start()
Thread(target=send_server).start()
