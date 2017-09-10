#!/usr/bin/env python3
"""
Server for a markov chain chat bot.

:copyright: (c) 2017 by Martin Grønholdt.
:license: GPLv3, see LICENSE for more details.
"""

import asyncore
import collections
import logging
import socket
import markov
import argparse

# Default server address and port
HOST = '127.0.0.1'
PORT = 1984


class RemoteClient(asyncore.dispatcher):
    """
    Wraps a remote client socket.
    """

    # Set up logging
    log = logging.getLogger('RemoteClient')

    def __init__(self, host, socket):
        """
        Constructor

        :param host: Server object
        :param socket: Remote socket
        """
        asyncore.dispatcher.__init__(self, socket)
        # Save server instance.
        self.host = host
        # Create the output message queue.
        self.outbox = collections.deque()

    def say(self, message):
        """
        Queue a message for the server.

        :param message: Message.
        """
        self.outbox.append(message)
        self.log.info('Enqueued message: %s', message)

    def handle_read(self):
        """
        Read a message from the server and broadcast the last word as seed.
        """
        # Get startet
        msg = ''
        data = self.recv(1024).decode('UTF-8')

        # Receive message data until an 'End Of Massage' character.
        while '@' not in data:
            msg += data
            data = self.recv(1024).decode('UTF-8')

        # Isolate data up until the EOM.
        for ch in data:
            if ch == '@':
                self.log.info('Recieved: {}'.format(msg))
                break
            msg += ch

        # Remove newlines at the end.
        if msg.endswith('\n'):
            msg = msg[0:-1]

        # Print the message.
        print(msg)

        # Get last word.
        word = markov.get_last_word(msg)
        # Broadcast as seed.
        self.host.broadcast(self, word)

    def handle_write(self):
        """
        Send a queued message.

        :return:
        """
        # Exit if queue is empty.
        if not self.outbox:
            return

        # Get a queued item.
        message = self.outbox.popleft()
        # Add EOM character
        message += '@'
        # Send message.
        self.send(bytes(message, 'UTF-8'))


class Host(asyncore.dispatcher):
    """
    Chat server, sending seed words to client on receiving new messages.
    """

    # Set up logging
    log = logging.getLogger('Host')

    def __init__(self, address):
        """
        Constructor

        :param address: Server address
        """
        asyncore.dispatcher.__init__(self)
        # Create a new socket.
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind to the address
        self.bind(address)
        # Act like a server and listen
        self.listen(1)
        # List of connected clients
        self.remote_clients = []

    def handle_accept(self):
        """
        Add newly connected clients to the internal list.
        """
        socket, addr = self.accept()
        self.log.info('Accepted client at {}:{}'.format(addr[0], addr[1]))
        # Create and store a RemoteClient instance.
        self.remote_clients.append(RemoteClient(self, socket))

    def handle_read(self):
        """
        The server recieves nothing, the RemoteClient instances does.
        """
        pass

    def broadcast(self, client, message):
        """
        Broadcast a message.

        :param client: Client that wishes to broadcast.
        :param message: Message.
        """
        self.log.info('Broadcasting message: %s', message)
        for remote_client in self.remote_clients:
            # Do not send to the client broadcasting.
            if client != remote_client:
                remote_client.say(message)

    def handle_error(self):
        """
        Raise an exception on error.
        """
        raise


def main():
    """
    Main code.
    """
    logging.basicConfig(level=logging.ERROR)

    # Parse command line
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-a', '--address',
                            type=str, dest='host', default=HOST,
                            help='Host name or address of the chat server ({}).'.format(
                                HOST))
    arg_parser.add_argument('-p', '--port', type=int,
                            dest='port', default=PORT,
                            help='Port of the chat server ({}).'.format(PORT))
    args = arg_parser.parse_args()

    logging.info('Creating host')
    # Instantiate the server.
    host = Host((args.host, args.port))
    # Enter the event loop
    logging.info('Looping')
    asyncore.loop()


if __name__ == "__main__":
    main()
