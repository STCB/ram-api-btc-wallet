from config import config


class Data:
    def __init__(self):
        self.conf = config
        self.master_key = None
        self.wallets = []


data = Data()
