# -*- coding: utf8 -*-

from ctypes import c_int32
import struct
import zlib


# import ctypes
# import array
# import string
PACKET_HEAD_SIZE = 4


def tean(k, v, N=32):
    y = c_int32(v[0])
    z = c_int32(v[1])
    delta = 0x9E3779B9
    i_sum = c_int32(0)    
    if(N > 0):  # 加密        
        limit = c_int32(delta * N)
        while i_sum.value != limit.value:
            y.value += ((z.value << 4) ^ (z.value >> 5)) + (z.value ^ i_sum.value) + k[i_sum.value & 3]
            i_sum.value += delta
            z.value += ((y.value << 4) ^ (y.value >> 5)) + (y.value ^ i_sum.value) + k[(i_sum.value >> 11) & 3];
    else:  # 解密
        i_sum = c_int32(delta * (-N))
        while i_sum.value != 0:
            z.value -= ((y.value << 4) ^ (y.value >> 5)) + (y.value ^ i_sum.value) + k[(i_sum.value >> 11) & 3];
            i_sum.value -= delta;
            y.value -= ((z.value << 4) ^ (z.value >> 5)) + (z.value ^ i_sum.value) + k[i_sum.value & 3];
    v[0] = y.value
    v[1] = z.value

class bytestream_exception:
    """读流异常类,当超过位置时抛出"""
    pass

class bytestream:
    """description of class"""
  
    def __init__(self):
        self.bytes = ''
        self.rpos = 0
        
    def __len__(self):
        return len(self.bytes)

    def check_last_unread_size(self, size):
        if len(self.bytes) - self.rpos < size:
            raise bytestream_exception()

    def write_int8(self, data):
        self.bytes += struct.pack('b', data)  
        return struct.calcsize('b')      
        
    def read_int8(self):
        self.check_last_unread_size(struct.calcsize('b'))
        val = struct.unpack_from('b', self.bytes, self.rpos)
        self.rpos += struct.calcsize('b')
        return val[0]
        
    def write_uint8(self, data):
        self.bytes += struct.pack('B', data)
        return struct.calcsize('B')
        
    def read_uint8(self):
        self.check_last_unread_size(struct.calcsize('B'))
        val = struct.unpack_from('B', self.bytes, self.rpos)
        self.rpos += struct.calcsize('B')
        return val[0]
        
    def write_int16(self, data):
        self.bytes += struct.pack('h', data)
        return struct.calcsize('h')
        
    def read_int16(self):
        self.check_last_unread_size(struct.calcsize('h'))
        val = struct.unpack_from('h', self.bytes, self.rpos)
        self.rpos += struct.calcsize('h')
        return val[0]
        
    def write_uint16(self, data):
        self.bytes += struct.pack('H', data)
        return struct.calcsize('H')
        
    def read_uint16(self):
        self.check_last_unread_size(struct.calcsize('<H'))
        val = struct.unpack_from('H', self.bytes, self.rpos)
        self.rpos += struct.calcsize('H')
        return val[0]
        
    def write_int32(self, data):
        self.bytes += struct.pack('i', data)
        return struct.calcsize('i')
        
    def read_int32(self):
        self.check_last_unread_size(struct.calcsize('i'))
        val = struct.unpack_from('i', self.bytes, self.rpos)
        self.rpos += struct.calcsize('i')
        return val[0]
        
    def write_uint32(self, data):
        self.bytes += struct.pack('I', data)
        return struct.calcsize('I')
        
    def read_uint32(self):
        self.check_last_unread_size(struct.calcsize('I'))
        val = struct.unpack_from('I', self.bytes, self.rpos)
        self.rpos += struct.calcsize('I')
        return val[0]
    
    def write_float(self, data):
        self.bytes += struct.pack('f', data)
        return struct.calcsize('f')
        
    def read_float(self):
        self.check_last_unread_size(struct.calcsize('f'))
        val = struct.unpack_from('f', self.bytes, self.rpos)
        self.rpos += struct.calcsize('f')
        return val[0]
        
    def write_int64(self, data):
        self.bytes += struct.pack('q', data)
        return struct.calcsize('q')
        
    def read_int64(self):
        self.check_last_unread_size(struct.calcsize('q'))
        val = struct.unpack_from('q', self.bytes, self.rpos)
        self.rpos += struct.calcsize('q')
        return val[0]
        
    def write_uint64(self, data):
        self.bytes += struct.pack('Q', data)
        return struct.calcsize('Q')
        
    def read_uint64(self):
        self.check_last_unread_size(struct.calcsize('Q'))
        val = struct.unpack_from('Q', self.bytes, self.rpos)
        self.rpos += struct.calcsize('Q')
        return val[0]
    
    def write_double(self, data):
        self.bytes += struct.pack('d', data)
        return struct.calcsize('d')
        
    def read_double(self):
        self.check_last_unread_size(struct.calcsize('d'))
        val = struct.unpack_from('d', self.bytes, self.rpos)
        self.rpos += struct.calcsize('d')
        return val[0]
        
    def write_str(self, data, size=0):
        if size == 0:
            total_size = 0  # #write in buffer total size
            total_size += self.write_uint16(len(data) + 1)
            self.bytes += data        
            self.write_uint8(0)
            return total_size + len(data) + 1
        else:
            if len(data) > size:
                self.bytes += data[0:size - 1]
            else:
                self.bytes += data
                count = size - len(data) - 1
                while count > 0:
                    self.write_uint8(0)
                    count = count - 1
            self.write_uint8(0)
            return size
        
    def read_str(self, size=0):
        val = ''
        if size == 0:
            count = self.read_uint16()
            self.check_last_unread_size(count)
            val = self.bytes[self.rpos:self.rpos + count - 1] 
            self.rpos += count
            return val
        else:
            self.check_last_unread_size(size)
            val = self.bytes[self.rpos:self.rpos + size]
            self.rpos += size
            # val = struct.unpack_from('s',val,0)[0]
            if -1 == val.find('\0'):
                return val
            else:
                return val[0:val.index('\0')]            
    
    def write(self, fmt, data):
        self.bytes += struct.pack(fmt, data)
        return struct.calcsize(fmt)
        
    def read(self, fmt):
        self.check_last_unread_size(struct.calcsize(fmt))
        val = struct.unpack_from(fmt, self.bytes, self.rpos)
        self.rpos += struct.calcsize(fmt)
        return val    

