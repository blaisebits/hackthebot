from os import getenv
from libnmap.process import NmapProcess
from libnmap.parser import NmapParser

DEBUG = bool(getenv("DEBUG"))

def debug_output(stdout: str, stderr: str):
    print(f"""
[*] NMAP SCAN SMALL:
[-] Stderr: {stdout}
[-] Stdout: {stderr}
""")
def nmap_port_scan_small(targets: str) -> str:
    """Uses nmap to find high-probability open ports for a list of IP addresses"""
    nm = NmapProcess(
        targets=targets,
        options="-Pn --top-ports 100"
    )
    nm.run()
    if DEBUG:
        debug_output(nm.stdout, nm.stderr)

    nr = NmapParser.parse(nm.stdout)
    output = ""
    for host in nr.hosts:
        ip = host.ipv4
        hostname = host.hostnames[0]
        ports = []
        for service in host.services:
            ports.append(service.port)
        output += f"{ip} ({hostname}): {", ".join(str(x) for x in ports)}\n"

    return output

def nmap_port_scan_medium(targets: str) -> str:
    """Uses nmap to find common open ports for a list of IP addresses"""
    nm = NmapProcess(
        targets=targets,
        options="-Pn"
    )
    nm.run()
    if DEBUG:
        debug_output(nm.stdout, nm.stderr)

    nr = NmapParser.parse(nm.stdout)
    output = ""
    for host in nr.hosts:
        ip = host.ipv4
        hostname = host.hostnames[0]
        ports = []
        for service in host.services:
            ports.append(service.port)
        output += f"{ip} ({hostname}): {", ".join(str(x) for x in ports)}\n"

    return nm.stdout

def nmap_port_scan_large(targets: str) -> str:
    """Uses nmap to find most open ports for a list of IP addresses"""
    nm = NmapProcess(
        targets=targets,
        options="-Pn --top-ports 4000"
    )
    nm.run()
    if DEBUG:
        debug_output(nm.stdout, nm.stderr)

    nr = NmapParser.parse(nm.stdout)
    output = ""
    for host in nr.hosts:
        ip = host.ipv4
        hostname = host.hostnames[0]
        ports = []
        for service in host.services:
            ports.append(service.port)
        output += f"{ip} ({hostname}): {", ".join(str(x) for x in ports)}\n"

    return nm.stdout

def nmap_port_scan_huge(targets: str) -> str:
    """Uses nmap to find all open ports for a list of IP addresses"""
    nm = NmapProcess(
        targets=targets,
        options="-Pn -p- -oA"
    )
    nm.run()
    if DEBUG:
        debug_output(nm.stdout, nm.stderr)

    nr = NmapParser.parse(nm.stdout)
    output = ""
    for host in nr.hosts:
        ip = host.ipv4
        hostname = host.hostnames[0]
        ports = []
        for service in host.services:
            ports.append(service.port)
        output += f"{ip} ({hostname}): {", ".join(str(x) for x in ports)}\n"

    return nm.stdout