import json
from wasmtime import Instance, Store
from host.memory import MemoryManager


class TypeSystem:
    def serialize(self, data: dict):
        return json.dumps(data).encode('utf-8')
    
    def deserialize(self, data_bytes: bytes):
        return json.loads(data_bytes.decode('utf-8'))
    
    def to_wasm(self, mem_mgr: MemoryManager, store: Store, instance: Instance, data: dict):
        raw = self.serialize(data)
        ptr, size = mem_mgr.write_bytes(store, instance, raw)
        return ptr, size
    
    def from_wasm(self, mem_mgr: MemoryManager, store: Store, instance: Instance, ptr: int):
        raw = mem_mgr.read_with_length_prefix(store, instance, ptr)
        return self.deserialize(raw)
    
    def wrap_with_length(self, data_bytes: bytes):
        size = len(data_bytes).to_bytes(4, "little")
        return size + data_bytes
    
    def prepare_input(self, mem_mgr: MemoryManager, store: Store, instance: Instance, data: dict):
        raw = self.serialize(data)
        wrapped = self.wrap_with_length(raw)
        return mem_mgr.write_bytes(store, instance, wrapped)
    
    def parse_output(self, mem_mgr: MemoryManager, store: Store, instance: Instance, ptr: int):
        raw = mem_mgr.read_with_length_prefix(store, instance, ptr)
        return self.deserialize(raw)