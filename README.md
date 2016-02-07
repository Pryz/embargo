# Embargo

Get list of IPv4 CIDR from Maxmind GeoIP CSV files.

Usage :
```
$ ./bin/embargo -h
Usage: embargo [options]

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -d, --debug           Run in debug mode
  -u URL, --url=URL     Source file URL. Default: http://bit.ly/20wcmhv
  -x EXTRACT_DIR, --extract-dir=EXTRACT_DIR
                        Directory to extract Zip file. Default:
                        /tmp/embargo_cache
  -f BLOCKED_IP_FILE, --blocked-ip-file=BLOCKED_IP_FILE
                        Blocked IPv4 CIDR list file. Default: blocked_ipv4.txt
  -c COUNTRY_CODES, --country-codes=COUNTRY_CODES
                        Country Codes list. Default: "CU,IR,KP,SD,SY"
  -S, --cidr-sorting    Sort by largest to smallest CIDR block size
```
