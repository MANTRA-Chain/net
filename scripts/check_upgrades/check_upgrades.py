#!/usr/bin/env python3
import os
import re
import json
import requests
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from packaging.version import parse as parse_version

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REPO_ROOT = Path(os.path.abspath(__file__)).parents[2]

def parse_readme() -> List[str]:
    """Extract chain IDs from README.md"""
    readme_path = REPO_ROOT / "README.md"
    chain_ids = []
    
    with open(readme_path, 'r') as f:
        content = f.read()
    
    # Extract chain IDs using regex pattern matching for markdown links
    pattern = r'\[mainnet\]\(([^)]+)\)|\[testnet\]\(([^)]+)\)'
    matches = re.findall(pattern, content)
    
    for match in matches:
        # Each match is a tuple with groups from the regex
        chain_id = next((m for m in match if m), None)
        if chain_id:
            chain_ids.append(chain_id)
    
    logger.info(f"Found chain IDs in README: {chain_ids}")
    return chain_ids

def find_latest_upgrade(chain_id: str) -> Optional[Tuple[str, Path]]:
    """Select the upgrade directory whose guide.md declares the highest Upgrade Block Height.
    Falls back to None if no valid guide.md with a parsable height is found.
    """
    upgrades_path = REPO_ROOT / chain_id / "upgrades"
    if not upgrades_path.exists():
        logger.info(f"No upgrades directory found for {chain_id}")
        return None

    candidates = []  # (height, dir_path, guide_path)
    for d in upgrades_path.iterdir():
        if not d.is_dir():
            continue
        guide_path = d / "guide.md"
        if not guide_path.exists():
            continue
        try:
            with open(guide_path, 'r') as f:
                content = f.read()
            m = re.search(r'Upgrade Block Height\*\*:\s*(\d+)', content)
            if m:
                height = int(m.group(1))
                candidates.append((height, d, guide_path))
            else:
                logger.debug(f"No upgrade height found in {guide_path}")
        except Exception as e:
            logger.warning(f"Error reading {guide_path}: {e}")

    if not candidates:
        logger.info(f"No valid upgrade guides with heights found for {chain_id}")
        return None

    # Pick the directory with the maximum height
    candidates.sort(key=lambda x: x[0], reverse=True)
    height, directory, guide_path = candidates[0]
    logger.info(f"Selected upgrade {directory.name} (height {height}) for {chain_id}")
    return (directory.name, guide_path)

def extract_upgrade_info(guide_path: Path) -> Dict:
    """Extract upgrade block height and version from guide.md"""
    with open(guide_path, 'r') as f:
        content = f.read()
    
    # Extract upgrade block height
    height_pattern = r'Upgrade Block Height\*\*:\s*(\d+)'
    height_match = re.search(height_pattern, content)
    
    # Extract upgrade version
    version_pattern = r'upgrade_version="([^"]+)"'
    version_match = re.search(version_pattern, content)
    
    if not height_match or not version_match:
        logger.error(f"Could not extract upgrade info from {guide_path}")
        return {}
    
    return {
        'upgrade_height': int(height_match.group(1)),
        'upgrade_version': version_match.group(1)
    }

def get_rest_url(chain_id: str) -> Optional[str]:
    """Get REST API URL from meta.json"""
    meta_path = REPO_ROOT / chain_id / "meta.json"
    
    if not meta_path.exists():
        logger.error(f"meta.json not found for {chain_id}")
        return None
    
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    
    if 'apis' not in meta or 'rest' not in meta['apis'] or not meta['apis']['rest']:
        logger.error(f"REST API not found in meta.json for {chain_id}")
        return None
    
    # Get first REST URL
    return meta['apis']['rest'][0]['address']

def get_current_block_height(rest_url: str) -> Optional[int]:
    """Get current block height from REST API"""
    try:
        response = requests.get(f"{rest_url}/cosmos/base/tendermint/v1beta1/blocks/latest", timeout=10)
        response.raise_for_status()
        data = response.json()
        height = int(data['block']['header']['height'])
        logger.info(f"Current block height: {height}")
        return height
    except Exception as e:
        logger.error(f"Error getting block height: {e}")
        return None

