#Markov chain chat server and bots.

This is a chat server and client that uses markov chains to keep talking.

## Main files

 * `client.py`: Client that connects to the server and sends markov generated
    messges as a response to seed words.
 * `rjwstat.py`: Markov corpus generator customised for extracting a characters
    dialogue from the Project Gutenbergs version of Rome and Juliet.
 * `server.py`: Server that sends out seed words to the clients in response
    to messages.
 * `.json`: Corpus file for the markov chain containing statistics of
    inter-word occurences in the source text.


##How?

### Generating corpus files

``rjwstat.py`` creates a dictionary of word associations and number of
occurrences needed for the generator. It is targeted at isolating dialogue, by
character, from Romeo and Juliet. Given tha character name used in the Project
Gutenberg version, it will extract a corpus for that character.

    usage: rjwstat.py [-h] [-o OUTFILE] [-c NAME] [-v] corpusfile

    positional arguments:
      corpusfile            Text file to process.

    optional arguments:
      -h, --help            show this help message and exit
      -o OUTFILE, --output OUTFILE
                            Write output to a this file.
      -c NAME, --character NAME
      -v, --verbose         Be verbose.

### Starting the server

The server needs to be started first, in order for the clients to succsefully
connect. It default to running on the localhost, but takes the following
arguments:

    usage: server.py [-h] [-a HOST] [-p PORT]

    optional arguments:
      -h, --help            show this help message and exit
      -a HOST, --address HOST
                            Host name or address of the chat server (127.0.0.1).
      -p PORT, --port PORT  Port of the chat server (1984).

### Starting a client

More that one client needs to be running for them to talk. Doh! The client
will try to connect to the server on localhost by default, but takes the
following argument:

    usage: client.py [-h] [-a HOST] [-p PORT] [-n NAME] corpus_file

    positional arguments:
      corpus_file           Generated Markov corpus file.

    optional arguments:
      -h, --help            show this help message and exit
      -a HOST, --address HOST
                            Host name or address of the chat server (localhost).
      -p PORT, --port PORT  Port of the chat server (1984).
      -n NAME, --name NAME  Name of the chatbot.

#### Example

    # Create a text corpus for Juliet.
    ./rjwstat -c Jul -o juliet.json romeo_and_juliet.txt

    # Start a client that uses the corpus and calls itself Juliet.
    ./client.py -a localhost -p 1984 -n Juliet juliet.json
