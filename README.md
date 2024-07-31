# ram-api-btc-wallet
A ram-only Bitcoin server-wallet

Please create an issue if you have a better name !

A deterministic ram-only bitcoin server-wallet => Interact through REST Api and STORES NO DATA

-----
# Kinda works !
Will send testnet coins to one or a list of bitcoin segwit addresses.
Because it entirely depends on Bitcoinlib, it does not support taproot yet.

## How ?

Install dependencies (requirements.txt)

Feed it a mnemonic phrase (or the path to a file containing one), a passphrase, and you're ready to go.

Warning, if you're using a mnemonic file, input an absolute path / a path relative to the location of main.py

I recommend "-p any" if you are not used to Bitcoinlib providers.

Please be careful and prefer "-n testnet" to play in testnet rather than mainnet.

## Coding

You're welcomed to issue or PR !

We need tons of things, like:
- tests
- consolidation
- tests
- security improvements
- working without blocking on every call
- seemless legacy support
- tests
