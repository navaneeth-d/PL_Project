from wasmtime import Instance, Store
from host.error import WASMRuntimeError
from host.memory import MemoryManager


class TypeSystem:
    def __init__(self):
        self.TYPE_INT = 4
        self.TYPE_INT_ARRAY = 4
        self.TYPE_STRING = 1

    
    def encode(self, data: dict):
        func_id = data["function"]
        args = data["args"]

        buf = bytearray()

        # write function id
        buf += func_id.to_bytes(4, "little")
        
        # write number of args
        buf += len(args).to_bytes(4, "little")

        for arg in args:
            if isinstance(arg, int):
                if arg < -(2**31) or arg > (2**31 - 1):
                    raise WASMRuntimeError("int argument out of 32-bit signed range")

                buf += self.TYPE_INT.to_bytes(4, "little")
                buf += (1).to_bytes(4, "little")
                buf += arg.to_bytes(4, "little", signed=True)

            elif isinstance(arg, list):
                if any(not isinstance(x, int) for x in arg):
                    raise WASMRuntimeError("list arguments must contain only integers")
                buf += self.TYPE_INT_ARRAY.to_bytes(4, "little")
                buf += len(arg).to_bytes(4, "little")

                for x in arg:
                    if x < -(2**31) or x > (2**31 - 1):
                        raise WASMRuntimeError("list int argument out of 32-bit signed range")
                    buf += x.to_bytes(4, "little", signed=True)
            
            elif isinstance(arg, str):
                encoded_str = arg.encode('utf-8')
                buf += self.TYPE_STRING.to_bytes(4, "little")
                # Include the null terminator in item_count for C-string consumers.
                buf += (len(encoded_str) + 1).to_bytes(4, "little")
                buf += encoded_str + b'\x00'

            else:
                raise WASMRuntimeError(f"Unsupported type: {type(arg)}")
    
        return bytes(buf)

    
    def decode(self, data: bytes):
        if len(data) < 8:
            raise WASMRuntimeError("Invalid response payload")

        count = int.from_bytes(data[0:4], "little")
        item_size = int.from_bytes(data[4:8], "little")

        offset = 8

        if count == 0:
            return None

        # int
        if count == 1 and item_size == 4:
            return int.from_bytes(data[offset:offset+4], "little", signed=True)

        # string (bytes → utf-8)
        if item_size == 1:
            raw = data[offset:offset+count]
            answer = raw.rstrip(b"\x00").decode("utf-8")
            return answer

        # int array
        arr = []
        for _ in range(count):
            x = int.from_bytes(data[offset:offset+item_size], "little", signed=True)
            offset += item_size
            arr.append(x)

        return arr

    
    def to_wasm(self, mem_mgr: MemoryManager, store: Store, instance: Instance, data: dict):
        raw = self.encode(data)
        return mem_mgr.write_bytes(store, instance, raw)


    
    def from_wasm(self, mem_mgr: MemoryManager, store: Store, instance: Instance, ptr: int):
        raw = mem_mgr.read_with_length_prefix(store, instance, ptr)
        if raw is None:
            return None
        return self.decode(raw)

    
    def wrap_with_length(self, data_bytes: bytes) -> bytes:
        size = len(data_bytes).to_bytes(4, "little")
        return size + data_bytes