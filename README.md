# Mantrachain Networks

This repository contains network information for the various Mantrachain networks.

In general, there will be three networks available at any given time:

| Network                    | Status             | Network version (binary version) | Description                                            |
| -------------------------- | ------------------ | -------------------------------- | ------------------------------------------------------ |
| [mainnet](mantra-1)        | :heavy_check_mark: | v3 (3.0.0)                       | Mantrachain Network mainnet network.                   |
| [testnet](mantra-dukong-1) | :heavy_check_mark: | v3 (3.0.0)                       | Mantrachain Network testnet network.                   |


Each network has a corresponding directory (linked to above) containing network information.
Each directory includes, at a minimum:

| File               | Description                                                                        |
| ------------------ | ---------------------------------------------------------------------------------- |
| `version.txt`      | The [Mantrachain](//github.com/MANTRA-Chain/mantrachain/releases) version used to participate in the network. |
| `chain-id.txt`     | The "chain-id" of the network.                                                     |
| `genesis.json`     | The genesis file for the network.                                                  |
| `seed-nodes.txt`   | A list of seed node addresses for the network.                                     |
| `rpc-nodes.txt`    | A list of RPC node addresses for the network.                                      |
| `api-nodes.txt`    | A list of API (LCD) node addresses for the network.                                |
| `explorer-url.txt` | The URL of an explorer UI for the network.                                         |

## Usage

The information in this repo may be used to automate tasks when deploying or configuring
[Mantrachain](//github.com/MANTRA-Chain/mantrachain) software.

The format is standardized across the networks so that you can use the same method
to fetch the information for all of them - just change the base URL

```sh
MANTRACHAIN_NET_BASE=https://raw.githubusercontent.com/MANTRA-Chain/net/main

##
#  Use _one_ of the following:
##

# mantra-1
MANTRACHAIN_NET="$MANTRACHAIN_NET_BASE/mantra-1"

# mantra-dukong-1
MANTRACHAIN_NET="$MANTRACHAIN_NET_BASE/mantra-dukong-1"
```

## Fetching Information

### Version

```sh
MANTRACHAIN_VERSION="$(curl -s "$MANTRACHAIN_NET/version.txt")"
```

### Chain ID

```sh
MANTRACHAIN_CHAIN_ID="$(curl -s "$MANTRACHAIN_NET/chain-id.txt")"
```

### Genesis

```sh
curl -s "$MANTRACHAIN_NET/genesis.json" > genesis.json
```

### Seed Nodes

```sh
curl -s "$MANTRACHAIN_NET/seed-nodes.txt" | paste -d, -s
```

### RPC Node

Print a random RPC endpoint

```sh
curl -s "$MANTRACHAIN_NET/rpc-nodes.txt" | shuf -n 1
```

### API Node

Print a random API endpoint

```sh
curl -s "$MANTRACHAIN_NET/api-nodes.txt" | shuf -n 1
```