class packet(bytestream):
    """"""   
    
    def __init__(self, cmd=0):     
        bytestream.__init__(self)   
        self.size = -1
        self.optcode = -1
        if cmd != 0:
            self.write_uint16(0)        
            self.write_uint16(cmd)  
            
    def __repr__(self):
        """打印出包"""
        strs = []
        for i in self.bytes[4:]:
            strs.append('%.2x' % struct.unpack_from('B', i, 0))
            
        return 'packet[%u,%u]:' % (self.getLength(), self.getOptcode()) + ','.join(strs)  

    def getLength(self):
        """packet head length , must be eq len(self.bytes)"""
        if len(self.bytes) < 2:
            return None
        if self.size == -1:
            self.size = struct.unpack_from('H', self.bytes, 0)[0] 
        return self.size    
    
    def getOptcode(self):
        if len(self.bytes) < PACKET_HEAD_SIZE:
            return None
        # if self.optcode == -1:
            # self.optcode = struct.unpack_from('H',self.bytes,2)[0]
        # return self.optcode
        return struct.unpack_from('H', self.bytes, 2)[0]
    
    def getBodyLength(self):
        assert len(self.bytes) >= PACKET_HEAD_SIZE
        return len(self.bytes) - PACKET_HEAD_SIZE
    
    def reset(self):        
        self.rpos = PACKET_HEAD_SIZE
        return self
    
    def updateHead(self):
        assert len(self.bytes) >= PACKET_HEAD_SIZE
        pkt_len = struct.pack('H', len(self.bytes))
        self.bytes = pkt_len + self.bytes[2:]
        # self.bytes[0] = pkt_len[0]
        # self.bytes[1] = pkt_len[1]            
        
    def decompress(self):
        # 忽略包头后解圧缩
        assert self.rpos == 4
        dst_str = zlib.decompress(self.bytes[self.rpos:])
        self.bytes = self.bytes[:self.rpos] + dst_str
        self.size = len(dst_str) + self.rpos
    
    def tea_encode(self, tea_k):
        tea_v = [0, 0]
        pos = 2  # 包头中的包长不需要加解密
        end_bytes = self.bytes[0: 2]
        while (pos + 8) <= len(self.bytes):
            tea_v[0] = struct.unpack_from('i', self.bytes, pos)[0]
            pos += 4
            tea_v[1] = struct.unpack_from('i', self.bytes, pos)[0]
            pos += 4
            tean(tea_k, tea_v, 16)
            end_bytes += struct.pack('i', tea_v[0])
            end_bytes += struct.pack('i', tea_v[1])
        end_bytes += self.bytes[pos:]
        self.bytes = end_bytes
    
    def tea_decode(self, tea_k):
        tea_v = [0, 0]
        pos = 2  # 包头不需要加解密
        end_bytes = self.bytes[0: 2]
        while (pos + 8) <= len(self.bytes):
            tea_v[0] = struct.unpack_from('i', self.bytes, pos)[0]
            pos += 4
            tea_v[1] = struct.unpack_from('i', self.bytes, pos)[0]
            pos += 4
            tean(tea_k, tea_v, -16)
            end_bytes += struct.pack('i', tea_v[0])
            end_bytes += struct.pack('i', tea_v[1])
        end_bytes += self.bytes[pos:]
        self.bytes = end_bytes
    
    def is_ok(self):
        return self.getLength() == len(self.bytes)
       
    def parsefrom(self, data, size):
        """根据包的状态进行读取数据,并返回读取后剩下的数据"""
        assert len(data) > 0
        if len(data) < size:
            size = len(data)
        self.bytes += data[0:size]
        return data[size:]       

#######################
# #tea测试
# test_tea_v = [24123,786456]
# test_tea_k = [1,2,3,4]
# tean(test_tea_k,test_tea_v,32)
# print test_tea_v[0],test_tea_v[1]
# tean(test_tea_k,test_tea_v,-32)
# assert test_tea_v[0] == 24123
# assert test_tea_v[1] == 786456
# print 'OK'

