import numpy as np

COMPONENT_TYPE = {1: 1,  # Unsigned Type
                  2: 1,  # ASCII String
                  3: 2,  # Unsigned Short
                  4: 4,  # Unsigned Long
                  5: 8,  # Unsigned Rational
                  6: 1,  # Signed Byte
                  7: 1,  # Undefined
                  8: 2,  # Signed Short
                  9: 4,  # Signed Long
                  10: 8,  # Signed Rational
                  11: 4,  # Signed Float
                  12: 8  # Double Float
                  }

TAG_TYPE = {b'\x01\x00': 'Image With',
            b'\x01\x01': 'Image Length',
            b'\x01\x02': 'Bits Per Sample',
            b'\x01\x03': 'Compression',
            b'\x01\x06': 'Photo Metric Interpretation',
            b'\x01\x12': 'Orientation',
            b'\x01\x15': 'Sample Per Pixel',
            b'\x01\x1a': 'X Resolution',
            b'\x01\x1b': 'Y Resolution',
            b'\x01\x28': 'ResolutionUnit',
            b'\x01\x31': 'Software',
            b'\x01\x32': 'ModifyDate',
            b'\x87\x69': 'ExifOffset',
            b'\x02\x01': 'ThumbnailOffset',
            b'\x02\x02': 'ThumbnailLength'}

IZZ = np.array([[0, 1, 5, 6, 14, 15, 27, 28],
                [2, 4, 7, 13, 16, 26, 29, 42],
                [3, 8, 12, 17, 25, 30, 41, 43],
                [9, 11, 18, 24, 31, 40, 44, 53],
                [10, 19, 23, 32, 39, 45, 52, 54],
                [20, 22, 33, 38, 46, 51, 55, 60],
                [21, 34, 37, 47, 50, 56, 59, 61],
                [35, 36, 48, 49, 57, 58, 62, 63]])

ZZ = np.array([[0, 1, 8, 16, 9, 2, 3, 10],
               [17, 24, 32, 25, 18, 11, 4, 5],
               [12, 19, 26, 33, 40, 48, 41, 34],
               [27, 20, 13, 6, 7, 14, 21, 28],
               [35, 42, 49, 56, 57, 50, 43, 36],
               [29, 22, 15, 23, 30, 37, 44, 51],
               [58, 59, 52, 45, 38, 31, 39, 46],
               [53, 60, 61, 54, 47, 55, 62, 63]])
