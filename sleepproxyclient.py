#
# This file is part of SleepProxyClient.
#
# @license   http://www.gnu.org/licenses/gpl.html GPL Version 3
# @author    Andreas Weinlein <andreas.dev@weinlein.info>
# @copyright Copyright (c) 2012-2023 Andreas Weinlein
#
# SleepProxyClient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# SleepProxyClient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SleepProxyClient. If not, see <http://www.gnu.org/licenses/>.

"""SleepProxyClient

A Python Wake On Demand client implementation (Sleep Proxy Client).
"""

from __future__ import annotations

import logging
import socket
import struct
import subprocess
from typing import Optional

import argparse
import codecs
from dataclasses import dataclass, field
import dns.update
import dns.query
import dns.rdtypes
import dns.rdata
import dns.edns
import dns.rrset
import dns.inet
import dns.reversename
from dns.exception import DNSException
import netifaces


DEFAULT_LEASE_TIME: int = 7200 # 2h
"""The default lease time (TTL) for sleep proxy client in minutes.

A Wake-On-LAN-Packet will be sent after this period. Defaults to 2 hours.
"""

TTL_LONG: int = 4500  # 75min
"""TTL for DDNS update request resource records.

see http://tools.ietf.org/html/draft-cheshire-dnsext-multicastdns-08#section-11
Should NOT be changed.
"""

TTL_SHORT: int = 120  # 2min
"""Shorter TTL for DDNS records.

Should NOT be changed.
"""

@dataclass
class InterfaceDetails:
    """Address details of a network interface."""
    ip_addresses: [str]
    hardware_address: str

    @staticmethod
    def for_interface(interface: str) -> InterfaceDetails:
        """Returns the address details for the given interface."""

        # get IPs for given interface
        ifaddrs = netifaces.ifaddresses(interface)

        ip_addresses: [str] = []
        if netifaces.AF_INET in ifaddrs:
            for ip_entry in ifaddrs[netifaces.AF_INET]:
                ip_addresses.append(ip_entry["addr"])

        if netifaces.AF_INET6 in ifaddrs:
            for ip_entry in ifaddrs[netifaces.AF_INET6]:
                ip_addresses.append(ip_entry["addr"].split("%")[0])  # ignore trailing %<iface>

        # get HW Address
        if ":" in interface:  # handle virtual interfaces
            hardware_address = netifaces.ifaddresses(interface.rsplit(":")[0])[netifaces.AF_LINK][0]["addr"]
        else:
            hardware_address = ifaddrs[netifaces.AF_LINK][0]["addr"]

        return InterfaceDetails(ip_addresses, hardware_address)

    def __str__(self):
        return f"InterfaceDetails(ip_addresses={self.ip_addresses}, hardware_address={self.hardware_address})"


