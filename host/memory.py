from wasmtime import Instance, Store


class MemoryManager:
    def get_memory(self, store: Store, instance: Instance):
        return instance.exports(store)["memory"]

    
    def get_malloc(self, store: Store, instance: Instance):
        return instance.exports(store)["malloc"]

    
    def get_free(self, store: Store, instance: Instance):
        return instance.exports(store)["free"]

    
    def alloc(self, store: Store, instance: Instance, size: int):
        return self.get_malloc(store, instance)(store, size)

    
    def write(self, store: Store, instance: Instance, ptr: int, data_bytes: bytes):
        memory = self.get_memory(store, instance)
        mem = memory.data_ptr(store)
        mem_len = memory.data_len(store)
        end = ptr + len(data_bytes)
        if ptr < 0 or end > mem_len:
            raise ValueError("write out of bounds")
        for i, byte in enumerate(data_bytes):
            mem[ptr + i] = byte

    
    def read(self, store: Store, instance: Instance, ptr: int, size: int):
        memory = self.get_memory(store, instance)
        mem = memory.data_ptr(store)
        mem_len = memory.data_len(store)
        end = ptr + size
        if ptr < 0 or size < 0 or end > mem_len:
            raise ValueError("read out of bounds")
        return bytes(mem[ptr + i] for i in range(size))

    
    def free(self, store: Store, instance: Instance, ptr: int):
        self.get_free(store, instance)(store, ptr)

    
    def write_bytes(self, store: Store, instance: Instance, data_bytes: bytes):
        if not data_bytes:
            raise ValueError("cannot write empty payload")
        ptr = self.alloc(store, instance, len(data_bytes))
        self.write(store, instance, ptr, data_bytes)
        return ptr, len(data_bytes)

    
    def read_bytes(self, store: Store, instance: Instance, ptr: int, size: int):
        return self.read(store, instance, ptr, size)

    
    def read_with_length_prefix(self, store: Store, instance: Instance, ptr: int):
        total_size = int.from_bytes(self.read(store, instance, ptr, 4), "little")
        if total_size == 0:
            return None
        if total_size < 12:
            raise ValueError("invalid response payload size")

        # total_size includes the initial 4-byte length prefix itself.
        payload_size = total_size - 4
        return self.read(store, instance, ptr + 4, payload_size)