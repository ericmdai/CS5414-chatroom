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
        self.master_socket.bind((address, port))
        self.master_socket.listen(1)

        # Setup listener for keeping track of broadcast messages
        self.listener = Listener(30000 + int(pid), n)

        # Setup scanners for maintaining alive list
        self.scanners = [Scanner(i) for i in xrange(n)]

    def get(self):
        return 'messages ' + ' '.join(self.listener.get_messages())

    def alive(self):
        return map(lambda x: x.is_alive(), self.scanners)

    def broadcast(self):
        for i in xrange(self.n):
            print i

    def run(self):
        self.listener.start()
        map(lambda scanner: scanner.start(), self.scanners)

        while True:
            # print self.alive()
            time.sleep(1)

        # while True:
        #     connection, address = self.master_socket.accept()
        #     print connection
        #     while True:
        #         message = connection.recv(64)
        #         if len(message) > 0:
        #             print 'messages:', self.messages


class Listener(Thread):

    def __init__(self, port, n=1):
        Thread.__init__(self)
        self.messages = []
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.bind((address, port))
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
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
