#!/usr/bin/env python

import argparse
import time

from socket import SOCK_STREAM, AF_INET, SOL_SOCKET, SO_REUSEADDR, socket, error
from threading import Thread

address = 'localhost'


class Server(Thread):

    def __init__(self, pid, n, address, port):
        Thread.__init__(self)
        self.n = n

        # Setup master socket for listening to commands from master
        self.master_socket = socket(AF_INET, SOCK_STREAM)
        self.master_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.master_socket.bind((address, port))
        self.master_socket.listen(1)

        # Setup listener for keeping track of broadcast messages
        self.listener = Listener(30000 + int(pid), n)

        # Setup scanners for maintaining alive list
        self.scanners = [Scanner(i) for i in xrange(n)]

    def parse_command(self, s, connection):
        cmd = s.strip().split(' ', 1)
        # print '[server] cmd:', cmd
        if cmd[0] == 'get':
            connection.send(self.get())
        elif cmd[0] == 'alive':
            connection.send(self.alive())
            # print '[server] Response sent'
        else:
            self.broadcast(cmd[1])

    def get(self):
        return 'messages ' + ','.join(self.listener.get_messages()) + '\n'

    def alive(self):
        living = [i if x.is_alive() else -1 for i, x in enumerate(self.scanners)]
        living = filter(lambda x: x >= 0, living)
        living = map(str, living)
        living = 'alive ' + ','.join(living) + '\n'
        # print '[server]', living
        return living

    def broadcast(self, message):
        for i in xrange(self.n):
            if self.scanners[i].is_alive():
                s = socket(AF_INET, SOCK_STREAM)
                s.connect((address, 30000 + i))
                s.send(message)
                s.close()

    def run(self):
        self.listener.start()
        map(lambda scanner: scanner.start(), self.scanners)

        # Parse commands from master
        master_buffer = ''
        connection, address = self.master_socket.accept()
        while True:
            if "\n" in master_buffer:
                (s, rest) = master_buffer.split("\n", 1)
                master_buffer = rest
                self.parse_command(s, connection)
            else:
                data = connection.recv(1024)
                master_buffer += data


class Listener(Thread):

    def __init__(self, port, n=1):
        Thread.__init__(self)
        self.messages = []
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.socket.bind((address, port))
        self.socket.listen(n)

    def get_messages(self):
        return self.messages

    def run(self):
        while True:
            connection, address = self.socket.accept()
            while True:
                message = connection.recv(128)
                if len(message) > 0:
                    # print message
                    self.messages.append(message)
                connection.close()
                break


class Scanner(Thread):

    def __init__(self, server):
        Thread.__init__(self)
        self.port = 30000 + server
        self.alive = False

    def is_alive(self):
        return self.alive

    def run(self):
        while True:
            s = socket(AF_INET, SOCK_STREAM)
            try:
                s.connect((address, self.port))
                s.close()
                self.alive = True
            except error as e:
                s.close()
                self.alive = False
            time.sleep(0.5)


def parse_args():
    parser = argparse.ArgumentParser(description='Starts a server')
    parser.add_argument('id', type=str, help='id of the server')
    parser.add_argument('n', type=int, help='number of processes')
    parser.add_argument('port', type=int, help='port of the server to run on')
    return parser.parse_args()


def main():
    args = parse_args()
    server = Server(args.id, args.n, address, args.port)
    server.start()


if __name__ == '__main__':
    main()
