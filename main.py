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
import argparse
import os
import shutil
import utils
from JPEGer import JPEGer
import hashlib


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


def Hide(binary_bit: str, full_path: str, number, p1: int, p2: int, once=False):
    dir_name = 'pic'
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    content = utils.GetByteFromFile(full_path)
    jpeg = JPEGer()
    AnalysisJPEG(content, jpeg)
    jpeg.HideDCT(binary_bit, p1, p2, number, once)
    jpeg.Write(f'{dir_name}/pic{number}.jpg')


def Extract(full_path: str, p1: int, p2: int, length=None):
    content = utils.GetByteFromFile(full_path)
    jpeg = JPEGer()
    AnalysisJPEG(content, jpeg)
    if not length:
        length = jpeg.getHideLength()
    number = jpeg.getHideNumber()
    res = jpeg.ExtractFromDCT(p1, p2, min(length, 7500))
    return res, number, length


def single_point(p1: int, p2: int):
    dir_name = 'pic'
    block_number = 7500
    # hide information to picture
    binary_bit = utils.GetBitFromFile('./src/secret.py')
    block_size = len(binary_bit) // block_number
    padding = len(binary_bit) % block_number
    for i in range(block_size):
        Hide(binary_bit[block_number * i:block_number * (i + 1)], './src/pic.jpg', i, p1, p2)
    Hide(binary_bit[-padding:], './src/pic.jpg', block_size, p1, p2)
    # check
    calc(block_size + 1)


def single_extract(p1: int, p2: int, dir_name: str):
    list_dir = os.listdir(dir_name)
    res = {}
    for i in list_dir:
        s, num, length = Extract(os.path.join(dir_name, i), p1, p2)
        res[num] = s
    content = ''
    for i in range(len(list_dir)):
        content += res[i]
    with open('secret.py', 'wb') as f:
        f.write(b''.join(utils.string2byte(content)))
    f.close()
    check('./src/secret.py', './secret.py')


def pair_point(p1: int, p2: int, p3: int, p4: int):
    block_number = 7500
    dir_name = 'pic'
    d_block_number = block_number << 1
    binary_bit = utils.GetBitFromFile('./src/secret.py')
    block_size = len(binary_bit) // d_block_number
    padding = len(binary_bit) % d_block_number
    for i in range(block_size):
        Hide(binary_bit[block_number * 2 * i:block_number * (2 * i + 1)], './src/pic.jpg', i, p1, p2)
        Hide(binary_bit[block_number * (2 * i + 1):block_number * (2 * i + 2)], f'./{dir_name}/pic{i}.jpg', i, p3, p4)
    if padding <= block_number:
        Hide(binary_bit[-padding:], './src/pic.jpg', block_size, p1, p2)
    else:
        Hide(binary_bit[-padding:-padding + block_number], './src/pic.jpg', block_size, p1, p2)
        Hide(binary_bit[-padding + block_number:], f'./{dir_name}/pic{block_size}.jpg', block_size, p3, p4, True)
    calc(block_size + 1)


def pair_extract(p1: int, p2: int, p3: int, p4: int, dir_name: str):
    res = {}
    content = ''
    list_dir = os.listdir(dir_name)
    for it in list_dir:
        sub_s, num, length = Extract(os.path.join(dir_name, it), p1, p2)
        if length > 7500:
            s, num, length = Extract(os.path.join(dir_name, it), p3, p4, length - 7500)
        else:
            s, num, length = Extract(os.path.join(dir_name, it), p3, p4)
        res[num] = sub_s + s
    for i in range(len(list_dir)):
        content += res[i]
    with open('secret.py', 'wb') as f:
        f.write(b''.join(utils.string2byte(content)))
    f.close()
    check('./src/secret.py', './secret.py')


def clear_dir():
    if os.path.exists('pic'):
        shutil.rmtree('pic')
        os.mkdir('pic')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-hide1', '--hd1', type=str, help='hide with one pair of point')
    parser.add_argument('-hide2', '--hd2', type=str, help='hide with two pairs of point')
    parser.add_argument('-ext1', '--ext1', type=str, help='extract info from one pair')
    parser.add_argument('-ext2', '--ext2', type=str, help='extract info from two pairs')
    args = parser.parse_args()
    # hide
    h1 = args.hd1
    h2 = args.hd2
    # extract
    ext1 = args.ext1
    ext2 = args.ext2
    if h1 or ext1:
        if h1:
            point = h1.split(',')
        if ext1:
            point = ext1.split(',')
        assert len(point) == 2, 'count of point is invalid'
        if h1:
            single_point(int(point[0]), int(point[1]))
        if ext1:
            single_extract(int(point[0]), int(point[1]), 'pic')
    elif h2 or ext2:
        if h2:
            point = h2.split(',')
        if ext2:
            point = ext2.split(',')
        assert len(point) == 4, 'count of point is invalid'
        if h2:
            pair_point(int(point[0]), int(point[1]), int(point[2]), int(point[3]))
        if ext2:
            pair_extract(int(point[0]), int(point[1]), int(point[2]), int(point[3]), 'pic')


def calc(number):
    # old
    size = os.path.getsize('./src/pic.jpg')
    # new
    total = 0
    for i in range(number):
        path = f'pic/pic{i}.jpg'
        if not os.path.exists(path):
            continue
        sub_size = os.path.getsize(path)
        assert sub_size - size <= size * 0.05, 'size not meet requirement'
        total += sub_size
    print((total - size * number) / (size * number))


def check(file1: str, file2: str):
    with open(file1, 'rb') as f1:
        content1 = f1.read()
    f1.close()
    with open(file2, 'rb') as f2:
        content2 = f2.read()
    f2.close()
    assert hashlib.md5(content1).hexdigest() == hashlib.md5(content2).hexdigest(), 'Check Failed!'
    print('md5 is equal!')


if __name__ == '__main__':
    main()
