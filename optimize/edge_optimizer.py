import time

def optimize_first_load():
    start = time.time()
    # Simulate optimization
    time.sleep(0.1)
    return time.time() - start < 2

def offline_fallback():
    return "Offline content available."

def device_context(device: str) -> str:
    if device.lower() in ['pi', 'raspberry', 'esp32']:
        return "Optimized for edge device."
    elif device.lower() in ['mobile', 'android', 'ios']:
        return "Optimized for mobile."
    else:
        return "Optimized for desktop." 