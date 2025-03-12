import argparse
from string import Template
import argparse
import re
import os
import sys

# This script is modified and based on the script in https://github.com/osmosis-labs/osmosis/blob/main/scripts/release/create_upgrade_guide/create_upgrade_guide.py
# USAGE:
#
# This script generates a Mainnet Upgrade Guide using a template. It replaces variables like current_version, upgrade_version,
# proposal_id, and upgrade_block based on the arguments provided.
# 
# Example:
# Run the script using the following command:
# python create_upgrade_guide.py --current_version=v2 --upgrade_version=v3 --proposal_id=10 --upgrade_block=3830000 --upgrade_tag=v3.0.0 --chain_id=mantra-1
#
# Arguments:
# --current_version    : The current version before upgrade (e.g., v2)
# --upgrade_version    : The version to upgrade to (e.g., v3)
# --proposal_id        : The proposal ID related to the upgrade
# --upgrade_block      : The block height at which the upgrade will occur
# --upgrade_tag        : The specific version tag for the upgrade (e.g., v3.0.0)
# --chain_id           : The Chain ID for which the upgrade guide is being generated (e.g., mantra-1)
#
# This will read a template file and replace the variables in it to generate a complete Mainnet Upgrade Guide.


def validate_tag(tag):
    pattern = '^v[0-9]+.[0-9]+.[0-9]+$'
    return bool(re.match(pattern, tag))

def validate_version(version):
    # Regex to match 'v' followed by a number
    pattern = '^v\d+$'
    return bool(re.match(pattern, version))

def validate_chain_id(chain_id):
    return chain_id in ['mantra-1', 'mantra-dukong-1']

def validate_block(block):
    pattern = '^\d+$'
    return bool(re.match(pattern, block))

def network(chain_id):
    return 'Mainnet' if chain_id == 'mantra-1' else 'Testnet'

def mintscan_network(chain_id):
    return 'mantra' if chain_id == 'mantra-1' else 'mantra-testnet'


def main():

    parser = argparse.ArgumentParser(description="Create upgrade guide from template")
    parser.add_argument('--current_version', '-c', metavar='current_version', type=str, required=True, help='Current version (e.g v1)')
    parser.add_argument('--upgrade_version', '-u', metavar='upgrade_version', type=str, required=True, help='Upgrade version (e.g v2)')
    parser.add_argument('--upgrade_tag', '-t', metavar='upgrade_tag', type=str, required=True, help='Upgrade tag (e.g v2.0.0)')
    parser.add_argument('--proposal_id', '-p', metavar='proposal_id', type=str, required=True, help='Proposal ID')
    parser.add_argument('--upgrade_block', '-b', metavar='upgrade_block', type=str, required=True, help='Upgrade block height')
    parser.add_argument('--chain_id', '-i', metavar='chain_id', type=str, required=True, help='The Chain ID for which the upgrade guide is being generated (e.g., mantra-1|mantra-dukong-1)')
    

    args = parser.parse_args()

    if not validate_version(args.current_version):
        print("Error: The provided current_version does not follow the 'vX' format.")
        sys.exit(1)
    
    if not validate_version(args.upgrade_version):
        print("Error: The provided upgrade_version does not follow the 'vX' format.")
        sys.exit(1)

    if not validate_tag(args.upgrade_tag):
        print("Error: The provided tag does not follow the 'vX.Y.Z' format.")
        sys.exit(1)

    if not validate_block(args.upgrade_block):
        print("Error: The provided block height is invalid.")
        sys.exit(1)

    if not validate_chain_id(args.chain_id):
        print("Error: The provided chain ID is invalid. It should be either 'mantra-1' or 'mantra-dukong-1'.")
        sys.exit(1)

    # Read the template from an external file
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'guide_template.md')
    with open(template_path, 'r') as f:
        markdown_template = f.read()

    # Initialize the template
    t = Template(markdown_template)

    # Substitute the variables
    # Use Template.safe_substitute() over Template.substitute()
    # This method won't throw an error for missing placeholders, making it suitable for partial replacements.
    filled_markdown = t.safe_substitute(
        CURRENT_VERSION=args.current_version,
        UPGRADE_VERSION=args.upgrade_version,
        UPGRADE_TAG_NUM=args.upgrade_tag.split('v')[1],
        PROPOSAL_ID=args.proposal_id,
        UPGRADE_BLOCK=args.upgrade_block,
        NETWORK=network(args.chain_id),
        MINTSCAN_NETWORK=mintscan_network(args.chain_id)
    )

    print(filled_markdown)
    
    # Write the filled template to a file
    output_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', args.chain_id, 'upgrades', args.upgrade_version)

    os.makedirs(output_directory, exist_ok=True)

    output_file_path = os.path.join(output_directory, f'guide.md')

    with open(output_file_path, 'w') as output_file:
        output_file.write(filled_markdown)
    
    print(f"Upgrade guide generated at: {output_file_path}")

if __name__ == "__main__":
    main()
