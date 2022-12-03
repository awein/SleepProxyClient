#
# This file is part of SleepProxyClient.
#
# @license   http://www.gnu.org/licenses/gpl.html GPL Version 3
# @author    Andreas Weinlein <andreas.dev@weinlein.info>
# @copyright Copyright (c) 2012-2022 Andreas Weinlein
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

import argparse
import codecs
import logging
import netifaces  # network interface handling
import socket
import struct
import subprocess

import dns.update
import dns.query
import dns.rdtypes
import dns.rdata
import dns.edns
import dns.rrset
import dns.inet
import dns.reversename
from dns.exception import DNSException

#
#  A Python Wake On Demand client implementation (SleepProxyClient)
#


# TTL (lease time) for sleep client.
# A Wake-On-Lan-Packet will be sent after this period.
# can be overwritten by specifying the corresponding argument!
TTL = 7200  # 2 h

# TTL for ddns update request ressource records
# see http://tools.ietf.org/html/draft-cheshire-dnsext-multicastdns-08#section-11
# should NOT be changed
TTL_LONG = 4500  # 75 min
# TTL is used for some other records
# should NOT be changed
TTL_SHORT = 120  # 2 min

# debug flag
DEBUG = False


def main():

    args = readArgs()

    # check interfaces
    sys_ifaces = netifaces.interfaces()

    interfaces = args.interfaces
    if "all" in args.interfaces:
        interfaces = sys_ifaces

    logging.debug("Interfaces: %s", ", ".join(interfaces))

    for iface in interfaces:
        if iface not in sys_ifaces:
            logging.error("Invalid interface specified: %s", iface)
        elif "lo" not in iface:
            sendUpdateForInterface(iface)


def sendUpdateForInterface(interface):
    # send update request per interface
    logging.debug("sending update on '%s'", interface)

    # get IPs for given interface
    ifaddrs = netifaces.ifaddresses(interface)

    ip_addresses = []
    if netifaces.AF_INET in ifaddrs:
        for ip_entry in ifaddrs[netifaces.AF_INET]:
            ip_addresses.append(ip_entry["addr"])

    if netifaces.AF_INET6 in ifaddrs:
        for ip_entry in ifaddrs[netifaces.AF_INET6]:
            ip_addresses.append(ip_entry["addr"].split("%")[0])  # ignore trailing %<iface>

    if len(ip_addresses) == 0:
        logging.error("No IPv4 or IPv6 Addresses found for interface: %s", interface)
        # TODO: throw instead?
        return

    logging.debug("Using IP Adresses: %s", ip_addresses)

    # get HW Addr
    if ":" in interface:  # handle virtual interfaces
        hardware_address = netifaces.ifaddresses(interface.rsplit(":")[0])[netifaces.AF_LINK][0]["addr"]
    else:
        hardware_address = ifaddrs[netifaces.AF_LINK][0]["addr"]

    logging.debug("Using MAC Address: %s", hardware_address)

    # get all available sleep proxies
    proxy = discoverSleepProxyForInterface(interface)
    if proxy is None:
        logging.warning("No sleep proxy available for interface: %s", interface)
        return

    # get hostname
    host = socket.gethostname()
    host_local = host + ".local"

    logging.debug("Using local hostname: %s", host_local)

    # create update request
    update = dns.update.Update("")

    ## add some host stuff
    for ip_address in ip_addresses:

        ip_version = dns.inet.af_for_address(ip_address)

        if ip_version == dns.inet.AF_INET:
            dns_datatype = dns.rdatatype.A
        elif ip_version == dns.inet.AF_INET6:
            dns_datatype = dns.rdatatype.AAAA
        else:
            continue

        update.add(dns.reversename.from_address(ip_address), TTL_SHORT, dns.rdatatype.PTR, host_local)
        update.add(host_local, TTL_SHORT, dns_datatype, ip_address)

    ## add services
    for service in discoverServices(ip_addresses):

        service_type = f"{service[0]}.local"
        service_type_host = f"{host}.{service_type}"
        port = service[1]

        # add the service
        txtrecord = ""
        if len(service) == 2 or service[2] == "":
            txtrecord = chr(0)
        else:
            for i in range(2, len(service)):
                txtrecord += " " + service[i]

        if DEBUG:
            txtrecord += " SPC_STATE=sleeping"

        update.add(service_type_host, TTL_LONG, dns.rdatatype.TXT, txtrecord)

        # device-info service gets a txt record only
        if service_type != "device-info._tcp.local":
            update.add("_services._dns-sd._udp.local", TTL_LONG, dns.rdatatype.PTR, service_type)
            update.add(service_type, TTL_LONG, dns.rdatatype.PTR, service_type_host)
            update.add(service_type_host, TTL_SHORT, dns.rdatatype.SRV, f"0 0 {port} {host_local}")

    ## add edns options

    # http://files.dns-sd.org/draft-sekar-dns-ul.txt
    # 2: Lease Time in seconds
    lease_time_option = dns.edns.GenericOption(2, struct.pack("!L", TTL))

    # http://tools.ietf.org/id/draft-cheshire-edns0-owner-option-00.txt
    # 4: edns owner option (MAC addr for WOL Magic packet)
    clean_hardware_address = hardware_address.replace(":", "")
    owner_option = dns.edns.GenericOption(4, codecs.decode("0000" + clean_hardware_address, 'hex_codec'))

    update.use_edns(edns=True, ednsflags=TTL_LONG, options=[lease_time_option, owner_option])

    logging.debug("Request: %s", update)

    # send request to proxy
    try:
        logging.debug("Sending update to %s", proxy['ip'])
        response = dns.query.udp(update, proxy["ip"], timeout=10, port=int(proxy["port"]))
        logging.debug("Response: %s", response)

        rcode = response.rcode()
        if rcode != dns.rcode.NOERROR:
            logging.error(
              "Unable to register with SleepProxy %s (%s:%d). Errcode: %d. Response: %s",
              proxy['name'], proxy['ip'], proxy['port'], rcode, response
              )
    except DNSException as e:
        logging.error(
            "Unable to register with SleepProxy %s (%s:%d): %s",
            proxy['name'], proxy['ip'], proxy['port'], e
        )


