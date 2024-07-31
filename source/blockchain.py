from time import time

from bitcoinlib.keys import HDKey
from fastapi import HTTPException
import requests
from data import data
import bitcoinlib.transactions as tx
from errors import WalletError


def check_transaction_confirmation(tx_hash):
    response = requests.get(f"https://blockchain.info/rawtx/{tx_hash}")
    if response.status_code == 200:
        transaction_data = response.json()
        confirmations = transaction_data["confirmations"]
        return confirmations
    else:
        return 84


def get_default_path():
    return data.conf.derivation.rsplit('/', 1)[0] + "/" + str(len(data.wallets))


def derive_wallet(path=None):
    if path is None:
        path = get_default_path() # Python c'est de la grosse merde et n'execute qu'une seule fois la fonction si elle est passée en paramètre par défaut
    wallet = data.master_key.subkey_for_path(path, data.conf.network)
    data.wallets.append(
        {
            "address": wallet.address(),
            "balance": 0,
            "last_fetch": 0,
            "uses": 0,
            "HDKey": wallet,
            "path": path
        }
    )
    bal = fetch_balance(data.wallets[-1])
    return {"address": wallet.address(), "balance": bal}


def fetch_balance(wallet):
    print("Fetching balance for ", wallet["address"],". Last fetch: ", int(time()) - int(wallet["last_fetch"]))
    res = data.conf.provider.getbalance(wallet["address"])
    wallet["balance"] = res
    wallet["last_fetch"] = int(time())
    return res


def wallet_for_address(address):
    for wallet in data.wallets:
        if wallet["address"] == address:
            return wallet
    return None


def select_utxos_for_targets(_utxos, targets):
    total_target_amount = sum(amount for _, amount in targets)

    all_utxos = []
    for utxos in _utxos:
        all_utxos.extend(utxos)
    all_utxos.sort(key=lambda x: x['value'], reverse=True)

    selected_utxos = []
    running_total = 0

    for utxo in all_utxos:
        if running_total >= total_target_amount:
            break
        selected_utxos.append(utxo)
        running_total += utxo['value']

    if running_total < total_target_amount:
        raise WalletError("Insufficient balance")

    return selected_utxos, running_total - total_target_amount


def build_tx(_utxos, _tx, targets, fee):
    try:
        selected_utxos, _rest = select_utxos_for_targets(_utxos, targets)
    except HTTPException as e:
        raise e
    if fee < 0:
        fee = data.conf.provider.estimatefee()

    ### Inputs
    for _utxo in selected_utxos:
        _tx.add_input(_utxo['txid'], _utxo['output_n'], address=_utxo['address'], witness_type='segwit', value=_utxo['value'])
        print("Input value: ", _utxo['value'], "id:", _utxo['txid'][0:10], "...")

    print("Transaction inputs: ", _tx.inputs)

    ### Outputs
    for addr, amount in targets:
        _tx.add_output(amount, address=addr)

    ### Fee / change printing and management (ugly)
    tx_size_with_change = _tx.estimate_size(number_of_change_outputs=1)
    tx_wu_with_change = _tx.calc_weight_units()
    tx_size_without_change = _tx.estimate_size(number_of_change_outputs=0)
    tx_wu_without_change = _tx.calc_weight_units()
    print("Transaction V-SIZE with change: ", tx_size_with_change, " without change: ", tx_size_without_change)
    print("Transaction WU size with change: ", tx_wu_with_change, " without change: ", tx_wu_without_change)
    print("Fee rate: ", fee)
    _tx_fee_change = tx_size_with_change * fee
    _tx_fee = tx_size_without_change * fee
    print("Transaction FEE with change: ", _tx_fee_change, " without change: ", _tx_fee)
    print("Rest: ", _rest)
    if _tx_fee_change < _rest:
        _tx.add_output(int(_rest - _tx_fee_change), address=selected_utxos[0]['address'])
        print("Change added: ", _rest - _tx_fee_change)
    else:
        if _tx_fee > _rest:
            raise WalletError(f"Fees: Insufficient balance ( {_rest}, < {_tx_fee},)")

    ### Signing each input
    for _input in _tx.inputs:
        print("Signing input: ", _input.address, " value: ", _input.value)
        print("Key to sign:", wallet_for_address(_input.address)["HDKey"].private_hex)
        _tx.sign(keys=wallet_for_address(_input.address)["HDKey"].private_hex, fail_on_unknown_key=False)

    return _tx


def send_tx(_tx: tx.Transaction):

    broadcast = data.conf.provider.sendrawtransaction(_tx.raw_hex())
    if not broadcast:
        raise ValueError("Cannot send transaction. ", data.conf.provider.errors)
    if 'txid' in broadcast:
        print("Successfully pushed transaction, result: %s" % broadcast)
        txid = broadcast['txid']
        response_dict = data.conf.provider.results
        return txid, response_dict
    raise WalletError("Transaction not send, unknown response from service providers")


def create_tx_and_send(senders: list, targets, fee=10, broadcast=True):
    _utxos = []
    for sender in senders:
        _utxos.append(data.conf.provider.getutxos(sender["address"]))

    _tx = tx.Transaction(network=data.conf.network, fee_per_kb=fee, witness_type='segwit')

    try:
        _tx = build_tx(_utxos, _tx, targets, fee)
    except WalletError as e:
        print("Error in transaction building: ", e)
        return e

    status = _tx.verify()
    if status:
        print("Transaction verified")
    else:
        print("Transaction verification failed")
        return _tx.as_json()

    print("Transaction: ", _tx.as_json())
    if broadcast:
        return send_tx(_tx)
    else:
        return _tx.as_json()

