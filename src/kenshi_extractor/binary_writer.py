import struct

from io import BufferedWriter

class BinaryWriter:
    def __init__(self, fd: BufferedWriter):
        self.fd = fd

    def boolean(self, value):
        buffer = struct.pack('<?', value)
        return self.write_bytes(buffer)

    def s8(self, value):
        buffer = struct.pack('<b', value)
        return self.write_bytes(buffer)

    def s16(self, value):
        buffer = struct.pack('<h', value)
        return self.write_bytes(buffer)

    def s32(self, value):
        buffer = struct.pack('<i', value)
        return self.write_bytes(buffer)

    def s64(self, value):
        buffer = struct.pack('<q', value)
        return self.write_bytes(buffer)

    def u8(self, value):
        buffer = struct.pack('<B', value)
        return self.write_bytes(buffer)

    def u16(self, value):
        buffer = struct.pack('<H', value)
        return self.write_bytes(buffer)

    def u32(self, value):
        buffer = struct.pack('<I', value)
        return self.write_bytes(buffer)

    def u64(self, value):
        buffer = struct.pack('<Q', value)
        return self.write_bytes(buffer)

    def f32(self, value):
        buffer = struct.pack('<f', value)
        return self.write_bytes(buffer)

    def string(self, value):
        encoded_value = value.encode()
        self.u32(len(encoded_value))
        return self.write_bytes(encoded_value)

    def write_bytes(self, b: bytes):
        return self.fd.write(b)

    def tell(self):
        return self.fd.tell()

    def seek(self, offset, whence):
        return self.fd.seek(offset, whence)

