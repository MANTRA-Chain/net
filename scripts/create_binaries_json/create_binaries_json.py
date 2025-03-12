"""
# This script is modified and based on the script in https://github.com/osmosis-labs/osmosis/blob/main/scripts/release/create_binaries_json/create_binaries_json.py
Usage:
This script generates a JSON object containing binary download URLs and their corresponding checksums 
for a given release tag of MANTRA-Chain/mantrachain or from a provided checksum URL.
The binary JSON is compatible with cosmovisor and with the chain registry.

You can run this script with the following commands:

❯ python create_binaries_json.py --checksums_url https://github.com/MANTRA-Chain/mantrachain/releases/download/v3.0.0/sha256sum.txt

Output:
{
  "binaries": {
    "linux/amd64": "https://github.com/MANTRA-Chain/mantrachain/releases/download/v3.0.0/mantrachaind-3.0.0-linux-amd64.tar.gz?checksum=<checksum>",
    "linux/arm64": "https://github.com/MANTRA-Chain/mantrachain/releases/download/v3.0.0/mantrachaind-3.0.0-linux-arm64.tar.gz?checksum=<checksum>",
    "darwin/amd64": "https://github.com/MANTRA-Chain/mantrachain/releases/download/v3.0.0/mantrachaind-3.0.0-darwin-amd64.tar.gz?checksum=<checksum>",
    "darwin/arm64": "https://github.com/MANTRA-Chain/mantrachain/releases/download/v3.0.0/mantrachaind-3.0.0-darwin-arm64.tar.gz?checksum=<checksum>"
  }
}

Expects a checksum in the form:

<CHECKSUM>  mantrachaind-<VERSION>-<OS>-<ARCH>[.tar.gz]
<CHECKSUM>  mantrachaind-<VERSION>-<OS>-<ARCH>[.tar.gz]
...

Example:

18ffe1da8f05fe191a1f7c0d3ab64f5e1c67586967bbc236095b5a32c439d39e  mantrachaind-3.0.0-linux-amd64
50ae2f624c477bc86272d5c2eeb53e0fdbc636211dd2af799a2b6c475afd90af  mantrachaind-3.0.0-linux-amd64.tar.gz

(From: https://github.com/MANTRA-Chain/mantrachain/releases/download/v3.0.0/sha256sum.txt)

❯ python create_binaries_json.py --tag v3.0.0

Output:
{
  "binaries": {
    "linux/amd64": "https://github.com/MANTRA-Chain/mantrachain/releases/download/v3.0.0/mantrachaind-3.0.0-linux-amd64.tar.gz?checksum=sha256:50ae2f624c477bc86272d5c2eeb53e0fdbc636211dd2af799a2b6c475afd90af",
    "linux/arm64": "https://github.com/MANTRA-Chain/mantrachain/releases/download/v3.0.0/mantrachaind-3.0.0-linux-arm64.tar.gz?checksum=sha256:d03e6a1731d25521e5517a6145ed9bc59f5a1bd11377ab03fae24710914d9a34",
    "darwin/amd64": "https://github.com/MANTRA-Chain/mantrachain/releases/download/v3.0.0/mantrachaind-3.0.0-darwin-amd64.tar.gz?checksum=sha256:fc7318fd834fe5b2912f309aec08aadbad085e7f220390d922cf8177542a4db0",
    "darwin/arm64": "https://github.com/MANTRA-Chain/mantrachain/releases/download/v3.0.0/mantrachaind-3.0.0-darwin-arm64.tar.gz?checksum=sha256:607ed92b71d0db1b8abbf5282392e734c04de8ac3945d970bfbe83088766d0d3"
  }
}

Expect a checksum to be present at: 
https://github.com/MANTRA-Chain/mantrachain/releases/download/<TAG>/sha256sum.txt
"""

import requests
import json
import argparse
import re
import os
import sys

def validate_chain_id(chain_id):
    return chain_id in ['mantra-1', 'mantra-dukong-1']

def validate_tag(tag):
    pattern = '^v[0-9]+.[0-9]+.[0-9]+$'
    return bool(re.match(pattern, tag))

def major_tag(tag):
    return tag.split('.')[0]

def download_checksums(checksums_url):

    response = requests.get(checksums_url)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch sha256sum.txt. Status code: {response.status_code}")
    return response.text

def checksums_to_binaries_json(checksums):

    binaries = {}
    
    # Parse the content and create the binaries dictionary 
    for line in checksums.splitlines():
        checksum, filename = line.split('  ')

        # include only tar.gz files for mantrachaind
        if filename.endswith('.tar.gz') and filename.startswith('mantrachaind'):
            try:
                _, tag, platform, arch = filename.split('-')
            except ValueError:
                print(f"Error: Expected binary name in the form: mantrachaind-X.Y.Z-platform-architecture.tar.gz, but got {filename}")
                sys.exit(1)
            _, tag, platform, arch = filename.split('-')
            arch = arch.split('.')[0]
            # exclude universal binaries and windows binaries
            if arch == 'all' or platform == 'windows':
                continue
            binaries[f"{platform}/{arch}"] = f"https://github.com/MANTRA-Chain/mantrachain/releases/download/v{tag}/{filename}?checksum=sha256:{checksum}"

    if not binaries:
        print("Error: No binaries found in the checksum file")
        sys.exit(1)

    # sort the binaries with linux first
    binaries = dict(sorted(binaries.items(), key=lambda item: item[0].split('/')[0] != 'linux'))

    binaries_json = {
        "binaries": binaries
    }

    return json.dumps(binaries_json, indent=2)

def main():

    parser = argparse.ArgumentParser(description="Create binaries json")
    parser.add_argument('--chain_id', metavar='chain_id', type=str, required=True, help='The Chain ID for which the binaries JSON is being generated (e.g., mantra-1|mantra-dukong-1)')
    parser.add_argument('--tag', metavar='tag', type=str, help='the tag to use (e.g v3.0.0)')
    parser.add_argument('--checksums_url', metavar='checksums_url', type=str, help='URL to the checksum')

    args = parser.parse_args()
    
    # Validate the tag format
    if args.tag and not validate_tag(args.tag):
        print("Error: The provided tag does not follow the 'vX.Y.Z' format.")
        sys.exit(1)
        
    if not validate_chain_id(args.chain_id):
        print("Error: The provided chain_id is invalid.")
        sys.exit(1)

    # Ensure that only one of --tag or --checksums_url is specified
    if not bool(args.tag) ^ bool(args.checksums_url):
        parser.error("Only one of tag or --checksums_url must be specified")
        sys.exit(1)

    checksums_url = args.checksums_url if args.checksums_url else f"https://github.com/MANTRA-Chain/mantrachain/releases/download/{args.tag}/sha256sum.txt"
    checksums = download_checksums(checksums_url)
    binaries_json = checksums_to_binaries_json(checksums)
    print(binaries_json)
    
    
    # Write the filled template to a file
    output_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', args.chain_id, 'upgrades', major_tag(args.tag))

    os.makedirs(output_directory, exist_ok=True)

    output_file_path = os.path.join(output_directory, f'cosmovisor.json')

    with open(output_file_path, 'w') as output_file:
        output_file.write(binaries_json)
    
    print(f"Binaries JSON generated at: {output_file_path}")

if __name__ == "__main__":
    main()
