#!/usr/bin/env python3
"""
Use Markov chains and templates to generate "poetry"

:copyright: (c) 2016, 2017 by Martin Grønholdt.
:license: GPLv3, see LICENSE for more details.
"""
import re
import json
import random
import argparse
from collections import OrderedDict

__version__ = '0.0.6'


def prepare_word(text, word, newline):
    """
    return a word that can be added to the text in a sensible way.

    :param text: Text to add word to.
    :type text: str.
    :param word: Word to add.
    :type word: str.
    :param newline: Filter out newlines.
    :type newline: Boolean.
    """
    # Capitalise I, and I'm...
    if word == 'i' or word.startswith("i'"):
        word = word.capitalize()

    if not newline:
        word = word.strip('\n')

    # Check if we are on a new line, with no text.
    if (re.search(r'\n\W*$', text) is not None):
        if word.strip('\n') in ',.!?':
            return (None, False)

    # Handle newline at the end.
    if text.endswith('\n'):
        word = word.capitalize()
        return (word, True)

    if word.strip('\n') not in ',.!?':
        if text == '':
            return (word, True)
        word = ' ' + word
        return (word, True)

    return (word, False)


def markov_gen(start_word=None, newline=True, n_words=1, corpus=None):
    """
    Generate a string.

    :param start_word: Word to start of with, a random if chosen if None.
    :type start_word: string or None
    :param newline: Allow newline in generated string.
    :type newline: Boolean
    :param n_words: Number of words to generate.
    :type n_words: int
    :param corpus: Dictionary to use for text generation.
    :type corpus: dict
    """
    if corpus is None:
        exit('No word corpus.')

    # Pick a random word if there is nowhere else to start.
    if (start_word is None) or (start_word.strip() == ''):
        last_word = random.choice(list(corpus.keys()))
    else:
        last_word = start_word

    ret = ''
    count = False

    while n_words > 0:
        # Make up something if there is nothing to go from.
        while last_word is None:
            last_word = random.choice(list(corpus.keys()))

            last_word, count = prepare_word(ret, last_word, newline)
            if count:
                n_words -= 1
                ret += last_word

        last_word = last_word.lower().strip(' ')

        if n_words > 0:
            # Use the corpus if the word is in there.
            if last_word in corpus.keys():
                # Good thing nobody is ever going to see this ugly sequence.
                # Get a dict sorted by occurrence.
                word_dict = OrderedDict(sorted(corpus[last_word].items(),
                                               key=lambda x: x[1]))
                # Make a list of words from it.
                word_list = list(word_dict.keys())
                # If this is the last word in the sentence prefer words that
                # statistically has few words following it
                if n_words == 1:
                    if len(word_list) > 1:
                        for word in word_list:
                            if '\n' not in word:
                                word_list.remove(word)
                if (len(word_list) > 0):
                    # Most used first.
                    word_list.reverse()
                    # Get a random index into the list
                    widx = random.randint(0, len(word_dict) - 1)
                    if widx == 0:
                        word = word_list[0]
                    else:
                        # Choose a word between the start and that index.
                        word = random.choice(word_list[0:widx])

                    word, count = prepare_word(ret, word, newline)
                    if word is not None:
                        ret += word
                    if count:
                        n_words -= 1

                    last_word = word
            else:
                last_word = None

    return (ret)


def get_last_word(text):
    """
    # Return the last word in a string including last newline.

    :param text: String to search.
    :type text: str
    """
    ret = re.search(r'([\w\']+[-\w+]*)\W*$', text)
    if ret is not None:
        ret = ret.group(1)
        if text.endswith('\n'):
            ret += '\n'
    return (ret)


def add_string(text, string, capitalize):
    """
    Add a string to the text while taking care of capitalisation.

    :param text: text to add string to.
    :type text: str
    :param string: Word to add.
    :type string: str.
    """
    if capitalize:
        text += string[0].upper() + string[1:]
    else:
        text += string
    return (text)


def main():
    """
    Create a dictionary of word associations for later use in a markov
    generator and save it as a file.
    """
    # Parse command line
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-v', '--verbose',
                            action='store_true', dest='verbose', default=False,
                            help='Be verbose.')
    arg_parser.add_argument('-o', '--output', type=argparse.FileType('w'),
                            dest='outfile', default=None,
                            help='Write output to a this file.')
    arg_parser.add_argument('-t', '--template', type=argparse.FileType('r'),
                            dest='tpl_file', default=None,
                            help='Use this file as template.')
    arg_parser.add_argument('corpusfile', type=argparse.FileType('r'),
                            help='Text file to process.')
    args = arg_parser.parse_args()

    random.seed()
    # Load JSON Markov seed corpus.
    corpus = json.load(args.corpusfile)

    if args.tpl_file is not None:
        # Load a template file.
        template = args.tpl_file.read()
    else:
        # Default to creating 3 word title and 150 words Markov.
        template = '**{.!3}**\n\n{.50}\n'

    text = ''
    blocks = list()
    newline = False
    last_word = None
    capitalize = False

    for tpl_token in re.split(r'({[^}]+})', template):
        # Not a template command token.
        if '{' in tpl_token:
            # Allow newlines?
            if '!' in tpl_token:
                newline = False
            else:
                newline = True

            if '.' in tpl_token:
                capitalize = True
            else:
                capitalize = False

            # Get last word for the Markov generator.
            last_word = get_last_word(text)
            # Convert the numerical part of the token.
            value = int(tpl_token.strip('{}!.'))

            # Reference or new Markov string?
            if value > 0:
                if args.verbose:
                    print('Generating ' + str(value) + ' words.')
                # Keep a list of generated block.
                # Insert Markov string.
                blocks.append(markov_gen(last_word, newline, value, corpus))
                text = add_string(text, blocks[-1], capitalize)
            else:
                # Insert previous string.
                value = abs(value)
                if value > len(blocks):
                    exit('Reference to unknown block: ' + str(value) + '.')
                blocks.append(blocks[value - 1])
                text = add_string(text, blocks[-1], capitalize)
        else:
            text += tpl_token

    if (args.verbose) and (args.outfile is None):
        print()

    if args.outfile is None:
        print(text)
    else:
        args.outfile.write(text)


if __name__ == '__main__':
    main()
