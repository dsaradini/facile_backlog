import os
import random
import re
import string

TEST_DATA = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')

with open(os.path.join(TEST_DATA, "lorem.txt"), "r") as f:
    # striping lowering and all those stuff may be done in the original
    # lorem.txt file
    data = f.read().decode('utf-8')
    data = re.sub(r"""[\.,\n\r'"]""", "", data)
    LOREM_WORDS = map(lambda w: w.lower(), data.split(" "))


def rand_lorem_word():
    """
    Return a random word
    """
    return random.choice(LOREM_WORDS)


def rand_lorem_phrase(min=1, max=100):
    """
    Return a random phrase containing 'n' words.
    where 'n' is contained between 'min' and 'max'
    """
    max = random.randrange(min - 1, max)
    phrase = rand_lorem_word().capitalize()
    for i in range(max):
        x = random.randint(0, 20)
        if x == 1:
            phrase = u"{0}. {1}".format(phrase, rand_lorem_word().capitalize())
        elif x < 4:
            phrase = u"{0}, {1}".format(phrase, rand_lorem_word())
        else:
            phrase = u"{0} {1}".format(phrase, rand_lorem_word())
    return phrase[:-1] + "."


def rand_color():
    """
    Return a random color string between "#000000" and "#ffffff"
    """
    return "#{0:0>6x}".format(random.randint(0, 16777215))


def rand_ascii(min_val, max_val):
    return "".join([random.choice(string.ascii_letters)
                    for i in range(random.randint(min_val, max_val))])


def rand_domain():
    return "{0}.{1}".format(rand_ascii(4, 20), rand_ascii(2, 4))


def rand_email():
    return "{0}@{1}".format(rand_ascii(4, 50), rand_domain())