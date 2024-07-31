import uvicorn
from uvicorn.config import LOGGING_CONFIG
from fastapi import FastAPI
from config import config

app = FastAPI()


def run():
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s [%(name)s] %(levelprefix)s %(message)s"
    LOGGING_CONFIG["formatters"]["access"]["fmt"] = '%(asctime)s [%(name)s] %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
    uvicorn.run(app, host=config.host, port=config.port)
