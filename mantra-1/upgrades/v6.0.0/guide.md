# Mainnet Upgrade Guide: From Version v5.0 to v6.0.0

## Overview

- **v6.0.0 Proposal**: [Proposal Page](https://www.mintscan.io/mantra/proposals/24)
- **v6.0.0 Upgrade Block Height**: 9664888
- **v6.0.0 Upgrade Countdown**: [Block Countdown](https://www.mintscan.io/mantra/block/9664888)
- **v6.0.0 Release**: [Release Page](https://github.com/MANTRA-Chain/mantrachain/releases/tag/v6.0.0)
- **v6.0.0 Docker Image**: [ghcr.io/mantra-chain/mantrachain:v6.0.0](https://github.com/mantra-chain/mantrachain/pkgs/container/mantrachain)

## Hardware Requirements

### Memory Specifications

Although this upgrade is not expected to be resource-intensive, a minimum of 32GB of RAM is advised. If you cannot meet this requirement, setting up a swap space is recommended.

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

### Upgrading to v6.0.0

_To prepare for the upgrade, execute these commands_:

#### Approach 1: Download Pre-built Release

```sh
upgrade_version="6.0.0"
upgrade_name="v6.0.0"
mkdir -p ~/.mantrachain/cosmovisor/upgrades/$upgrade_name/bin
if [[ $(uname -m) == 'arm64' ]] || [[ $(uname -m) == 'aarch64' ]]; then export ARCH="arm64"; else export ARCH="amd64"; fi
if [[ $(uname) == 'Darwin' ]]; then export OS="darwin"; else export OS="linux"; fi
wget https://github.com/MANTRA-Chain/mantrachain/releases/download/v$upgrade_version/mantrachaind-$upgrade_version-$OS-$ARCH.tar.gz
tar -xvf mantrachaind-$upgrade_version-$OS-$ARCH.tar.gz -C ~/.mantrachain/cosmovisor/upgrades/$upgrade_name/bin
rm mantrachaind-$upgrade_version-$OS-$ARCH.tar.gz
```

#### Approach 2: Build from Source

```sh
upgrade_version="6.0.0"
upgrade_name="v6.0.0"
mkdir -p ~/.mantrachain/cosmovisor/upgrades/$upgrade_name/bin
cd $HOME/mantrachain
git fetch --tags
git checkout v$upgrade_version
make build
cp build/mantrachaind ~/.mantrachain/cosmovisor/upgrades/$upgrade_name/bin
```

At the designated block height, Cosmovisor will automatically upgrade to version v6.0.0.

---

## Manual Upgrade Procedure

Follow these steps if you opt for a manual upgrade:

1. Monitor Mantrachain until it reaches the specified upgrade block height: 9664888.
2. Observe for a panic message followed by continuous peer logs, then halt the daemon.
3. Perform these steps:

### Approach 1: Download Pre-built Release

```sh
upgrade_version="6.0.0"
upgrade_name="v6.0.0"
if [[ $(uname -m) == 'arm64' ]] || [[ $(uname -m) == 'aarch64' ]]; then export ARCH="arm64"; else export ARCH="amd64"; fi
if [[ $(uname) == 'Darwin' ]]; then export OS="darwin"; else export OS="linux"; fi
wget https://github.com/MANTRA-Chain/mantrachain/releases/download/v$upgrade_version/mantrachaind-$upgrade_version-$OS-$ARCH.tar.gz
tar -xvf mantrachaind-$upgrade_version-$OS-$ARCH.tar.gz -C $GOPATH/bin
```

### Approach 2: Build from Source

```sh
upgrade_version="6.0.0"
cd $HOME/mantrachain
git fetch --tags
git checkout v$upgrade_version
make install
```

4. Restart the Mantrachain daemon and observe the upgrade.

---

## 🚨 Optional EVM Mempool Configuration for v6.0.0

The v6.0.0 release introduces the experimental Cosmos EVM mempool. You can optionally tune mempool behaviour ahead of the upgrade.

### Optional app.toml updates

Adjust `~/.mantrachain/config/app.toml` only if custom limits are required:

```toml
[mempool]
# Setting max-txs to 0 will allow for a unbounded amount of transactions in the mempool.
# Setting max_txs to negative 1 (-1) will disable transactions from being inserted into the mempool (no-op mempool).
# Setting max_txs to a positive number (> 0) will limit the number of transactions in the mempool, by the specified amount.
max-txs = 0

[evm]
evm-chain-id = 5888

[evm.mempool]
# PriceLimit is the minimum gas price to enforce for acceptance into the pool (in wei)
price-limit = 1
# PriceBump is the minimum price bump percentage to replace an already existing transaction (nonce)
price-bump = 10
# AccountSlots is the number of executable transaction slots guaranteed per account
account-slots = 16
# GlobalSlots is the maximum number of executable transaction slots for all accounts
global-slots = 5120
# AccountQueue is the maximum number of non-executable transaction slots permitted per account
account-queue = 64
# GlobalQueue is the maximum number of non-executable transaction slots for all accounts
global-queue = 1024
# Lifetime is the maximum amount of time non-executable transaction are queued
lifetime = "3h0m0s"
```


## Additional Resources

If you need more help, please:
    - go to <https://docs.mantrachain.io>
    - join our discord at <https://discord.gg/fHSqUng7Hy>.
