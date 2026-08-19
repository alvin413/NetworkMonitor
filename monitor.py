#!/usr/bin/env python3

import json
import os
import re
import subprocess
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DEVICES_FILE = os.path.join(BASE_DIR, "devices.json")


def load_json(filename, default):
    """Carga un archivo JSON o devuelve un valor por defecto."""
    try:
        with open(filename, "r") as file_handle:
            return json.load(file_handle)
    except IOError:
        return default
    except ValueError:
        print("ERROR: JSON invalido: {}".format(filename))
        return default


def save_json(filename, data):
    """Guarda datos en formato JSON."""
    with open(filename, "w") as file_handle:
        json.dump(data, file_handle, indent=4, sort_keys=True)
        file_handle.write("\n")


def scan_network(interface, network):
    """Ejecuta arp-scan y devuelve una lista de dispositivos."""
    command = [
        "sudo",
        "arp-scan",
        "--interface={}".format(interface),
        network
    ]

    try:
        result = subprocess.check_output(
            command,
            stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as error:
        print("ERROR ejecutando arp-scan:")
        print(error.output.decode("utf-8", "ignore"))
        return []

    output = result.decode("utf-8", "ignore")

    devices = []

    pattern = re.compile(
        r"^(\d+\.\d+\.\d+\.\d+)\s+"
        r"([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})"
    )

    for line in output.splitlines():
        match = pattern.match(line.strip())

        if match:
            ip = match.group(1)
            mac = match.group(2).lower()

            devices.append({
                "ip": ip,
                "mac": mac
            })

    return devices


def update_inventory(devices, inventory):
    """Actualiza el inventario conservando los nombres manuales."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for device in devices:
        mac = device["mac"]
        ip = device["ip"]

        if mac not in inventory:
            inventory[mac] = {
                "ip": ip,
                "name": "",
                "known": False,
                "first_seen": now,
                "last_seen": now
            }

            print("[NUEVO] {} - {}".format(ip, mac))

        else:
            inventory[mac]["ip"] = ip
            inventory[mac]["last_seen"] = now

            name = inventory[mac].get("name", "")

            if name:
                print("[VISTO] {} - {} ({})".format(
                    ip,
                    mac,
                    name
                ))
            else:
                print("[VISTO] {} - {}".format(ip, mac))

    return inventory


def main():
    print("========================================")
    print(" NetworkMonitor")
    print("========================================")

    config = load_json(CONFIG_FILE, {})

    network = config.get("network", "192.168.0.0/24")
    interface = config.get("interface", "enp3s0")

    print("Interfaz : {}".format(interface))
    print("Red      : {}".format(network))
    print("")

    inventory = load_json(DEVICES_FILE, {})

    devices = scan_network(interface, network)

    if not devices:
        print("No se encontraron dispositivos.")
        return

    print("{} dispositivos encontrados.".format(len(devices)))
    print("")

    inventory = update_inventory(devices, inventory)

    save_json(DEVICES_FILE, inventory)

    print("")
    print("Inventario actualizado.")
    print("Dispositivos registrados: {}".format(len(inventory)))


if __name__ == "__main__":
    main()
