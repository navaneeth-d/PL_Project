#![no_std]

use core::ptr;
use core::slice;

// --- Memory Management ---

const HEAP_SIZE: usize = 64 * 1024;

struct BumpAllocator {
    buffer: [u8; HEAP_SIZE],
    offset: usize,
}

static mut ALLOCATOR: BumpAllocator = BumpAllocator {
    buffer: [0u8; HEAP_SIZE],
    offset: 0,
};

impl BumpAllocator {
    fn alloc(&mut self, size: usize) -> *mut u8 {
        let aligned_size = (size + 7) & !7; // 8-byte alignment
        let start = self.offset;
        
        if start + aligned_size > HEAP_SIZE {
            return ptr::null_mut();
        }

        self.offset += aligned_size;
        unsafe { self.buffer.as_mut_ptr().add(start) }
    }
}

// --- FFI Exports for Memory ---

#[no_mangle]
pub extern "C" fn malloc(size: usize) -> *mut u8 {
    unsafe { ALLOCATOR.alloc(size) }
}

#[no_mangle]
pub extern "C" fn free(_ptr: *mut u8) {
    // Bump allocators are "allocate-only" by design
}

#[no_mangle]
pub extern "C" fn init() {}

#[no_mangle]
pub extern "C" fn cleanup() {}

// --- Helpers ---

/// Packs data into the [total_len][count][item_size][payload] format
fn create_response(count: i32, item_size: i32, payload: &[u8]) -> *mut u8 {
    let total_len = (12 + payload.len()) as i32;
    let ptr = malloc(total_len as usize);
    
    if ptr.is_null() { return ptr; }

    unsafe {
        // We treat the pointer as a slice to make writing data much cleaner
        let out = slice::from_raw_parts_mut(ptr, total_len as usize);
        
        out[0..4].copy_from_slice(&total_len.to_le_bytes());
        out[4..8].copy_from_slice(&count.to_le_bytes());
        out[8..12].copy_from_slice(&item_size.to_le_bytes());
        out[12..].copy_from_slice(payload);
    }

    ptr
}

// --- Plugin Logic ---

#[no_mangle]
pub extern "C" fn get_functions() -> *mut u8 {
    let json = br#"{"functions": [
        {"id": 1, "name": "factorial", "args": "[int]", "return": "int"},
        {"id": 2, "name": "fibonacci", "args": "[int]", "return": "int"},
        {"id": 3, "name": "is_prime",  "args": "[int]", "return": "int"}
    ]}"#;
    
    create_response(json.len() as i32, 1, json)
}

#[no_mangle]
pub extern "C" fn call_function(ptr: *mut u8, _len: i32) -> *mut u8 {
    if ptr.is_null() { return ptr; }

    unsafe {
        // Read the header values using native Rust byte conversion
        let header = slice::from_raw_parts(ptr, 8);
        let func_id = i32::from_le_bytes(header[0..4].try_into().unwrap_or([0; 4]));
        
        // Extract the first argument (at offset 16 to skip item_size and item_count)
        let arg_bytes = slice::from_raw_parts(ptr.add(16), 4);
        let n = i32::from_le_bytes(arg_bytes.try_into().unwrap_or([0; 4]));

        match func_id {
            1 => {
                let res = (1..=n).fold(1i32, |acc, i| acc.saturating_mul(i));
                create_response(1, 4, &res.to_le_bytes())
            }
            2 => {
                let mut a: (i32, i32) = (0, 1);

                for _ in 0..n { a = (a.1, a.0.saturating_add(a.1)); }
                create_response(1, 4, &a.0.to_le_bytes())
            }
            3 => {
                let is_p = if n < 2 { 0 } else { 
                    (2..n).take_while(|i| i * i <= n).all(|i| n % i != 0) as i32 
                };
                create_response(1, 4, &is_p.to_le_bytes())
            }
            _ => {
                let msg = b"Function not found";
                create_response(msg.len() as i32, 1, msg)
            }
        }
    }
}

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! { loop {} }