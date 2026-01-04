import json
import os
import socket
import sys
import time

SHELLY_IP = os.getenv("SHELLY_IP", "10.80.23.51")
SHELLY_PORT = int(os.getenv("SHELLY_PORT", "80"))
SHELLY_TIMEOUT = float(os.getenv("SHELLY_TIMEOUT", "5"))


def format_state(state):
    if state is None:
        return "UNKNOWN"
    return "ON" if state else "OFF"


def send_request(request):
    addr = socket.getaddrinfo(SHELLY_IP, SHELLY_PORT)[0][-1]
    s = socket.socket()
    s.settimeout(SHELLY_TIMEOUT)
    try:
        s.connect(addr)
        s.sendall(request.encode("utf-8"))
        data = b""
        max_size = 8192
        while len(data) < max_size:
            chunk = s.recv(min(2048, max_size - len(data)))
            if not chunk:
                break
            data += chunk
        return data
    finally:
        s.close()


def get_state():
    request = (
        "GET /rpc/Switch.GetStatus?id=0 HTTP/1.1\r\n"
        "Host: {}\r\n"
        "Connection: close\r\n\r\n"
    ).format(SHELLY_IP)
    response = send_request(request)
    start = response.find(b"{")
    if start == -1:
        return None
    try:
        payload = json.loads(response[start:].decode("utf-8"))
    except Exception:
        return None
    return bool(payload.get("output", False))


def set_state(on):
    body = '{"id":0,"on":' + ("true" if on else "false") + "}"
    request = (
        "POST /rpc/Switch.Set HTTP/1.1\r\n"
        "Host: {}\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: {}\r\n"
        "Connection: close\r\n\r\n{}"
    ).format(SHELLY_IP, len(body), body)
    send_request(request)


def main():
    try:
        initial = get_state()
    except Exception as exc:
        print("Shelly state: ERROR ({})".format(exc))
        return 1

    if initial is None:
        print("Shelly state: UNKNOWN")
        return 1

    print("Shelly state: {}".format(format_state(initial)))

    target = not initial
    print("Set Shelly {}".format(format_state(target)))
    set_state(target)

    time.sleep(5)
    mid_state = get_state()
    print("Shelly state after 5s: {}".format(format_state(mid_state)))

    set_state(initial)
    print("Restored Shelly {}".format(format_state(initial)))
    final_state = get_state()
    print("Shelly state final: {}".format(format_state(final_state)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
