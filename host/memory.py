from wasmtime import Instance, Store


class MemoryManager:
    def get_memory(self, store: Store, instance: Instance):
        return instance.exports(store)["memory"]

    def get_malloc(self, store: Store, instance: Instance):
        return instance.exports(store)["malloc"]

    def get_free(self, store: Store, instance: Instance):
        return instance.exports(store)["free"]

    def alloc(self, store: Store, instance: Instance, size: int) -> int:
        return self.get_malloc(store, instance)(store, size)

    def write(self, store: Store, instance: Instance, ptr: int, data_bytes: bytes) -> None:
        memory = self.get_memory(store, instance)
        mem = memory.data_ptr(store)
        for i in range(len(data_bytes)):
            mem[ptr + i] = data_bytes[i]

    def read(self, store: Store, instance: Instance, ptr: int, size: int) -> bytes:
        memory = self.get_memory(store, instance)
        mem = memory.data_ptr(store)
        return bytes(mem[ptr:ptr+size])

    def free(self, store: Store, instance: Instance, ptr: int) -> None:
        self.get_free(store, instance)(store, ptr)

    def write_bytes(self, store: Store, instance: Instance, data_bytes: bytes) -> tuple[int, int]:
        ptr = self.alloc(store, instance, len(data_bytes))
        self.write(store, instance, ptr, data_bytes)
        return ptr, len(data_bytes)

    def read_bytes(self, store: Store, instance: Instance, ptr: int, size: int) -> bytes:
        return self.read(store, instance, ptr, size)

    def read_with_length_prefix(self, store: Store, instance: Instance, ptr: int) -> bytes:
        size = int.from_bytes(self.read(store, instance, ptr, 4), "little")
        if size == 0:
            return b""
        return self.read(store, instance, ptr + 4, size)