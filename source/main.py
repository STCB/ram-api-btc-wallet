#!/usr/bin/env python3
import os
from time import time
from fastapi import FastAPI, HTTPException
from bitcoinlib.keys import HDKey
import uvicorn
import sys
from pydantic import BaseModel
from config import config
from arguments import check_args
from data import data
from blockchain import derive_wallet, fetch_balance, create_tx_and_send, wallet_for_address
from dotenv import load_dotenv
from server import app, run

load_dotenv()
print("Wallet Management System")


@app.get("/")
async def root():
    return {"message": "Wallet Management System"}


@app.get("/wallet/path")
async def get_path(address: str):
    wallet = wallet_for_address(address)
    if wallet:
        return wallet
    return "Wallet not found."


@app.get("/wallet/get_addresses")
async def get_addresses():
    if not data.wallets:
        return "No wallets found."
    return [item["address"] for item in data.wallets]


@app.get("/wallet/get_balance")
async def get_balance(address: str = None):
    start = time()
    if not data.wallets:
        return "No wallets found."

    if address is None:
        balances = []
        for wallet in data.wallets:
            if wallet["last_fetch"] + 5 * 60 < int(time()):
                balances.append(fetch_balance(wallet))
            else:
                balances.append(wallet["balance"])
        return balances

    wallet = wallet_for_address(address)
    if not wallet:
        return "Wallet not found."
    if wallet["last_fetch"] + 5 * 60 < int(time()):
        res = fetch_balance(wallet)
        print("Time taken:", time() - start)
        return res
    else:
        return wallet["balance"]


class Emitter(BaseModel):
    address: str

class Target(BaseModel):
    address: str
    amount: int


class Sending(BaseModel):
    sender: list[Emitter]
    targets: list[Target]
    fee: int = 10


@app.post("/wallet/send")
async def send_bitcoins(_sending: Sending, broadcast: bool = True):
    _senders = []
    _targets = [(tx.address, tx.amount) for tx in _sending.targets]

    for sender in _sending.sender:
        wallet = wallet_for_address(sender.address)
        if wallet:
            _senders.append(wallet)
        else:
            raise HTTPException(status_code=401, detail="Sender wallets not found")

    total_balance = 0
    for sender in _senders:
        if sender["last_fetch"] + 5 * 60 < int(time()):  # 5 minutes
            _balance = fetch_balance(sender)
        total_balance += sender["balance"]

    total_amount = sum(amount for _, amount in _targets)
    if total_balance < total_amount:
        raise HTTPException(status_code=402, detail="Insufficient balance")

    try:
        res = create_tx_and_send(_senders, _targets, _sending.fee, broadcast)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return res

@app.delete("/wallet/del_wallet")
async def delete_wallet(address: str):
    _w = wallet_for_address(address)
    if _w:
        data.wallets.remove(_w)
        return {"message": "Wallet deleted successfully"}
    raise HTTPException(status_code=404, detail="Wallet not found")


@app.post("/wallet/new_wallet")
async def create_new_wallet(number: int = 1):
    return [derive_wallet() for _ in range(number)]


if __name__ == "__main__":
    try:
        config.host = os.getenv("HOST", config.host)
        config.port = int(os.getenv("PORT", config.port))
        check_args()
    except Exception as e:
        print("Error in arguments.\n", e)
        sys.exit(1)
    data.master_key = HDKey.from_seed(config.shared_seed, network=config.network, witness_type="segwit")
    run()