def discoverServices(ip_addresses):
    # discover all currently announced services from given IPs
    logging.debug("IPs: %s", ", ".join(ip_addresses))

    services = []
    cmd = "avahi-browse --all --resolve --parsable --no-db-lookup --terminate 2>/dev/null | grep '^=;'"

    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    for line in p.stdout.readlines():
        line_array = line.decode('utf8').rsplit(";")

        # check length
        if len(line_array) < 10:
            p.terminate()
            logging.error("Discovering services failed for: %s", "', ".join(ip_addresses))
            break

        # extract service details
        if line_array[7] in ip_addresses:
            service = line_array[4]
            port = line_array[8]
            txt_records = (
                line_array[9]
                .replace('" "', ";")
                .replace("\n", "")
                .replace('"', "")
                .rsplit(";")
            )
            service_entry = [service, port] + txt_records

            # ignore duplicates (e.g. due to IPv4/IPv6 dual stack)
            if service_entry not in services:
                services.append(service_entry)

    # wait for cmd to terminate
    p.wait()

    logging.debug("Discovered Services: %s", services)
    return services


def discoverSleepProxyForInterface(interface):

    logging.debug("Interface: %s", interface)

    cmd = (
        "avahi-browse --resolve --parsable --no-db-lookup --terminate _sleep-proxy._udp 2>/dev/null | "
        + f"grep '^=;{interface.rsplit(':')[0]}'"
    )

    # the best proxy found
    best_sleep_proxy = None
    # the best proxy properties found
    min_properties = ""

    # get all sleep proxies for the given interface an check for duplicates (IPv4/IPv6)
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    for line in p.stdout.readlines():
        line_array = line.decode('utf8').rsplit(";")

        # check length
        if len(line_array) < 10:
            p.terminate()
            break

        sleep_proxy = {"name": line_array[6], "ip": line_array[7], "port": line_array[8]}
        properties = line_array[3].rsplit(" ")[0]

        logging.debug("Available proxy: %s with properties: %s", sleep_proxy, properties)

        # choose the server with lowest properties and prefer none 169.254.X.X addresses
        if (
            min_properties == ""
            or min_properties > properties
            or (best_sleep_proxy and best_sleep_proxy["ip"].startswith("169.254."))
        ):
            min_properties = properties
            best_sleep_proxy = sleep_proxy

    # wait for cmd to terminate
    p.wait()

    logging.debug("Selected proxy: %s with properties: %s", best_sleep_proxy, min_properties)
    return best_sleep_proxy


def readArgs():
    # parse arguments
    global TTL
    global DEBUG

    parser = argparse.ArgumentParser(description="SleepProxyClient")
    parser.add_argument(
        "--interfaces",
        nargs="+",
        metavar="iface",
        action="store",
        help="A list of network interfaces to use, separated by space.",
        default=["all"],
    )
    parser.add_argument(
        "--ttl",
        action="store",
        type=int,
        help="TTL for the update in seconds. Client will be woken up after this period.",
        default=TTL_LONG,
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug switch for verbose output.",
        default=False,
    )

    result = parser.parse_args()

    # update some global vars
    TTL = result.ttl
    DEBUG = result.debug

    return result


if __name__ == "__main__":
    # call main
    main()
