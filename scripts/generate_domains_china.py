#!/usr/bin/env python3
"""Generate domains.china.json / domains.china.list.

Downloads the felixonmars dnsmasq-china-list domain conf files, extracts the
domains they cover as sing-box domain_suffix rules, merges in a fixed set of
local/private domain_suffix entries and the extra domain_regex entry, dedupes
and sorts, then writes:
  - domains.china.json  (sing-box rule-set source, compiled to .srs separately)
  - domains.china.list  (Shadowrocket-style list: DOMAIN-SUFFIX / DOMAIN-REGEX)

Usage:
    python3 generate_domains_china.py
"""

import json
import urllib.request

SOURCE_URLS = [
    "https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/accelerated-domains.china.conf",
    "https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/google.china.conf",
    "https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/apple.china.conf",
]

# Local / private domain_suffix entries to always include, merged with the
# domains pulled from SOURCE_URLS.
EXTRA_DOMAIN_SUFFIX = [
    "lan",
    "local",
    "internal",
    "home",
    "corp",
    "localdomain",
    "intranet",
    "private",
    "localhost",
    "home.arpa",
    "in-addr.arpa",
    "ip6.arpa",
    "router.asus.com",
    "asusrouter.com",
]

# https://github.com/v2fly/domain-list-community/pull/2436
# Must stay valid RE2 syntax (sing-box's regex engine) - no backreferences or
# lookaround.
EXTRA_DOMAIN_REGEX = [
    r"^r+[0-9]+(---|\.)sn-(2x3|ni5|j5o)\w{5}\.xn--ngstr-lra8j\.com$",
]

JSON_OUTPUT = "domains.china.json"
LIST_OUTPUT = "domains.china.list"


def fetch_lines(url):
    with urllib.request.urlopen(url) as resp:
        text = resp.read().decode("utf-8", errors="ignore")
    return text.splitlines()


def extract_domains(lines, domain_suffix_set):
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        start = line.find("/")
        if start == -1:
            continue
        start += 1
        end = line.find("/", start)
        if end == -1 or end <= start:
            continue

        domain = line[start:end]
        if domain:
            domain_suffix_set.add(domain)


def main():
    domain_suffix_set = set(EXTRA_DOMAIN_SUFFIX)
    for url in SOURCE_URLS:
        extract_domains(fetch_lines(url), domain_suffix_set)

    domain_suffix = sorted(domain_suffix_set)
    domain_regex = sorted(set(EXTRA_DOMAIN_REGEX))

    rule_set = {
        "version": 5,
        "rules": [
            {
                "domain_suffix": domain_suffix,
                "domain_regex": domain_regex,
            }
        ],
    }

    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(rule_set, f, indent=2)
        f.write("\n")

    with open(LIST_OUTPUT, "w", encoding="utf-8") as f:
        for domain in domain_suffix:
            f.write(f"DOMAIN-SUFFIX,{domain}\n")
        for pattern in domain_regex:
            f.write(f"DOMAIN-REGEX,{pattern}\n")

    print(
        f"domain_suffix: {len(domain_suffix)} (incl. {len(EXTRA_DOMAIN_SUFFIX)} local), "
        f"domain_regex: {len(domain_regex)}"
    )


if __name__ == "__main__":
    main()
