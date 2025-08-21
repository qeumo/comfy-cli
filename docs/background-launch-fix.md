# Background Launch Hanging Fix

## Problem Description

When running ComfyUI in background mode using `comfy launch --background`, the process would hang indefinitely during startup. The issue occurred in the `launch_and_monitor` function at `process.wait()` call.

## Root Cause Analysis

The hanging was caused by multiple issues in `comfy_cli/command/launch.py`:

1. **Blocking `process.wait()`**: The `launch_and_monitor` function used blocking `process.wait()` which would wait indefinitely for the child process to complete
2. **Rich markup parsing errors**: Output redirection threads used `print()` function which tried to parse Rich markup, causing exceptions when ComfyUI output contained markup-like characters (e.g., file paths with brackets)
3. **Success detection logic**: The function only detected success on "To see the GUI go to:" string, but this wasn't always output in background mode

## Solution Implementation

### 1. Replace Blocking Wait with Async Monitoring

**Before:**
```python
process.wait()  # Blocks indefinitely
```

**After:**
```python
# Wait for either success signal or process termination with timeout
timeout_seconds = 120  # 2 minutes timeout
elapsed = 0

while not success_event.is_set() and elapsed < timeout_seconds:
    if process.poll() is not None:  # Process has terminated
        break
    await asyncio.sleep(1.0)  # Non-blocking wait
    elapsed += 1.0
```

### 2. Fix Rich Markup Errors in Redirectors

**Before:**
```python
def redirector_stderr(proc):
    while True:
        line = proc.stderr.readline()
        if not line:
            break
        print(line, end="")  # Causes Rich markup parsing errors
```

**After:**
```python
def redirector_stderr(proc):
    while True:
        line = proc.stderr.readline()
        if not line:
            break
        # Use sys.stderr.write to avoid Rich markup parsing
        sys.stderr.write(line)
        sys.stderr.flush()
```

### 3. Expand Success Detection Logic

**Before:**
```python
elif "To see the GUI go to:" in line:
    # Success detection logic
```

**After:**
```python
elif "To see the GUI go to:" in line or "web root:" in line:
    # Success detection logic - also detect when web server starts
```

### 4. Add Threading Event for Coordination

Added `threading.Event()` to coordinate between monitoring threads and main async loop:

```python
success_event = threading.Event()

def msg_hook(stream):
    # ... parsing logic ...
    if success_condition:
        success_event.set()  # Signal success
        os._exit(0)

# Main loop waits for event
while not success_event.is_set() and elapsed < timeout_seconds:
    # ... monitoring logic ...
```

## Files Modified

- `comfy_cli/command/launch.py`: Main fix in `launch_and_monitor` function and redirector functions

## Testing

Test the fix by running:
```bash
comfy launch --background
```

Expected output:
```
Launching ComfyUI from: /path/to/comfyui
DEBUG: Starting monitoring loop, PID: XXXXX
DEBUG: Started monitoring threads - stdout: True, stderr: True
ComfyUI is successfully launched in the background.
To see the GUI go to: http://127.0.0.1:8188
```

## Debugging

If issues persist, temporary debug output can be enabled by uncommenting:
```python
# Debug: print all lines to see what's happening
sys.stderr.write(f"DEBUG: {line.strip()}\n")
sys.stderr.flush()
```

This will show all ComfyUI output lines to identify where the process stops or what error occurs.

## Prevention

To prevent similar issues:
1. Always use non-blocking process monitoring in background operations
2. Avoid `print()` function for raw output redirection - use `sys.stdout.write()`/`sys.stderr.write()`
3. Add timeout mechanisms for long-running operations
4. Use multiple success indicators rather than relying on single string match
5. Add comprehensive debugging output during development