def load_cosmovisor_json(upgrade_dir: Path) -> Dict:
    """Load cosmovisor.json file"""
    cosmovisor_path = upgrade_dir / "cosmovisor.json"
    
    if not cosmovisor_path.exists():
        logger.error(f"cosmovisor.json not found in {upgrade_dir}")
        return {}
    
    try:
        with open(cosmovisor_path, 'r') as f:
            data = json.load(f)
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing cosmovisor.json: {e}")
        return {}

def update_version_file(chain_id: str, version: str) -> bool:
    """Update version.txt file"""
    version_path = REPO_ROOT / chain_id / "version.txt"
    
    try:
        # Check current version
        with open(version_path, 'r') as f:
            current_version = f.read().strip()
        
        if current_version == version:
            logger.info(f"Version file already at {version}, no update needed")
            return False
        
        # Update version
        with open(version_path, 'w') as f:
            f.write(version)
        
        logger.info(f"Updated version.txt to {version}")
        return True
    except Exception as e:
        logger.error(f"Error updating version file: {e}")
        return False

def update_meta_json(chain_id: str, version: str, cosmovisor_data: Dict) -> bool:
    """Update meta.json with new version and binaries"""
    meta_path = REPO_ROOT / chain_id / "meta.json"
    
    if not meta_path.exists():
        logger.error(f"meta.json not found for {chain_id}")
        return False
    
    try:
        with open(meta_path, 'r') as f:
            meta = json.load(f)
        
        # Create a deep copy to properly detect changes
        orig_meta = json.loads(json.dumps(meta))
        
        # Update version information
        if 'codebase' in meta:
            # Update recommended version
            if 'recommended_version' in meta['codebase']:
                current_version = meta['codebase']['recommended_version']
                new_version = f"v{version}"
                logger.info(f"Updating recommended_version from {current_version} to {new_version}")
                meta['codebase']['recommended_version'] = new_version
            
            # Replace compatible versions instead of appending
            if 'compatible_versions' in meta['codebase']:
                new_version = f"v{version}"
                logger.info(f"Replacing compatible_versions with only {new_version}")
                meta['codebase']['compatible_versions'] = [new_version]
            
            # Update binaries if cosmovisor data is available
            if cosmovisor_data:                
                # First try to find binaries in the cosmovisor_data
                binaries_data = None
                if 'binaries' in cosmovisor_data:
                    binaries_data = cosmovisor_data['binaries']
                else:
                    # Look for platform keys directly (linux/amd64, etc.)
                    platform_keys = [k for k in cosmovisor_data.keys() if '/' in k]
                    if platform_keys:
                        logger.info(f"Found platform keys directly: {platform_keys}")
                        binaries_data = {k: cosmovisor_data[k] for k in platform_keys}
                
                if binaries_data and 'binaries' in meta['codebase']:
                    new_binaries = {}
                    
                    for platform, binary_info in binaries_data.items():
                        new_binaries[platform] = binary_info
                    
                    if new_binaries:
                        meta['codebase']['binaries'] = new_binaries
                    else:
                        logger.error("No binaries were extracted from cosmovisor_data")
                else:
                    logger.info("No binaries data found in cosmovisor.json or meta.json")
        
        # Check if there were any actual changes by comparing JSON strings
        if json.dumps(meta, sort_keys=True) == json.dumps(orig_meta, sort_keys=True):
            logger.info("No changes detected in meta.json after comparison")
            return False
        else:
            # Log what changed
            for key in meta.get('codebase', {}):
                if key in orig_meta.get('codebase', {}):
                    if meta['codebase'][key] != orig_meta['codebase'][key]:
                        logger.info(f"Change detected in {key}: {orig_meta['codebase'][key]} -> {meta['codebase'][key]}")
        
        # Write updated meta.json
        with open(meta_path, 'w') as f:
            json.dump(meta, f, indent=2)
        
        logger.info(f"Updated meta.json with new version information")
        return True
    except Exception as e:
        logger.error(f"Error updating meta.json: {e}")
        logger.error(f"Exception details: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def update_readme(version: str, chain_id: str) -> bool:
    """Update README.md with new version information"""
    readme_path = REPO_ROOT / "README.md"
    
    try:
        with open(readme_path, 'r') as f:
            content = f.read()
        
        # Determine network type based on chain_id
        network_type = "mainnet" if chain_id == "mantra-1" else "testnet"
        
        # Update version in the table
        pattern = rf'\[{network_type}\]\([^)]+\)\s*\|\s*:heavy_check_mark:\s*\|\s*v[0-9]+ \(([0-9.]+)\)'
        replacement = f"[{network_type}]({chain_id}) | :heavy_check_mark: | v{version.split('.')[0]} ({version})"
        
        new_content = re.sub(pattern, replacement, content)
        
        if new_content == content:
            logger.info(f"No changes needed for README.md")
            return False
        
        with open(readme_path, 'w') as f:
            f.write(new_content)
        
        logger.info(f"Updated README.md with new version information")
        return True
    except Exception as e:
        logger.error(f"Error updating README.md: {e}")
        return False

def process_chain(chain_id: str) -> Dict:
    """Process a single chain to check for and apply upgrades if needed"""
    result = {
        'chain_id': chain_id,
        'updated': False,
        'error': None,
        'changes': {}
    }
    
    try:
        # Find latest upgrade
        latest_upgrade = find_latest_upgrade(chain_id)
        if not latest_upgrade:
            # This is not a critical error, just log and return
            logger.info(f"No upgrade found for {chain_id}")
            return result
        
        upgrade_version, guide_path = latest_upgrade
        
        # Extract upgrade info
        upgrade_info = extract_upgrade_info(guide_path)
        if not upgrade_info:
            result['error'] = f"Could not extract upgrade info for {chain_id}"
            return result
        
        # Get REST URL
        rest_url = get_rest_url(chain_id)
        if not rest_url:
            result['error'] = f"Could not get REST URL for {chain_id}"
            return result
        
        # Get current height
        current_height = get_current_block_height(rest_url)
        if current_height is None:
            result['error'] = f"Could not get current block height for {chain_id}"
            return result
        
        # Check if upgrade height has passed
        if current_height <= upgrade_info['upgrade_height']:
            logger.info(f"Upgrade height {upgrade_info['upgrade_height']} not reached yet. Current height: {current_height}")
            return result
        
        logger.info(f"Upgrade height {upgrade_info['upgrade_height']} has passed! Current height: {current_height}")
        
        # Load cosmovisor.json
        upgrade_dir = REPO_ROOT / chain_id / "upgrades" / upgrade_version
        cosmovisor_data = load_cosmovisor_json(upgrade_dir)
        
        # Update files
        version_updated = update_version_file(chain_id, upgrade_info['upgrade_version'])
        meta_updated = update_meta_json(chain_id, upgrade_info['upgrade_version'], cosmovisor_data)
        readme_updated = update_readme(upgrade_info['upgrade_version'], chain_id)
        
        result['updated'] = any([version_updated, meta_updated, readme_updated])
        result['changes'] = {
            'version.txt': version_updated,
            'meta.json': meta_updated,
            'README.md': readme_updated
        }
        
        return result
    except Exception as e:
        logger.error(f"Error processing {chain_id}: {e}")
        result['error'] = str(e)
        return result

def main():
    """Main function to process all chains"""
    logger.info("Starting upgrade check process")
    
    # Get all chain IDs from README
    chain_ids = parse_readme()
    results = []
    errors = []
    
    for chain_id in chain_ids:
        logger.info(f"Processing chain: {chain_id}")
        result = process_chain(chain_id)
        results.append(result)
        
        # Collect actual errors, not just missing upgrades
        if result['error'] and not result['error'].startswith("No upgrade found"):
            errors.append(f"{chain_id}: {result['error']}")
    
    # Summarize results
    any_updated = any(r['updated'] for r in results)
    
    if any_updated:
        logger.info("Updates made to at least one network configuration")
    else:
        logger.info("No updates needed for any network")
    
    if errors:
        logger.error(f"Errors occurred: {', '.join(errors)}")
        exit(1)
    
    return 0

if __name__ == "__main__":
    exit(main())
