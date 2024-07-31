from fastapi.testclient import TestClient
from source import main  # replace with your actual app

client = TestClient(main.app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Wallet Management System"}


## LOL, this is supposed to be used in PROD ?? Really ?? (issouuuu)
