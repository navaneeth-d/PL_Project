// REMOVE unused imports

#[no_mangle]
pub extern "C" fn init() {}

#[no_mangle]
pub extern "C" fn cleanup() {}


// ---------- REQUIRED BY ABI ----------
#[no_mangle]
pub extern "C" fn malloc(size: usize) -> *mut u8 {
    let mut buf = Vec::with_capacity(size);
    let ptr = buf.as_mut_ptr();
    std::mem::forget(buf);
    ptr
}

#[no_mangle]
pub extern "C" fn free(_ptr: *mut u8) {
    // no-op (safe for now)
}


// ---------- helper ----------
fn make_response(json: &str) -> *mut u8 {
    let bytes = json.as_bytes();
    let len = bytes.len();

    let mut buf = Vec::with_capacity(len + 4);

    buf.extend_from_slice(&(len as u32).to_le_bytes());
    buf.extend_from_slice(bytes);

    let ptr = buf.as_mut_ptr();
    std::mem::forget(buf);

    ptr
}

#[no_mangle]
pub extern "C" fn get_functions() -> *mut u8 {
    make_response("{\"functions\": [\"mul\"]}")
}

fn extract_numbers_mul(input: &str) -> i32 {
    let mut result = 1;

    for token in input.split(|c: char| !c.is_numeric()) {
        if let Ok(num) = token.parse::<i32>() {
            result *= num;
        }
    }

    result
}

#[no_mangle]
pub extern "C" fn call_function(ptr: *mut u8, len: usize) -> *mut u8 {
    let data = unsafe { std::slice::from_raw_parts(ptr.add(4), len - 4) };

    let input = std::str::from_utf8(data).unwrap_or("");

    if input.contains("mul") {
        let result = extract_numbers_mul(input);
        return make_response(&format!("{{\"result\": {}}}", result));
    }

    make_response("{\"error\": \"unknown function\"}")
}