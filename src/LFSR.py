"""
    Created by mbenlioglu on 10/30/2017
"""
from collections import deque
import numpy as np
import copy


def generate_key(polynomial, init_state=None):
    """
    Create key using given polynomial and determine whether the polynomial by counting number of states generated
    :param polynomial: Binary string representing the connection polynomial
    :type polynomial: str
    :param init_state: binary string representing initial state of the key generation
    :type init_state: str
    :raises ValueError if init_state doesn't match polynomial degree or any of the strings are not binary
    :return:
    """
    degree = len(polynomial) - 1

    ini = init_state if init_state is not None else '0' * (degree - 1) + '1'
    ini = [int(x) for x in ini]
    if len(ini) != degree:
        raise ValueError("Degrees don't match")

    xor_indices = []
    for i, n in enumerate(polynomial[1:]):
        if n == '1':
            xor_indices.append(i)

    key = []
    ini_deque = deque(ini)
    cur_state = deque(ini)
    while True:
        el = sum(cur_state[x] for x in xor_indices) % 2  # xor the elements in the indices determined by the polynomial

        key.append(cur_state.pop())
        cur_state.appendleft(el)
        if ini_deque == cur_state:  # full cycle completed
            break
    return key


def berlekamp_massey(data):
    """
    Implementation of berlekamp-massey algorithm that finds the minimal LFSR and minimal polynomial to generate given
    data
    :param data: list of 1s and 0s
    :type data: list[int]
    :return:
    """
    n = len(data)
    c_x, b_x = np.zeros(n, dtype=np.int), np.zeros(n, dtype=np.int)
    c_x[0], b_x[0] = 1, 1
    l, m, i = 0, -1, 0
    while i < n:
        v = data[(i - l):i]
        v = v[::-1]
        cc = c_x[1:l + 1]
        delta = (data[i] + np.dot(v, cc)) % 2
        if delta == 1:
            temp = copy.copy(c_x)
            p = np.zeros(n, dtype=np.int)
            for j in range(0, l):
                if b_x[j] == 1:
                    p[j + i - m] = 1
            c_x = (c_x + p) % 2
            if l <= 0.5 * i:
                l = i + 1 - l
                m = i
                b_x = temp
        i += 1
    c_x = c_x.tolist()
    ind = 0
    for x in c_x[::-1]:
        if x == 0:
            ind += 1
        else:
            break
    c_x = c_x[:-ind]
    return len(c_x)-1, c_x


def break_partially_known(cipher, ends_with):
    """
    Extract plain text, connection polynomial and initial state from partially known cipher text
    :param cipher: integer array of 1s and 0s representing message
    :type cipher: list[int]
    :param ends_with: string that is known to be end of message
    :type ends_with: str
    :return:
    """
    binary_str = ''.join(format(ord(x), 'b').zfill(7) for x in ends_with)
    len_of_known = len(binary_str)
    partial_cipher = cipher[-len_of_known:]
    partial_key = [(partial_cipher[i] + int(binary_str[i])) % 2 for i in range(len(partial_cipher))]
    print partial_key
    l, c_x = berlekamp_massey(partial_key)

    # create initial state from known part get key accordingly
    # note that order of the key assumes known part is at the beginning.
    key = deque(generate_key(''.join(str(x) for x in c_x), ''.join(str(x) for x in partial_key[l-1::-1])))

    # Rotate the key so that key order matches cipher order
    key.rotate(-len_of_known)
    key = list(key)[-len(cipher):]

    extracted_plain_binary = ''.join([str((cipher[i] + key[i]) % 2) for i in range(len(cipher))])

    return ''.join(str(x) for x in c_x), key, \
           ''.join(chr(int('0'+extracted_plain_binary[i:i+7], 2)) for i in range(0, len(extracted_plain_binary), 7))
