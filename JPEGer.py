from format import *
import utils


class JPEGer:
    def __init__(self):
        # DHT AC | DC
        self.huffmanDC = {}
        self.huffmanAC = {}
        # DQT: Y | Cr, Cb / other
        self.DQT_table = {}
        # quantization component
        self.Q_component = {}
        # sampling
        self.sample = {}
        # huffman component
        self.huffman_component = {}
        # three component
        self.YCrCb = {}
        # reverse (key, val) of huffman table
        self.re_huffmanDC = {}
        self.re_huffmanAC = {}
        # objective data
        self.data = []
        # APP1
        self.app1 = b''
        # other app
        self.app = []
        # SOF0
        self.SOF0 = b''
        # DRI
        self.DRI = b''
        # SOS
        self.SOS = b''
        # SOI
        self.SOI = b'\xFF\xD8'
        # EOI
        self.EOI = b'\xFF\xD9'
        # raw DQT
        self.DQT = b''
        # DHT
        self.DHT = b''
        # COM
        self.COM = []
        # zip data
        self.other_data = b''
        # bit data
        self.bit_data = ''
        # other info
        self.width = 0
        self.height = 0
        self.interval = 0

    @staticmethod
    def getSOI(data: bytes):
        """ Start of Image"""
        assert data == b'\xFF\xD8', 'Invalid SOI'

    @staticmethod
    def TIFFHeader(data: bytes):
        byte_align = data[0:2]  # byte order II / MM [2 bytes]
        tag_mark = data[2:4]  # Tag Mark [2 bytes]
        if byte_align == b'II':
            order = 'little'
            assert tag_mark == b'\x2a\x00', 'Invalid tag mark'
        else:
            order = 'big'
            assert tag_mark == b'\x00\x2a', 'Invalid tag mark'
        # Image File Directory
        IFD = data[4:8]
        return int.from_bytes(IFD, byteorder=order), order

    @staticmethod
    def DirectoryEntry(data: bytes, order='big'):
        """
        Exif Tag
        Also See
        https://exiftool.org/TagNames/EXIF.html
        """
        assert len(data) == 12, 'Invalid Directory Entry'
        exif_tag = data[0:2]

        type = int.from_bytes(data[2:4], byteorder=order)  # Component Type
        num_component = int.from_bytes(data[4:8], byteorder=order)  # number of component
        val_or_offset = int.from_bytes(data[8:12], byteorder=order)  # entry value or value offset
        data_len = num_component * COMPONENT_TYPE[type]
        return data_len, val_or_offset, exif_tag

    @staticmethod
    def DirectoryData(data: bytes, val_offset: int, data_len: int):
        if data_len <= 4:
            res = hex(val_offset).replace('0x', '').replace('00', '')
            return int(res, 16)
        else:
            return data[val_offset - 8: val_offset - 8 + data_len]

    @staticmethod
    def ImageFileDirectory(data: bytes, order='big'):
        num_dirs = int.from_bytes(data[0:2], byteorder=order)
        for i in range(num_dirs):
            entry = data[2 + 12 * i:2 + 12 * (i + 1)]
            data_len, val_off, exif_tag = JPEGer.DirectoryEntry(entry, order)
            val = JPEGer.DirectoryData(data, val_off, data_len)
            # print(TAG_TYPE[exif_tag], 'value:', val)
        offset_nextIFD = int.from_bytes(data[2 + 12 * num_dirs:2 + 12 * num_dirs + 4], byteorder=order)
        return offset_nextIFD

    def getCOM(self, data: bytes):
        """ comment """
        assert data[0:2] == b'\xFF\xFE'
        ext_length = int.from_bytes(data[2:4], byteorder='big')
        comment = data[4:ext_length + 2]
        self.COM.append(comment)
        return ext_length + 2

    def getAPP1(self, data: bytes):
        """ Exif Format """
        assert data[0:2] == b'\xFF\xE1', 'Invalid APP1 Marker'
        ext_length = data[2:4]
        identifier = data[4:10]
        assert identifier == b'Exif\x00\x00', 'Invalid Exif'
        TIFF_Header = data[10:18]
        offset, order = JPEGer.TIFFHeader(TIFF_Header)
        ext_length = int.from_bytes(ext_length, byteorder=order)
        assert len(data) >= ext_length + 4
        nextIFD = JPEGer.ImageFileDirectory(data[10 + offset:10 + offset + ext_length], order)
        while nextIFD != 0:
            nextIFD = JPEGer.ImageFileDirectory(data[10 + nextIFD:10 + nextIFD + ext_length], order)
        self.app1 = data[0:ext_length + 2]
        return ext_length + 2

    @staticmethod
    def getAPP0(data: bytes):
        """ JFIF Format """
        assert data[0:2] == b'\xFF\xE0', 'Invalid APP0 Marker'
        ext_length = int.from_bytes(data[2:4], byteorder='big')
        identifier = data[4:10]
        assert identifier == b'JFIF\x00\x00' or identifier == b'JFIF\x00\x01', 'Invalid JFIF'
        return ext_length + 2

    def getAPP(self, data: bytes, order='big'):
        assert b'\xFF\xE1' <= data[0:2] <= b'\xFF\xEE', 'Invalid APP Marker'
        ext_length = int.from_bytes(data[2:4], byteorder=order)
        self.app.append(data[0:ext_length + 2])
        return ext_length + 2

    def getDQT(self, data: bytes, order='big'):
        """ Define Quantization Table """
        assert data[0:2] == b'\xFF\xDB', 'Invalid DQT'
        ext_length = int.from_bytes(data[2:4], byteorder=order)
        k = 0
        while k < ext_length - 2:
            value, id = data[4 + k] & 0xf0, data[4 + k] & 0x0f
            assert id <= 3, 'Invalid DQT table'
            k += 1
            Qtable = []
            rounds = 64 if value == 0 else 128
            for i in range(rounds):
                Qtable.append(data[4 + k + i])
            k += rounds
            self.DQT_table[id] = utils.InverseZZ(np.array(Qtable).reshape(8, 8))
        self.DQT = data[0:ext_length + 2]
        return ext_length + 2

    def getSOF0(self, data: bytes, order='big'):
        """ Start of Frame """
        assert data[0:2] == b'\xFF\xC0', 'Invalid SOF0'
        ext_length = int.from_bytes(data[2:4], byteorder=order)
        accuracy = data[4]
        assert accuracy == 8, 'Invalid precision'
        height, width = int.from_bytes(data[5:7], order), int.from_bytes(data[7:9], order)
        self.width = width
        self.height = height
        assert height > 0 and width > 0, 'Invalid dimension'
        # 1:Gray | 3:CrCb | 4:CMYK
        type = data[9]
        assert type == 3, 'Invalid CrCb(others not support!)'
        # Y U V | x:y sampling
        for i in range(3):
            ID, coefficient, tab_num = data[10 + i * 3], data[11 + i * 3], data[12 + i * 3]
            self.Q_component[ID] = tab_num
            self.sample[ID] = (coefficient >> 4, coefficient & 0x0F)
        self.SOF0 = data[0:ext_length + 2]
        return ext_length + 2

    def getDRI(self, data: bytes, order='big'):
        """ # Define Restart Interval """
        assert data[0:2] == b'\xFF\xDD', 'Invalid DRI'
        ext_length = int.from_bytes(data[2:4], byteorder=order)
        interval = int.from_bytes(data[4:6], byteorder=order)
        self.interval = interval
        self.DRI = data[0: ext_length + 2]
        return ext_length + 2

    @staticmethod
    def AnalyseHT(node: bytes, content: bytes):
        """
         Parser HT
         Also See
         https://zhuanlan.zhihu.com/p/72044095
        """
        res = {}
        start = 0
        value = 0
        n_bit = 0
        for i in node:
            n_bit += 1
            if i == 0:
                continue
            for c in range(i):
                res[bin(value).replace('0b', '').zfill(n_bit)] = content[start]
                value += 1
                start += 1
            value = value << 1
        return res

    def getDHT(self, data: bytes, order='big'):
        """ Define Huffman Table """
        assert data[0:2] == b'\xFF\xC4', 'Invalid DHT'
        ext_length = int.from_bytes(data[2:4], byteorder=order)
        i = 0
        while i < ext_length - 2:
            assert data[4 + i] & 0b11100000 == 0, 'Invalid HT'
            # HT_type 0 : DC table | 1 : AC table
            HT_num, HT_type = data[4 + i] & 0x07, data[4 + i] >> 4
            assert HT_type == 0 or HT_type == 1, 'Invalid HT type'
            total_node = sum(data[5 + i:21 + i])
            assert total_node <= 256, 'Invalid Node Number'
            content = data[21 + i:21 + total_node + i]
            code = JPEGer.AnalyseHT(data[5 + i:21 + i], content)
            if HT_type == 1:
                self.huffmanAC[HT_num] = code
            else:
                self.huffmanDC[HT_num] = code
            i += (1 + 16 + total_node)
        self.ReverseHuffman()
        self.DHT = data[0:ext_length + 2]
        return ext_length + 2

    def getSOS(self, data: bytes, order='big'):
        """ Start of Scan """
        assert data[0:2] == b'\xFF\xDA', 'Invalid SOS'
        ext_length = int.from_bytes(data[2:4], byteorder=order)
        number = data[4]
        assert number == 3, 'Invalid Y U V'
        self.SOS = data[0:ext_length + 2]
        for i in range(3):
            # Component : 1 = Y | 2 = Cb | 3 = Cr
            component_id, AC_tab, DC_tab = data[5 + i * 2], data[6 + i * 2] & 0x0f, (data[6 + i * 2] & 0xf0) >> 4
            self.huffman_component[component_id] = (DC_tab, AC_tab)

        self.YCrCb, acc = self.AnalysisZipData(data[ext_length + 2:-2])
        assert data[-2:] == b'\xFF\xD9', 'Invalid EOI'
        self.other_data = data[acc: -2]
        return len(data)

    def AnalysisZipData(self, data: bytes):
        # Y_DC, Y_AC | U_DC,U_AC | V_DC,V_AC
        self.bit_data = utils.convert_bit_string(data)
        bit_length = len(self.bit_data)

        all_block = {0: [], 1: [], 2: []}
        previous = [0, 0, 0]
        rounds = self.interval
        block_width = self.width // 8
        block_height = self.height // 8
        i = 0
        for y in range(0, block_height):
            for x in range(0, block_width):
                if rounds != 0 and (y * block_width + x) % rounds == 0:
                    previous = [0, 0, 0]
                    if i % 8 != 0:
                        padding = 8 - i % 8
                        assert self.bit_data[i:i + padding] == '1' * padding, 'Invalid padding'
                        i += padding
                for k in range(3):
                    i, block = self.ExtractBlock(i, self.huffman_component[k + 1][0],
                                                 self.huffman_component[k + 1][1], previous[k])
                    previous[k] = block[0]
                    all_block[k].append(block)
        if i % 8 != 0:
            padding = 8 - i % 8
            assert self.bit_data[i:i + padding] == '1' * padding, 'Invalid padding'
            i += padding
        assert i <= bit_length, 'bit data overflow'
        return all_block, i

    def ExtractBlock(self, offset: int, DC_flag: int, AC_flag: int, previous: int):
        temp = np.zeros(64, dtype=int)
        """ extract DC """
        key = JPEGer.ExtractKey(self.bit_data[offset: offset + 0x10], self.huffmanDC[DC_flag])
        offset += len(key)
        DC_length = self.ExtractDC(key, DC_flag)
        assert DC_length <= 11, 'DC coefficient is more than 11!'
        DC = JPEGer.RestoreValue(self.bit_data[offset: offset + DC_length])
        offset += DC_length
        temp[0] = DC + previous
        """ extract  AC """
        i = 1
        while i < 64:
            key = self.ExtractKey(self.bit_data[offset: offset + 0x10], self.huffmanAC[AC_flag])
            offset += len(key)
            zero, AC_length = self.ExtractAC(key, AC_flag)
            assert i + zero <= 64, 'ZRL exceeded 64'
            i += zero
            if AC_length == 0 and zero == 0:
                break
            else:
                AC = JPEGer.RestoreValue(self.bit_data[offset:offset + AC_length])
                offset += AC_length
                temp[i] = AC
            i += 1
        return offset, temp

    @staticmethod
    def ExtractKey(data: str, dictionary: dict):
        key = ''
        i = 0
        max_len = len(max(dictionary.keys()))
        while key not in dictionary and i <= max_len:
            key += data[i]
            i += 1
        assert i <= max_len, 'overflow!'
        return key

    def ExtractDC(self, key: str, table_num):
        return self.huffmanDC[table_num][key]

    def ExtractAC(self, key: str, table_num):
        value = self.huffmanAC[table_num][key]
        return value >> 4, value & 0x0f

    @staticmethod
    def RestoreValue(data: str) -> int:
        if len(data) == 0:
            return 0
        value = int(data, 2)
        if value < (1 << (len(data) - 1)):
            return value - (1 << len(data)) + 1
        else:
            return value

    def RecoverIDCT(self, b: list, flag: int):
        Block = []
        for block in b:
            # re-Quantization
            matrix = block.reshape(8, 8)
            q_res = utils.InverseZZ(matrix) * self.DQT_table[flag]
            # IDCT
            re_idct = utils.idct(q_res)
            re_idct.astype(np.int)
            Block.append(np.round(re_idct).astype(np.int))
        return Block

    def ConvertDCT(self, b: list, flag: int):
        Block = []
        for block in b:
            dct = utils.dct(block)
            res = dct / self.DQT_table[flag]
            matrix = np.round(res).astype(np.int)
            vector = utils.ZZEncoder(matrix).flatten()
            Block.append(vector)
        return Block

    def ReverseHuffman(self):
        for it in self.huffmanDC:
            self.re_huffmanDC[it] = {val: key for key, val in self.huffmanDC[it].items()}
        for it in self.huffmanAC:
            self.re_huffmanAC[it] = {val: key for key, val in self.huffmanAC[it].items()}

    def ConvertToStream(self):
        Y, Cb, Cr = self.YCrCb[0], self.YCrCb[1], self.YCrCb[2]
        bit_stream = ''
        previous = [0, 0, 0]
        rounds = 0
        for c in zip(Y, Cb, Cr):
            if rounds != 0 and rounds % self.interval == 0:
                previous = [0, 0, 0]
                if len(bit_stream) % 8 != 0:
                    padding = 8 - len(bit_stream) % 8
                    bit_stream += '1' * padding
                self.data.append(b''.join(utils.string2byte(bit_stream)))
                bit_stream = ''
            for k in range(3):
                sub_stream, previous[k] = self.ConvertBlock(c[k], previous[k], self.huffman_component[k + 1][0])
                bit_stream += sub_stream
            rounds += 1
        if len(bit_stream) % 8 != 0:
            padding = 8 - len(bit_stream) % 8
            bit_stream += '1' * padding
        self.data.append(b''.join(utils.string2byte(bit_stream)))
        return

    def ConvertBlock(self, data: list, previous: int, flag: int):
        assert len(data) == 64, 'Invalid block'
        """ DC part """
        DC = data[0] - previous
        length = utils.bit_length(abs(DC))
        assert length <= 11, 'DC coefficient length more than 11'
        if DC < 0:
            DC += (1 << length) - 1
        code = self.re_huffmanDC[flag][length]
        stream = code
        stream += utils.int2stringbit(DC, length)
        """ AC part """
        k = 1
        while k < 64:
            zero_number = 0
            while k < 64 and data[k] == 0:
                zero_number += 1
                k += 1
            if k == 64:
                stream += self.re_huffmanAC[flag][0x00]
                return stream, data[0]
            while zero_number >= 16:
                stream += self.re_huffmanAC[flag][0xF0]
                zero_number -= 16
            coef = data[k]
            length = utils.bit_length(abs(coef))
            if coef < 0:
                coef += (1 << length) - 1
            code = self.re_huffmanAC[flag][(zero_number << 4) | length]
            stream += code
            stream += utils.int2stringbit(coef, length)
            k += 1
        return stream, data[0]

    def HideDCT(self, data: str, p1: int, p2: int, number: int, once=False):
        assert 60 >= p1 >= 1 and 60 >= p2 >= 1, 'Invalid position'
        assert len(data) <= (self.height // 8) * (self.width // 8), 'Data is too long'
        assert 60 >= p1 >= 1 and 60 >= p2 >= 1, 'Invalid position'
        for i in range(len(data)):
            self.YCrCb[0][i][63] = 0
            self.YCrCb[0][i][62] = 0
            self.YCrCb[0][i][61] = 0
            if self.YCrCb[0][i][p1] == self.YCrCb[0][i][p2]:
                if data[i] == '0':
                    self.YCrCb[0][i][p2] += 1
                continue
            if data[i] == '1':
                if self.YCrCb[0][i][p1] < self.YCrCb[0][i][p2]:
                    self.YCrCb[0][i][p1], self.YCrCb[0][i][p2] = self.YCrCb[0][i][p2], self.YCrCb[0][i][p1]
            else:
                if self.YCrCb[0][i][p1] > self.YCrCb[0][i][p2]:
                    self.YCrCb[0][i][p1], self.YCrCb[0][i][p2] = self.YCrCb[0][i][p2], self.YCrCb[0][i][p1]
        if not once:
            self.DQT_table[0][6][7], self.DQT_table[0][7][6] = len(data) >> 8, len(data) & 0xff
        else:
            size = (self.DQT_table[0][6][7] << 8) + (self.DQT_table[0][7][6]) + len(data)
            self.DQT_table[0][6][7], self.DQT_table[0][7][6] = size >> 8, size & 0xff

        self.DQT_table[0][7][7] = number

    def ExtractFromDCT(self, p1: int, p2: int, length=None):
        if not length:
            length = (self.DQT_table[0][6][7] << 8) + (self.DQT_table[0][7][6])
        if length <= 0:
            return ''
        assert 60 >= p1 >= 1 and 60 >= p2 >= 1, 'Invalid position'
        assert 60 >= p1 >= 1 and 60 >= p2 >= 1, 'Invalid position'
        res = ''
        for i in range(length):
            if self.YCrCb[0][i][p1] >= self.YCrCb[0][i][p2]:
                res += '1'
            else:
                res += '0'
        return res

    def WriteDQT(self):
        """ modify DQT """
        data = [b'\xff', b'\xdb']
        length = len(self.DQT_table) + 2
        for key in self.DQT_table:
            length += len(self.DQT_table[key].flatten())
        data.append(length.to_bytes(2, 'big'))
        for id in self.DQT_table:
            data.append(id.to_bytes(1, 'big'))
            element = utils.ZZEncoder(self.DQT_table[id]).flatten()
            for it in element:
                data.append(int(it).to_bytes(1, 'big'))
        self.DQT = b''.join(data)

    def Write(self, file_name: str):
        self.ConvertToStream()
        self.WriteDQT()
        # I/O
        with open(file_name, 'wb') as f:
            f.write(self.SOI)
            f.write(self.app1)
            for it in self.app:
                f.write(it)
            f.write(self.DQT)
            f.write(self.SOF0)
            f.write(self.DRI)
            f.write(self.DHT)
            f.write(self.SOS)
            data = self.PadData()
            f.write(data)
            f.write(self.other_data)
            f.write(self.EOI)
        f.close()
        print('file write successfully!')

    def PadData(self):
        temp = []
        interval = [_.to_bytes(1, 'big') for _ in range(0xd0, 0xd8)]
        k = 0
        for it in self.data:
            temp.append(it)
            temp.append(b'\xff')
            temp.append(interval[k % 8])
            k += 1
        temp.pop()
        temp.pop()
        return b''.join(temp)
