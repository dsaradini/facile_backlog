import os
import random
import re

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

