
BCOIN_DEFAULT_URL = "http://localhost:8332"


class Config:
    def __init__(self):
        self.shared_seed = None
        self.url = None
        self.provider = BCOIN_DEFAULT_URL
        self.network = "bitcoin"
        self.port = 8069
        self.derivation = "m/44'/0'/0'/0'/0'"
        self.mnemo_type = None  # 1 = file
        self.host = "127.0.0.1"


config = Config()  # Create a global config instance
