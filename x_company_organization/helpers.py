import string
import random


def generate_random_string(seq=string.ascii_lowercase + string.digits, lengh=6):
    return ''.join(random.choice(seq) for _ in range(lengh))
