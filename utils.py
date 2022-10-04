from format import *
import re
import os


def convert_bit_string(data: bytes):
    """ convert string data to bit string """
    res = ''
    flag = True
    for it in data:
        if not flag:
            if it == 0x00:
                res += bin(0xff).replace('0b', '').zfill(8)
            elif 0xd0 <= int(it) <= 0xd7:
                # RST n
                pass
            elif it == 0xff:
                # skip current 0xff
                pass
            else:
                # skip current 0xff
                res += bin(it).replace('0b', '').zfill(8)
            flag = True
            continue
        if it == 0xff:
            flag = False
            continue
        res += bin(it).replace('0b', '').zfill(8)
    return res


def bit_length(data: int):
    length = 0
    while data > 0:
        data >>= 1
        length += 1
    return length


def int2stringbit(data: int, length: int):
    if length == 0:
        return ''
    return bin(data).replace('0b', '').zfill(length)


def string2byte(data: str):
    str_list = re.findall(r'.{8}', data)
    res = []
    for it in str_list:
        value = int(it, 2).to_bytes(1, byteorder='big')
        if value == b'\xff':
            res.append(value)
            res.append(b'\x00')
            continue
        res.append(value)
    return res


def InverseZZ(block):
    zz = IZZ.flatten()
    return block.flatten()[zz].reshape([8, 8])


def ZZEncoder(block):
    zz = ZZ.flatten()
    return block.flatten()[zz].reshape([8, 8])


def GetByteFromFile(full_path: str):
    assert os.path.exists(full_path), 'path not exist!'
    with open(full_path, 'rb') as f:
        content = f.read()
    f.close()
    return content


def GetBitFromFile(full_path: str):
    assert os.path.exists(full_path), 'path not exist!'
    with open(full_path, 'rb') as f:
        content = f.read()
        res = ''
        for it in content:
            res += bin(it).replace('0b', '').zfill(8)
    f.close()
    return res
