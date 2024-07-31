import argparse

import bitcoinlib.services.services
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib import services
from bitcoinlib.services.bcoin import BcoinClient
import hashlib
from config import config, BCOIN_DEFAULT_URL
import re

parser = argparse.ArgumentParser(description="Wallet Management System")
parser.add_argument('mnemonic', help="Mnemonic for wallet recovery or its file path")
parser.add_argument('passphrase', help="Passphrase for wallet encryption and operation")
parser.add_argument('-p', '--provider', default="bcoin", help="URL of the bcoin node")
parser.add_argument('-u', '--url', default=BCOIN_DEFAULT_URL, help="URL of the bcoin node")
parser.add_argument('-d', '--derivation', help="Bitcoin derivation path", metavar='PATH', type=str, default="m/44'/0'/0'/0/0")
parser.add_argument('-n', '--network', default="bitcoin", help="Network to connect to (e.g., bitcoin, testnet)")
parser.add_argument('-wp', '--webport', type=int, help="Port to run the application on")
parser.add_argument('--host', default="127.0.0.1", help="Host to run the application on")

_args = parser.parse_args()


def check_mnemonic(mnemonic):
    mnemo = Mnemonic()
    result = 0

    try:
        with open(mnemonic, 'r') as f:
            content = f.read().strip()
            mnemo.to_seed(content)
            config.mnemo_type = 1
            result = 1
    except Exception:
        print("Mnemonic is not a valid file. Trying as a mnemonic phrase.")
    if result == 0:
        mnemo.to_seed(mnemonic)


def check_mnemonic_passphrase(mnemonic, passphrase):
    mnemo = Mnemonic()

    if config.mnemo_type == 1:
        with open(mnemonic, 'r') as f:
            content = f.read().strip()
            config.shared_seed = mnemo.to_seed(content, password=passphrase)
    else:
        config.shared_seed = mnemo.to_seed(mnemonic, password=passphrase)
    print("Mnemonic and passphrase loaded successfully.\n\tFingerprint:", hashlib.sha256(config.shared_seed).hexdigest())


def check_provider(provider):
    services = [
        "baseclient",
        "authproxy",
        "bitcoinlibtest",
        "bitcoind",
        "dogecoind",
        "litecoind",
        "dashd",
        "bitgo",
        "blockchaininfo",
        "blockcypher",
        "cryptoid",
        "litecoreio",
        "blockchair",
        "bcoin",
        "bitaps",
        "litecoinblockexplorer",
        "insightdash",
        "blockstream",
        "blocksmurfer",
        "mempool",
        "bitflyer",
        "blockbook"
    ]
    if provider not in services and not "any":
        raise ValueError("Provider must be in the bitcoinlib's handled services.")
    if provider not in ["bcoin", "blockchaininfo", "blockstream", "any"]:
        raise ValueError("Provider currently not supported. Implement it yourself !")
    config.provider = provider
    print("Provider set to", provider)


def check_url(url):
    if config.provider != "bcoin":
        if url != BCOIN_DEFAULT_URL:
            print("URL is only used for bcoin provider. SKIPPED.")
        return

    if not url.startswith("http"):
        raise ValueError("URL must start with http or https.")
    try:
        config.provider = BcoinClient(base_url=url, network=config.network, denominator=100000000)
        block = config.provider.getinfo()["blockcount"]
    except TypeError:
        raise ValueError("Invalid URL or network: could not connect to the bcoin node.")
    print("Successfully connected to", url, "\n\tblock height", block, "\n\tnetwork", config.network)


def check_derivation(derivation):
    if not bool(re.compile(r"^[mM](?:/\d+'?)*$").match(derivation)):
        raise ValueError("Invalid derivation path ", derivation)
    config.derivation = derivation


def check_network(network):
    if network not in ["bitcoin", "testnet", "regtest"]:
        raise ValueError("Network must be either 'bitcoin' or 'testnet'.")
    config.network = network


def check_port(port):
    if port <= 1000 or port > 65535:
        raise ValueError("Port must be a positive integer between 1000 and 65535.")
    config.port = port
    print("Port set to", port)


def check_host(host):
    print("Checking host", host)
    if not bool(re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$").match(host)):
        raise ValueError("Host must be a valid IPv4 address.")
    config.host = host


# Dictionnaire associant chaque argument à sa fonction de vérification
arg_checkers = {
    'webport': check_port,
    'mnemonic': check_mnemonic,
    'passphrase': check_mnemonic_passphrase,
    'provider': check_provider,
    'derivation': check_derivation,
    'network': check_network,
    'host': check_host,
    'url': check_url,
}


## Provider 'ANY' is TOO LONG (15s to fetch a single balance)
def initialize_provider():
    if config.url == BCOIN_DEFAULT_URL:
        return
    print("Initializing provider...")
    try:
        if config.provider != "any":
            config.provider = bitcoinlib.services.services.Service(network=config.network, providers=[config.provider])
        else:
            config.provider = bitcoinlib.services.services.Service(network=config.network, max_providers=10)
    except Exception as e:
        print("Error in provider initialization.\n", e)
        raise
    print("Provider initialized successfully !  | ", config.provider.getinfo())


def check_args():
    for arg_name, arg_value in vars(_args).items():
        if arg_name in arg_checkers:
            if arg_name == 'passphrase':
                arg_checkers[arg_name](_args.mnemonic, arg_value)
            else:
                arg_checkers[arg_name](arg_value)
    initialize_provider()


def get_args():
    return _args
