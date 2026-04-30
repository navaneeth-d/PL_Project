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
        {"id": 1, "name": "sumarray", "args": ["list[int]"], "return": "int"},
        {"id": 2, "name": "mul", "args": ["list[int]"], "return": "int"},
        {"id": 3, "name": "sumab", "args": ["int", "int"], "return": "int"},
        {"id": 4, "name": "greet", "args": ["string"], "return": "string"},
        {"id": 5, "name": "noReturn", "args": [], "return": "null"},
        {"id": 6, "name": "doubleArray", "args": ["list[int]"], "return": "list[int]"},
        {"id": 7, "name": "greet", "args": ["string", "string"], "return": "string"}
    ]}"#;

    
    create_response(json.len() as i32, 1, json)
}


#[no_mangle]
pub extern "C" fn call_function(ptr: *mut u8, _len: i32) -> *mut u8 {
    if ptr.is_null() { return ptr; }

    unsafe {
        let header = slice::from_raw_parts(ptr, 8);
        let func_id = i32::from_le_bytes(header[0..4].try_into().unwrap_or([0; 4]));

        let args_ptr = ptr.add(8);

        match func_id {
            1 => { // sumarray
                let size = i32::from_le_bytes(slice::from_raw_parts(args_ptr, 4).try_into().unwrap_or([0; 4])) as usize;
                let num_elements = i32::from_le_bytes(slice::from_raw_parts(args_ptr.add(4), 4).try_into().unwrap_or([0; 4])) as usize;
                
                let mut sum: i32 = 0;
                let mut offset = 8;
                for _ in 0..num_elements {
                    let arg = i32::from_le_bytes(slice::from_raw_parts(args_ptr.add(offset), 4).try_into().unwrap_or([0; 4]));
                    sum = sum.wrapping_add(arg);
                    offset += size;
                }
                create_response(1, 4, &sum.to_le_bytes())
            }
            2 => { // mul
                let size = i32::from_le_bytes(slice::from_raw_parts(args_ptr, 4).try_into().unwrap_or([0; 4])) as usize;
                let num_elements = i32::from_le_bytes(slice::from_raw_parts(args_ptr.add(4), 4).try_into().unwrap_or([0; 4])) as usize;
                
                let mut product: i32 = 1;
                let mut offset = 8;
                for _ in 0..num_elements {
                    let arg = i32::from_le_bytes(slice::from_raw_parts(args_ptr.add(offset), 4).try_into().unwrap_or([0; 4]));
                    product = product.wrapping_mul(arg);
                    offset += size;
                }
                create_response(1, 4, &product.to_le_bytes())
            }
            3 => { // sumab
                let mut offset = 0;
                let size_a = i32::from_le_bytes(slice::from_raw_parts(args_ptr.add(offset), 4).try_into().unwrap_or([0; 4])) as usize;
                let num_a = i32::from_le_bytes(slice::from_raw_parts(args_ptr.add(offset + 4), 4).try_into().unwrap_or([0; 4])) as usize;
                offset += 8;
                let a = i32::from_le_bytes(slice::from_raw_parts(args_ptr.add(offset), 4).try_into().unwrap_or([0; 4]));
                offset += size_a * num_a;
                
                let _size_b = i32::from_le_bytes(slice::from_raw_parts(args_ptr.add(offset), 4).try_into().unwrap_or([0; 4])) as usize;
                let _num_b = i32::from_le_bytes(slice::from_raw_parts(args_ptr.add(offset + 4), 4).try_into().unwrap_or([0; 4])) as usize;
                offset += 8;
                let b = i32::from_le_bytes(slice::from_raw_parts(args_ptr.add(offset), 4).try_into().unwrap_or([0; 4]));
                
                let sum = a.wrapping_add(b);
                create_response(1, 4, &sum.to_le_bytes())
            }
            4 => { // greet
                let item_size = i32::from_le_bytes(slice::from_raw_parts(args_ptr, 4).try_into().unwrap_or([0; 4])) as usize;
                let item_count = i32::from_le_bytes(slice::from_raw_parts(args_ptr.add(4), 4).try_into().unwrap_or([0; 4])) as usize;
                
                let str_len = item_size * item_count;
                let str_bytes = slice::from_raw_parts(args_ptr.add(8), str_len);
                
                let buf_len = str_len + 8; // "Hello, " + name + "!"
                let buf_ptr = malloc(buf_len);
                if buf_ptr.is_null() { return ptr::null_mut(); }
                
                let mut greet_len = 0;
                let buf = slice::from_raw_parts_mut(buf_ptr, buf_len);
                for &b in b"Hello, " { buf[greet_len] = b; greet_len += 1; }
                for &b in str_bytes { 
                    if b != 0 { buf[greet_len] = b; greet_len += 1; } 
                }
                buf[greet_len] = b'!'; greet_len += 1;
                
                create_response(greet_len as i32, 1, &buf[0..greet_len])
            }
            5 => { // noReturn
                ptr::null_mut()
            }
            6 => { // doubleArray
                let size = i32::from_le_bytes(slice::from_raw_parts(args_ptr, 4).try_into().unwrap_or([0; 4])) as usize;
                let num_elements = i32::from_le_bytes(slice::from_raw_parts(args_ptr.add(4), 4).try_into().unwrap_or([0; 4])) as usize;
                
                let res_total_len = 12 + size * num_elements;
                let res_ptr = malloc(res_total_len);
                if !res_ptr.is_null() {
                    let out = slice::from_raw_parts_mut(res_ptr, res_total_len);
                    out[0..4].copy_from_slice(&(res_total_len as i32).to_le_bytes());
                    out[4..8].copy_from_slice(&(num_elements as i32).to_le_bytes());
                    out[8..12].copy_from_slice(&(size as i32).to_le_bytes());
                    
                    let mut offset = 8;
                    let mut out_offset = 12;
                    for _ in 0..num_elements {
                        let arg = i32::from_le_bytes(slice::from_raw_parts(args_ptr.add(offset), 4).try_into().unwrap_or([0; 4]));
                        let doubled = arg.wrapping_mul(2);
                        out[out_offset..out_offset+4].copy_from_slice(&doubled.to_le_bytes());
                        offset += size;
                        out_offset += 4;
                    }
                }
                res_ptr
            }
            7 => { // greet_full (overloaded)
                let mut offset = 0;
                
                // Read first string
                let item_size1 = i32::from_le_bytes(slice::from_raw_parts(args_ptr.add(offset), 4).try_into().unwrap_or([0; 4])) as usize;
                let item_count1 = i32::from_le_bytes(slice::from_raw_parts(args_ptr.add(offset + 4), 4).try_into().unwrap_or([0; 4])) as usize;
                let str_len1 = item_size1 * item_count1;
                let str_bytes1 = slice::from_raw_parts(args_ptr.add(offset + 8), str_len1);
                
                // Jump memory offset to the second argument
                offset += 8 + str_len1;
                
                // Read second string
                let item_size2 = i32::from_le_bytes(slice::from_raw_parts(args_ptr.add(offset), 4).try_into().unwrap_or([0; 4])) as usize;
                let item_count2 = i32::from_le_bytes(slice::from_raw_parts(args_ptr.add(offset + 4), 4).try_into().unwrap_or([0; 4])) as usize;
                let str_len2 = item_size2 * item_count2;
                let str_bytes2 = slice::from_raw_parts(args_ptr.add(offset + 8), str_len2);
                
                // Allocate exact buffer size needed: "Hello, " + str1 + " " + str2 + "!"
                let buf_len = 7 + str_len1 + 1 + str_len2 + 1;
                let buf_ptr = malloc(buf_len);
                if buf_ptr.is_null() { return ptr::null_mut(); }
                
                let mut len = 0;
                let buf = slice::from_raw_parts_mut(buf_ptr, buf_len);
                
                for &b in b"Hello, " { buf[len] = b; len += 1; }
                for &b in str_bytes1 { if b != 0 { buf[len] = b; len += 1; } }
                buf[len] = b' '; len += 1;
                for &b in str_bytes2 { if b != 0 { buf[len] = b; len += 1; } }
                buf[len] = b'!'; len += 1;
                
                create_response(len as i32, 1, &buf[0..len])
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