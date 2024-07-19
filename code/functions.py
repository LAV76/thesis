import requests
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import copy
import time
import random

from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
from binance_py import send_signed_request, send_public_request
from ENV import KEY, SECRET, TOKEN, ID

symbol='BNBUSDT'
client = Client(KEY, SECRET)

maxposition=0.03
stop_percent=0.01 # 0.01=1%
eth_proffit_array=[[20,1],[40,1],[60,2],[80,2],[100,2],[150,1],[200,1],[200,0]]
proffit_array=copy.copy(eth_proffit_array)
telegram_delay=12
bot_token=TOKEN
chat_id=ID
pointer=str(random.randint(1000, 9999))