@dataclass
class SleepProxyClient:
    """The Sleep Proxy Client."""

    lease_time: int
    preferred_proxies: list[str] = field(default_factory=list)

    def _create_update(self, interface_details: InterfaceDetails, hostname: str) -> dns.update.Update:
        """Creates and populates the DNS Update request."""
        # pylint:disable=too-many-locals

        update = dns.update.Update("")
        hostname_local = f"{hostname}.local"

        ## add some host stuff
        for ip_address in interface_details.ip_addresses:

            ip_version = dns.inet.af_for_address(ip_address)

            if ip_version == dns.inet.AF_INET:
                dns_datatype = dns.rdatatype.A
            elif ip_version == dns.inet.AF_INET6:
                dns_datatype = dns.rdatatype.AAAA
            else:
                continue

            update.add(dns.reversename.from_address(ip_address), TTL_SHORT, dns.rdatatype.PTR, hostname_local)
            update.add(hostname_local, TTL_SHORT, dns_datatype, ip_address)

        ## add services
        for service in MDNS.discover_services(interface_details.ip_addresses):

            service_type = f"{service.type}.local"
            service_type_host = f"{service.name}.{service_type}"
            service_txt_records = set(service.txt_records)
            service_txt_records.add("spc=1")
            txt_record = " ".join(service_txt_records)
            update.add(service_type_host, TTL_LONG, dns.rdatatype.TXT, txt_record)

            # device-info service gets a txt record only
            if service_type != "device-info._tcp.local":
                update.add("_services._dns-sd._udp.local", TTL_LONG, dns.rdatatype.PTR, service_type)
                update.add(service_type, TTL_LONG, dns.rdatatype.PTR, service_type_host)
                update.add(service_type_host, TTL_SHORT, dns.rdatatype.SRV, f"0 0 {service.port} {hostname_local}")

        ## add edns options

        # http://files.dns-sd.org/draft-sekar-dns-ul.txt
        # 2: Lease Time in seconds
        lease_time_option = dns.edns.GenericOption(2, struct.pack("!L", self.lease_time))

        # http://tools.ietf.org/id/draft-cheshire-edns0-owner-option-00.txt
        # 4: edns owner option (MAC addr for WOL Magic packet)
        clean_hardware_address = interface_details.hardware_address.replace(":", "")
        owner_option = dns.edns.GenericOption(4, codecs.decode("0000" + clean_hardware_address, 'hex_codec'))

        # The maximum size of UDP messages that can be sent and received. Messages with a size larger than
        # the interface MTU will be fragmented. This should not cause issues in most local networks.
        payload = 4096
        update.use_edns(edns=True, ednsflags=TTL_LONG, payload=payload, options=[lease_time_option, owner_option])
        return update


    def send_update(self, interface: str):
        """Sends a update request for the given interface."""
        logging.debug("Send update on '%s'", interface)

        interface_details: InterfaceDetails = InterfaceDetails.for_interface(interface)
        if len(interface_details.ip_addresses) == 0:
            logging.error("No IPv4 or IPv6 Addresses found for interface: %s", interface)
            return

        logging.debug("Using interface details: %s", interface_details)

        # get all available sleep proxies
        sleep_proxies = MDNS.discover_sleep_proxies(interface, preferred_proxies=self.preferred_proxies)
        if len(sleep_proxies) < 1:
            logging.warning("No sleep proxy available for interface: %s", interface)
            return

        # get hostname
        hostname = socket.gethostname()
        logging.debug("Using hostname: %s", hostname)

        update: dns.update.Update = self._create_update(interface_details, hostname)
        logging.debug("Request: %s", update)

        # send request to best proxy first and fall back on failure
        for proxy in sleep_proxies:
            try:
                logging.info("Sending update to %s", proxy)
                response = dns.query.udp(update, proxy.ip_address, timeout=10, port=proxy.port)

                logging.debug("Response: %s", response)
                rcode = response.rcode()
                if rcode != dns.rcode.NOERROR:
                    logging.error("Update failed for Sleep Proxy %s. Rcode: %d. Response: %s", proxy, rcode, response)
                else:
                    response_option = next((option for option in response.options if option.otype == 2), None)
                    if response_option is not None:
                        granted_lease_time = struct.unpack("!L", response_option.data)[0]
                        logging.info("Granted lease time is %s (Requested: %s)", granted_lease_time, self.lease_time)
                    break
            except DNSException as e:
                logging.error("Unable to register with Sleep Proxy %s: %s", proxy, e)


@dataclass(order=True)
class SleepProxyRecord:
    """A Sleep Proxy record."""
    sort_index: str = field(init=False, repr=False)
    name: str
    ip_address: str
    port: int
    properties: str # See [https://github.com/awein/SleepProxyClient/wiki/Sleep-Proxy-Property-Encoding]
    preferred: bool

    @staticmethod
    def from_avahi_browse(line: str, preferred_proxies: Optional[list[str]] = None) -> Optional[SleepProxyRecord]:
        """Creates a SleepProxyRecord from the output of avahi-browse"""

        if preferred_proxies is None:
            preferred_proxies = []

        # =;enp0s0;IPv4;70-35-60-63\.1\032Apple\032TV;_sleep-proxy._udp;local;Apple-TV.local;192.168.1.14;60540;
        line_array = line.rsplit(";")
        if len(line_array) < 10:
            logging.error("Failed to create Sleep Proxy Record from %s", line)
            return None

        name = line_array[6]
        ip_address = line_array[7]
        port = int(line_array[8])
        # avahi-browse output of "name" is encoded when the "--parsable" option is used
        properties = line_array[3].replace('\\032', ' ').split(" ", 1)[0].replace('\\', '')

        return SleepProxyRecord(name, ip_address, port, properties, name in preferred_proxies)

    def __post_init__(self):
        ip_rating = 10
        if self.ip_address.startswith("169.254."):
            ip_rating = 50
        self.sort_index = f"{'0' if self.preferred else '1' }_{self.properties}_{ip_rating}"

    def __str__(self):
        return (
            f'SleepProxyRecord({self.name}, {self.ip_address}:{self.port}, properties: {self.properties}'
            f'{", preferred" if self.preferred else ""})'
        )

