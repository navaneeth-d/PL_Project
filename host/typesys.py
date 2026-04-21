from wasmtime import Instance, Store
from host.error import WASMRuntimeError
from host.memory import MemoryManager


class TypeSystem:
    def __init__(self):
        self._SIZE_INT = 4
        self._SIZE_INT_ARRAY = 4
        self._SIZE_STRING = 1

    
    def encode(self, data: dict):
        if "function" not in data:
            raise WASMRuntimeError("Data must contain 'function' key")
        
        if "args" not in data:
            raise WASMRuntimeError("Data must contain 'args' key")
        
        if "argspec" not in data:
            raise WASMRuntimeError("Data must contain 'argspec' key")
        
        func_id = data["function"]
        args = data["args"]
        argspecs = data['argspec']

        buf = bytearray()

        # write function id
        buf += func_id.to_bytes(4, "little")
        
        # write number of args
        buf += len(args).to_bytes(4, "little")

        def _safe_int(x: int):
            if x < -(2**31) or x > (2**31 - 1):
                raise WASMRuntimeError("int argument out of 32-bit signed range")
            return x.to_bytes(4, "little", signed=True)

        for arg, argspec in zip(args, argspecs):
            if argspec == "int":
                # write size of the int
                buf += self._SIZE_INT.to_bytes(4, "little")

                # write count (1 for single int)
                buf += (1).to_bytes(4, "little")

                #write the int value
                buf += _safe_int(arg)

            elif argspec == "list[int]":
                if any(not isinstance(x, int) for x in arg):
                    raise WASMRuntimeError("list arguments must contain only integers")
            
                # write size of each int in the array
                buf += self._SIZE_INT_ARRAY.to_bytes(4, "little")
                
                # write count (number of ints in the array)
                buf += len(arg).to_bytes(4, "little")

                # write each int value
                for x in arg:
                    buf += _safe_int(x)
            
            elif argspec == "string":
                # write size of each byte in the string (1 for utf-8)
                encoded_str = arg.encode('utf-8')

                # write count (number of bytes in the encoded string + 1 for null terminator)
                buf += self._SIZE_STRING.to_bytes(4, "little")

                # write the string bytes followed by a null terminator
                buf += (len(encoded_str) + 1).to_bytes(4, "little")

                # write the string bytes followed by a null terminator
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