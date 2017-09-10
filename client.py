#!/usr/bin/env python3
"""
Client for a markov chain chat bot.

:copyright: (c) 2017 by Martin Grønholdt.
:license: GPLv3, see LICENSE for more details.
"""

import argparse
import asyncore
import collections
import json
import logging
import socket
import time

import markov

# Default server address and port
HOST = 'localhost'
PORT = 1984


class Client(asyncore.dispatcher):
    """
    Client that uses a markov chain to respond to seed words from the server.
    """

    def __init__(self, host_address, name, corpus):
        """
        Constructor.

        :param host_address: Address of the chat server
        :param name: Name of the chatbot
        :param corpus: Text corpus for the markov chain.
        """
        # Base class constructor.
        asyncore.dispatcher.__init__(self)

        # Set logger.
        self.log = logging.getLogger('Client (%7s)' % name)
        # Create a new socket.
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        # Save the name
        self.name = name

        self.log.info('Connecting to host at %s', host_address)
        # Connect to the server
        self.connect(host_address)
        # Create the output message queue.
        self.outbox = collections.deque()
        # Save the text corpus.
        self.corpus = corpus

    def say(self, message):
        """
        Queue a message for the server.

        :param message: Message.
        """
        self.outbox.append(message)
        self.log.info('Enqueued message: %s', message)

    def handle_write(self):
        """
        Send queued message to the server.
        """
        # Quit if there are no messages
        if not self.outbox:
            return

        # Pop the message
        message = self.outbox.popleft()
        # Add 'End Of Massage' character.
        message += '@'
        # Send it
        self.send(bytes(message, 'UTF-8'))

    def handle_read(self):
        """
        Get messages from the server.
        """
        # Get startet
        msg = ''
        data = self.recv(1024).decode('UTF-8')

        # Continue until an EOM.
        while '@' not in data:
            msg += data
            data = self.recv(1024).decode('UTF-8')

        # Isolate data up until the EOM.
        for ch in data:
            if ch == '@':
                self.log.info('Recieved: {}'.format(msg))
                break
            msg += ch

        # Use the markov generator to create a response
        word = markov.get_last_word(msg)
        markov_str = markov.markov_gen(word, True, 5, self.corpus)
        msg = ''
        msg = markov.add_string(msg, markov_str, True)

        # Don't spam.
        #time.sleep(1)

        # Send the generated response.
        self.say('[{}]: {}'.format(self.name, msg))

    def handle_error(self):
        """
        Raise an exception on error.
        """
        raise


def main():
    """

    """
    logging.basicConfig(level=logging.INFO)

    # Parse command line
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-a', '--address',
                            type=str, dest='host', default=HOST,
                            help='Host name or address of the chat server ({}).'.format(
                                HOST))
    arg_parser.add_argument('-p', '--port', type=int,
                            dest='port', default=PORT,
                            help='Port of the chat server ({}).'.format(PORT))
    arg_parser.add_argument('-n', '--name', type=str,
                            dest='name', default='John',
                            help='Name of the chatbot.')
    arg_parser.add_argument('corpus_file', type=argparse.FileType('r'),
                            help='Generated Markov corpus file.')
    args = arg_parser.parse_args()

    # Load the text corpus.
    corpus = json.load(args.corpus_file)

    # Instanciate the client.
    client = Client((args.host, args.port), args.name, corpus)

    # Say hello.
    client.say('yo')

    # Enter the event loop-
    logging.info('Looping')
    asyncore.loop()


if __name__ == "__main__":
    main()