class MDNS:
    """MDNS discovery related functions.
    Should be transformed to a module when split into multiple files
    """

    @dataclass(frozen=True, eq=True)
    class Service:
        """A MDNS service"""
        name: str
        type: str
        port: int
        txt_records: frozenset[str]

        def __str__(self):
            return f"MDNS.Service(name={self.name}, type={self.type}, port={self.port}, txt_records={self.txt_records})"

    avahi_browse_base_cmd = "avahi-browse --resolve --parsable --no-db-lookup --terminate"

    @staticmethod
    def discover_services(ip_addresses: [str]) -> set[Service]:
        """Discover all currently announced services for the given IPs."""

        logging.debug("IPs: %s", ", ".join(ip_addresses))

        # services are announced dual-stack and need to be de-duplicated
        services = set()

        cmd = f"{MDNS.avahi_browse_base_cmd} --all 2>/dev/null | grep '^=;'"
        with subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc:
            for line in proc.stdout.readlines():
                # =;enp0s1;IPv6;hostname;_ssh._tcp;local;hostname.local;fe80::1ce6:40ff:fec1:bca4;22;
                # =;enp0s1;IPv4;hostname;_ssh._tcp;local;hostname.local;192.168.1.12;22;
                # =;enp0s1;IPv4;hostname;_airplay._tcp;local;hostname.local;192.168.1.12;7000;"srcvers=670.6.2" "pk=..."
                line_array = line.decode('utf8').rsplit(";")

                if len(line_array) < 10:
                    proc.terminate()
                    logging.error("Discovering services failed for: %s", "', ".join(ip_addresses))
                    break

                # extract service details
                ip_address = line_array[7]
                if ip_address in ip_addresses:
                    service_name = line_array[3]
                    service_type = line_array[4]
                    port = int(line_array[8])
                    txt_records = frozenset(
                        line_array[9]
                        .replace('" "', ";")
                        .replace("\n", "")
                        .replace('"', "")
                        .rsplit(";")
                    )
                    services.add(MDNS.Service(service_name, service_type, port, txt_records))

            # wait for cmd to terminate
            proc.wait()

        logging.debug("Discovered Services: %s", services)
        return services

    @staticmethod
    def discover_sleep_proxies(interface: str, preferred_proxies: Optional[list[str]] = None) -> list[SleepProxyRecord]:
        """Discover all Sleep Proxy Servers available via the given interface.

        Returns a sorted list with the best Sleep Proxy in the front.
        """

        logging.debug("Interface: %s", interface)

        sleep_proxies: [SleepProxyRecord] = []

        cmd = f"{MDNS.avahi_browse_base_cmd} _sleep-proxy._udp 2>/dev/null | grep '^=;{interface.rsplit(':')[0]}'"
        # =;enp0s0;IPv4;70-35-60-63\.1\032Apple\032TV;_sleep-proxy._udp;local;Apple-TV.local;192.168.1.14;60540;
        with subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc:
            for line in proc.stdout.readlines():
                sleep_proxy = SleepProxyRecord.from_avahi_browse(
                    line.decode('utf8'),
                    preferred_proxies=preferred_proxies
                )
                if sleep_proxy is not None:
                    sleep_proxies.append(sleep_proxy)
            proc.wait()

        logging.debug("Discovered Sleep Proxies: %s", sleep_proxies)
        return sorted(sleep_proxies)


def parse_arguments() -> argparse.Namespace:
    """Parses the command line arguments and returns them."""
    parser = argparse.ArgumentParser(description="SleepProxyClient")
    parser.add_argument(
        "--interfaces",
        nargs="+",
        help="A list of network interfaces to use, separated by space.",
        default=["all"],
    )
    parser.add_argument(
        "--preferred-proxies",
        nargs="+",
        help="""
             A list of Sleep Proxy Servers to prefer.
             Sleep Proxy Servers with those host names will be preferred if discovered.
             """,
    )
    parser.add_argument(
        "--lease-time",
        type=int,
        help="Lease time for the update in seconds. Client will be woken up after this period.",
        default=DEFAULT_LEASE_TIME,
    )
    parser.add_argument(
        "--logfile",
        help="The file to log output to.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enables debug logging.",
        default=False,
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    logging_config = {
        "format": "%(asctime)s spc[%(process)d] %(levelname)s %(filename)s[%(funcName)s:%(lineno)d] %(message)s",
        "datefmt": "%b %d %Y %H:%M:%S"
    }
    if args.debug is not None:
        logging_config["level"] = logging.DEBUG
    if args.logfile is not None:
        logging_config["filename"] = args.logfile
    logging.basicConfig(**logging_config)

    logging.debug("Arguments: %s", args)

    client = SleepProxyClient(args.lease_time, preferred_proxies=args.preferred_proxies)

    # check interfaces
    system_interfaces = netifaces.interfaces()

    interfaces = args.interfaces
    if "all" in args.interfaces:
        interfaces = system_interfaces

    logging.debug("Interfaces: %s", ", ".join(interfaces))

    for iface in interfaces:
        if iface not in system_interfaces:
            logging.error("Invalid interface specified: %s", iface)
        elif iface.startswith("lo"):
            logging.debug("Skipping local interface: %s", iface)
        else:
            client.send_update(iface)
