# Mainnet Upgrade Guide: From Version v6.1.0 to v7.0.0

## Overview

- **v7.0.0 Proposal**: [Proposal Page](https://www.mintscan.io/mantra/proposals/29)
- **v7.0.0 Upgrade Block Height**: 13000000
- **v7.0.0 Upgrade Countdown**: [Block Countdown](https://www.mintscan.io/mantra/block/13000000)
- **v7.0.0 Release**: [Release Page](https://github.com/MANTRA-Chain/mantrachain/releases/tag/v7.0.0)
- **v7.0.0 Docker Image**: [ghcr.io/mantra-chain/mantrachain:v7.0.0](https://github.com/mantra-chain/mantrachain/pkgs/container/mantrachain)

## Token Redenomination

The v7.0.0 upgrade performs a one-time, on-chain token redenomination from the legacy `uom` denomination to the new `amantra` denomination. All token balances are scaled by a factor of **4,000,000,000,000 (4 x 10^12)** to align with the new 18-decimal `amantra` base unit. The display denomination becomes `mantra`.

This is a **state-migration-only upgrade** -- no new modules are added, no modules are removed, and no store keys change. The upgrade handler migrates existing state in-place across all affected modules.

Below are a few notable fee-related parameter changes. Note that 1 MANTRA = 10^18 amantra.

| Item | Old Value | New Value | New Value (MANTRA) |
|------|-----------|-----------|-------------------|
| Gas Price `base_fee` | 0.01uom | 40000000000amantra | 0.00000004 MANTRA |
| TokenFactory `denom_creation_fee` | 88000000uom | 352000000000000000000amantra | 352 MANTRA |
| Governance `min_deposit` | 88888000000uom | 355552000000000000000000amantra | 355,552 MANTRA |
| Min staking amount | 1uom | 1amantra | 10^-18 MANTRA |

---

## Hardware Requirements

### Memory Specifications

This upgrade includes state changes and may take longer than previous upgrades. During migration, it may take around 10-20 minutes depending on your node's data size.

To avoid OOM during the upgrade process (which can lead to data corruption), increase node resources before the upgrade height.

Recommended VM resource limits:

```yaml
archive node:
    cpu: "4"
    memory: "64Gi"

full node:
    cpu: "4"
    memory: "50Gi"

sentry and validator:
    cpu: "2"
    memory: "32Gi"
```

If you run on Kubernetes, treat the above values as pod resource limits.

If your environment cannot meet these memory targets, setting up swap space is recommended as a fallback.

#### Configuring Swap Space

_Execute these commands to set up a 32GB swap space_:

```sh
sudo swapoff -a
sudo fallocate -l 32G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

_To ensure the swap space persists after reboot_:

```sh
sudo cp /etc/fstab /etc/fstab.bak
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

For an in-depth guide on swap configuration, please refer to [this tutorial](https://www.digitalocean.com/community/tutorials/how-to-add-swap-space-on-ubuntu-20-04).

---

## Cosmovisor Configuration

### Initial Setup (For First-Time Users)

If you have not previously configured Cosmovisor, follow this section; otherwise, proceed to the next section.

Cosmovisor is strongly recommended for validators to minimize downtime during upgrades. It automates the binary replacement process according to on-chain `SoftwareUpgrade` proposals.

Documentation for Cosmovisor can be found [here](https://docs.cosmos.network/main/tooling/cosmovisor).

#### Installation Steps

_Run these commands to install and configure Cosmovisor_:


```sh
go install github.com/cosmos/cosmos-sdk/cosmovisor/cmd/cosmovisor@v1.6.0
mkdir -p ~/.mantrachain
mkdir -p ~/.mantrachain/cosmovisor
mkdir -p ~/.mantrachain/cosmovisor/genesis
mkdir -p ~/.mantrachain/cosmovisor/genesis/bin
mkdir -p ~/.mantrachain/cosmovisor/upgrades
cp $GOPATH/bin/mantrachaind ~/.mantrachain/cosmovisor/genesis/bin
```

_Add these lines to your profile to set up environment variables_:

```sh
echo "# Setup Cosmovisor" >> ~/.profile
echo "export DAEMON_NAME=mantrachaind" >> ~/.profile
echo "export DAEMON_HOME=$HOME/.mantrachain" >> ~/.profile
echo "export DAEMON_ALLOW_DOWNLOAD_BINARIES=false" >> ~/.profile
echo "export DAEMON_LOG_BUFFER_SIZE=512" >> ~/.profile
echo "export DAEMON_RESTART_AFTER_UPGRADE=true" >> ~/.profile
echo "export UNSAFE_SKIP_BACKUP=true" >> ~/.profile
source ~/.profile
```

### Upgrading to v7.0.0

_To prepare for the upgrade, execute these commands_:

#### Approach 1: Download Pre-built Release

```sh
upgrade_version="7.0.0"
upgrade_name="v7.0.0"
mkdir -p ~/.mantrachain/cosmovisor/upgrades/$upgrade_name/bin
if [[ $(uname -m) == 'arm64' ]] || [[ $(uname -m) == 'aarch64' ]]; then export ARCH="arm64"; else export ARCH="amd64"; fi
if [[ $(uname) == 'Darwin' ]]; then export OS="darwin"; else export OS="linux"; fi
wget https://github.com/MANTRA-Chain/mantrachain/releases/download/v$upgrade_version/mantrachaind-$upgrade_version-$OS-$ARCH.tar.gz
tar -xvf mantrachaind-$upgrade_version-$OS-$ARCH.tar.gz -C ~/.mantrachain/cosmovisor/upgrades/$upgrade_name/bin
rm mantrachaind-$upgrade_version-$OS-$ARCH.tar.gz
```

#### Approach 2: Build from Source

```sh
upgrade_version="7.0.0"
upgrade_name="v7.0.0"
mkdir -p ~/.mantrachain/cosmovisor/upgrades/$upgrade_name/bin
cd $HOME/mantrachain
git fetch --tags
git checkout v$upgrade_version
make build
cp build/mantrachaind ~/.mantrachain/cosmovisor/upgrades/$upgrade_name/bin
```

At the designated block height, Cosmovisor will automatically upgrade to version v7.0.0.

---

## Manual Upgrade Procedure

Follow these steps if you opt for a manual upgrade:

1. Monitor Mantrachain until it reaches the specified upgrade block height: 13000000.
2. Observe for a panic message followed by continuous peer logs, then halt the daemon.
3. Perform these steps:

### Approach 1: Download Pre-built Release

```sh
upgrade_version="7.0.0"
upgrade_name="v7.0.0"
if [[ $(uname -m) == 'arm64' ]] || [[ $(uname -m) == 'aarch64' ]]; then export ARCH="arm64"; else export ARCH="amd64"; fi
if [[ $(uname) == 'Darwin' ]]; then export OS="darwin"; else export OS="linux"; fi
wget https://github.com/MANTRA-Chain/mantrachain/releases/download/v$upgrade_version/mantrachaind-$upgrade_version-$OS-$ARCH.tar.gz
tar -xvf mantrachaind-$upgrade_version-$OS-$ARCH.tar.gz -C $GOPATH/bin
```

### Approach 2: Build from Source

```sh
upgrade_version="7.0.0"
cd $HOME/mantrachain
git fetch --tags
git checkout v$upgrade_version
make install
```

4. Restart the Mantrachain daemon and observe the upgrade.

---

## Additional Resources

If you need more help, please:

- go to <https://docs.mantrachain.io>
- join our discord at <https://discord.gg/fHSqUng7Hy>.
