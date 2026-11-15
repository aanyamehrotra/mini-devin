"""Bounded subprocess pipes without communicate() accumulating unlimited output."""
import os
import selectors
import subprocess
import time

MAX_OUTPUT_BYTES = 256 * 1024


def capture_output(command, *, timeout, stdin=None, capture_output=True, text=True):
    started = time.monotonic()
    buffers = [bytearray(), bytearray()]
    with subprocess.Popen(command, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        try:
            with selectors.DefaultSelector() as selector:
                for index, pipe in enumerate((process.stdout, process.stderr)):
                    os.set_blocking(pipe.fileno(), False)
                    selector.register(pipe, selectors.EVENT_READ, index)
                while selector.get_map():
                    remaining = timeout - (time.monotonic() - started)
                    if remaining <= 0:
                        raise subprocess.TimeoutExpired(command, timeout)
                    for key, _ in selector.select(min(remaining, .1)):
                        chunk = os.read(key.fileobj.fileno(), 65536)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        available = MAX_OUTPUT_BYTES - sum(map(len, buffers))
                        buffers[key.data].extend(chunk[:available])
                        if len(chunk) > available:
                            process.kill()
                            process.wait()
                            return subprocess.CompletedProcess(command, -2,
                                buffers[0].decode('utf-8', errors='replace'),
                                'OutputLimitExceeded: combined stdout/stderr exceeded 256 KiB.')
                process.wait(timeout=max(.001, timeout - (time.monotonic() - started)))
                return subprocess.CompletedProcess(command, process.returncode,
                    buffers[0].decode('utf-8', errors='replace'),
                    buffers[1].decode('utf-8', errors='replace'))
        except BaseException:
            process.kill()
            process.wait()
            raise
