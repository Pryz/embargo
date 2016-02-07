#!/usr/bin/env python
# encoding: utf-8
"""
embargo.py

Author: Julien Fabre
Email: ju.pryz@gmail.com
"""

import requests
import zipfile
import os
import sys
import csv
import logging
from optparse import OptionParser
from netaddr import IPNetwork

__VERSION__ = "0.1.0"

# Default list of country codes
COUNTRY_CODES = ['CU', 'IR', 'KP', 'SD', 'SY']

# Target location to download the zipfile
TMP_ZIP = '/tmp/maxmind.zip'


def get_list_from_csv(csv_file, search_key, for_values, get_key):
    """
    Retrieve list of `get_key` values in CSV for `search_key` in `for_values`
    """
    result = []
    with open(csv_file) as c_fh:
        reader = csv.DictReader(c_fh)
        for row in reader:
            if row[search_key] in for_values:
                result.append(row[get_key])
    return result


def sort_ip(cidr_blocks):
    """
    Easy IP sorting using netaddr library
    """
    l = [IPNetwork(ip) for ip in cidr_blocks]
    l.sort()
    return l


def sort_by_cidr(cidr_blocks):
    """
    Contruct a sorted CIDR blocks list
    """
    c_dict = {}
    for c_block in cidr_blocks:
        c = str(c_block).split('/')
        if len(c) == 2:
            if c[1] in c_dict:
                c_dict[c[1]].append(c[0])
            else:
                c_dict[c[1]] = [c[0]]

    sorted_cidr_blocks = []
    for k in sorted(c_dict.iterkeys()):
        for subnet in c_dict[k]:
            sorted_cidr_blocks.append("{}/{}".format(subnet, k))
    return sorted_cidr_blocks

def list_callback(option, opt, value, parser):
    setattr(parser.values, option.dest, value.split(','))


def main(**kwargs):
    """
    Main function
    """
    log = logging.getLogger("embargo")

    getopt = OptionParser(
        version=__VERSION__,
        usage="Usage: %prog [options]")
    getopt.add_option(
        "-d", "--debug", dest="debug", action="store_true",
        help="Run in debug mode")
    getopt.add_option(
        "-u", "--url", dest="url", type="string", metavar="URL",
        help="Source file URL. Default: http://bit.ly/20wcmhv", default="http://bit.ly/20wcmhv")
    getopt.add_option(
        "-x", "--extract-dir", dest="extract_dir", type="string",
        help="Directory to extract Zip file. Default: /tmp/embargo_cache",
        default="/tmp/embargo_cache")
    getopt.add_option(
        "-f", "--blocked-ip-file", dest="blocked_ip_file", type="string",
        help="Blocked IPv4 CIDR list file. Default: blocked_ipv4.txt",
        default="blocked_ipv4.txt")
    getopt.add_option(
        "-c", "--country-codes", dest="country_codes", type="string",
        help='Country Codes list. Default: "CU,IR,KP,SD,SY"',
        action="callback", callback=list_callback)
    getopt.add_option(
        "-S", "--cidr-sorting", dest="cidr_sorting", action="store_true",
        help="Sort by largest to smallest CIDR block size")

    (opts, args) = getopt.parse_args(**kwargs)

    if opts.debug is True:
        logLevel = logging.DEBUG
    else:
        logLevel = logging.INFO

    log.setLevel(logLevel)
    ch = logging.StreamHandler()
    ch.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    log.addHandler(ch)

    if opts.country_codes is None:
        opts.country_codes = COUNTRY_CODES

    # Create extract location is not present
    if not os.path.exists(opts.extract_dir):
        try:
            os.makedirs(opts.extract_dir)
        except OSError as e:
            log.error(e)
            sys.exit(1)

    # Perform some clean up
    log.info("Cleaning up previous run...")
    if os.path.exists(TMP_ZIP):
        os.remove(TMP_ZIP)
    if os.path.exists(opts.blocked_ip_file):
        os.remove(opts.blocked_ip_file)

    # Get the zip file and extract
    log.info("Downloading Maxmind GeoIP zip from %s", opts.url)
    try:
        r = requests.get(opts.url)
    except requests.exceptions.ConnectionError as e:
        log.error(e.message)
        sys.exit(1)
    with open(TMP_ZIP, "wb") as code:
        code.write(r.content)

    log.info("Extracting files from Zip archive")
    zf = zipfile.ZipFile(TMP_ZIP, 'r')
    try:
        zf.extractall(opts.extract_dir)
    except Exception as e:
        log.error(e)
        sys.exit(1)

    # Get name of the main source dir
    ldir = os.listdir(opts.extract_dir)[-1]

    location_file = "{}/{}/GeoLite2-Country-Locations-en.csv".format(opts.extract_dir, ldir)
    if os.path.exists(location_file):
        geoname_ids = get_list_from_csv(
            location_file, "country_iso_code", opts.country_codes, "geoname_id"
        )
    else:
        log.error(
            "%s does not exist. Please verify Maxmind GeoIP zip file source", location_file
        )

    if len(geoname_ids) > 0:
        ipv4_file = "{}/{}/GeoLite2-Country-Blocks-IPv4.csv".format(opts.extract_dir, ldir)
        if os.path.exists(ipv4_file):
            cidr_blocks = get_list_from_csv(
                ipv4_file, "geoname_id", geoname_ids, "network"
            )
            cidr_blocks = sort_ip(cidr_blocks)
            if opts.cidr_sorting:
                cidr_blocks = sort_by_cidr(cidr_blocks)

            if len(cidr_blocks) > 0:
                log.info("%s IPv4 subnet(s) will be blocked.", len(cidr_blocks))
                with open("{}".format(opts.blocked_ip_file), 'w') as f:
                    for cb in cidr_blocks:
                        f.write("{}\n".format(cb))
            else:
                log.info("No IPv4 subnet block found.")
        else:
            log.error(
                "%s does not exist. Please verify Maxmind GeoIP zip file source", ipv4_file
            )
    else:
        log.info("No Geoname ID found for Country Codes : %s", COUNTRY_CODES)

    sys.exit(0)


if __name__ == '__main__':
    main()
