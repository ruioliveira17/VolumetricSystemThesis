import json
import socket
import subprocess

PRODUCT_NAME = "QUBIC"

DISCOVERY_PORT = 5001
DISCOVERY_MESSAGE = "DISCOVER_QUBIC"

API_PORT = 8000

def get_interface_ips():
    ips = {
        "ethernet": None,
        "wifi": None,
    }

    try:
        result = subprocess.run(
            ["ip", "-j", "addr", "show"],
            capture_output=True,
            text=True,
            check=True,
        )

        interfaces = json.loads(result.stdout)

        for interface in interfaces:
            name = interface.get("ifname")

            if name not in ("eth0", "wlan0"):
                continue

            for address in interface.get("addr_info", []):
                if address.get("family") != "inet":
                    continue

                ip = address.get("local")

                if name == "eth0":
                    ips["ethernet"] = ip
                elif name == "wlan0":
                    ips["wifi"] = ip

                break

    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(f"Failed to get interface addresses: {exc}")

    return ips

def get_interface_mac(interface_name):
    try:
        with open(f"/sys/class/net/{interface_name}/address") as file:
            return file.read().strip().upper()
    except OSError:
        return None

def create_response():
    return {
        "product": PRODUCT_NAME,
        "ip": get_interface_ips(),
        "mac": {
            "ethernet": get_interface_mac("eth0"),
            "wifi": get_interface_mac("wlan0"),
        },
        "api_port": API_PORT,
    }

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1,
    )

    sock.bind(("0.0.0.0", DISCOVERY_PORT))

    print(f"Qubic discovery listening on UDP {DISCOVERY_PORT}")

    while True:
        data, address = sock.recvfrom(1024)

        message = data.decode("utf-8", errors="ignore").strip()

        print(f"Discovery request from {address}: {message}")

        if message != DISCOVERY_MESSAGE:
            continue

        response = create_response()
        response_data = json.dumps(response).encode("utf-8")

        sock.sendto(response_data, address)

        print(f"Discovery response sent to {address}:")
        print(json.dumps(response, indent=2))

if __name__ == "__main__":
    main()