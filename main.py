# -*- coding: utf-8 -*-
"""
Decoder
decode the JPEG file, analysis the format of the picture
Also See
https://github.com/djh-sudo/JPEGer
@author:djh-sudo
if you have any question, pls contact me
at djh113@126.com
"""
import os
from JPEGer import JPEGer
import utils


def AnalysisJPEG(data: bytes, jpeg: JPEGer):
    assert len(data) >= 18, 'Invalid JPEG'
    jpeg.getSOI(data[0:2])
    if data[2:4] == b'\xFF\xE1':
        data_len = jpeg.getAPP1(data[2:])
    else:
        data_len = jpeg.getAPP0(data[2:])
    while data_len + 2 < len(data) and data[2 + data_len] == 0xFF:
        while b'\xFF\xE0' <= data[2 + data_len:4 + data_len] <= b'\xFF\xEE':
            data_len += jpeg.getAPP(data[2 + data_len:])
        if data[2 + data_len:4 + data_len] == b'\xFF\xDB':
            data_len += jpeg.getDQT(data[2 + data_len:])
        elif data[2 + data_len:4 + data_len] == b'\xFF\xC0':
            data_len += jpeg.getSOF0(data[2 + data_len:])
        elif data[2 + data_len:4 + data_len] == b'\xFF\xDD':
            data_len += jpeg.getDRI(data[2 + data_len:])
        elif data[2 + data_len:4 + data_len] == b'\xFF\xC4':
            data_len += jpeg.getDHT(data[2 + data_len:])
        elif data[2 + data_len:4 + data_len] == b'\xFF\xDA':
            data_len += jpeg.getSOS(data[2 + data_len:])
    assert data_len + 2 == len(data)
    return


def Hide(binary_bit: str, full_path: str, number, p1: int, p2: int):
    content = utils.GetByteFromFile(full_path)
    jpeg = JPEGer()
    AnalysisJPEG(content, jpeg)
    jpeg.HideDCT(binary_bit, p1, p2, number)
    jpeg.Write('pic{}.jpg'.format(number))


def Extract(full_path: str, p1: int, p2: int):
    content = utils.GetByteFromFile(full_path)
    jpeg = JPEGer()
    AnalysisJPEG(content, jpeg)
    res = jpeg.ExtractFromDCT(p1, p2)
    return res


def main():
    # hide information to picture
    binary_bit = utils.GetBitFromFile('./src/secret.py')
    block_size = len(binary_bit) // 7500
    padding = len(binary_bit) % 7500
    p1, p2 = 15, 16
    print(p1, p2)
    for i in range(block_size):
        Hide(binary_bit[7500 * i:7500 * (i + 1)], './src/pic.jpg', i, p1, p2)
    Hide(binary_bit[-padding:], './src/pic.jpg', block_size, p1, p2)
    # check
    calc(block_size + 1)
    # extract information from picture
    res = ''
    for i in range(block_size):
        res += Extract('./pic{}.jpg'.format(i), p1, p2)
    res += Extract('./pic{}.jpg'.format(block_size), p1, p2)
    with open('secret.py', 'wb') as f:
        f.write(b''.join(utils.string2byte(res)))
    f.close()


def calc(number):
    # old
    size = os.path.getsize('./src/pic.jpg')
    # new
    total = 0
    for i in range(number):
        path = f'./pic{i}.jpg'
        if not os.path.exists(path):
            continue
        sub_size = os.path.getsize(path)
        assert sub_size - size <= size * 0.05, 'size not meet requirement'
        total += sub_size
    print((total - size * number) / (size * number))


if __name__ == '__main__':
    main()
