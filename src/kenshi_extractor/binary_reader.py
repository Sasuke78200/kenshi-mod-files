import struct

class BinaryReader:
    def __init__(self, fd):
        self.fd = fd

    def boolean(self):
        buffer = self.read_bytes(1)
        return struct.unpack('<?', buffer)[0]

    def s8(self):
        buffer = self.read_bytes(1)
        return struct.unpack('<b', buffer)[0]

    def s16(self):
        buffer = self.read_bytes(2)
        return struct.unpack('<h', buffer)[0]

    def s32(self):
        buffer = self.read_bytes(4)
        return struct.unpack('<i', buffer)[0]

    def s64(self):
        buffer = self.read_bytes(8)
        return struct.unpack('<q', buffer)[0]

    def u8(self):
        buffer = self.read_bytes(1)
        return struct.unpack('<B', buffer)[0]

    def u16(self):
        buffer = self.read_bytes(2)
        return struct.unpack('<H', buffer)[0]

    def u32(self):
        buffer = self.read_bytes(4)
        return struct.unpack('<I', buffer)[0]

    def u64(self):
        buffer = self.read_bytes(8)
        return struct.unpack('<Q', buffer)[0]

    def f32(self):
        buffer = self.read_bytes(4)
        return struct.unpack('<f', buffer)[0]

    def string(self):
        string_len = self.u32()
        return self.read_bytes(string_len).decode('utf-8')

    def string_raw(self):
        string_len = self.u32()
        return self.read_bytes(string_len)

    def read_bytes(self, n):
        return self.fd.read(n)

    def tell(self):
        return self.fd.tell()

    def seek(self, offset, whence):
        return self.fd.seek(offset, whence)

