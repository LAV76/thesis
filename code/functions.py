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

# последние 500 свечей за 5 минут дл Symbol

def get_futures_klines(symbol,limit=500):
    x = requests.get('https://binance.com/fapi/v1/klines?symbol='+symbol+'&limit='+str(limit)+'&interval=5m')
    df=pd.DataFrame(x.json())
    df.columns=['open_time','open','high','low','close','volume','close_time','d1','d2','d3','d4','d5']
    df=df.drop(['d1','d2','d3','d4','d5'],axis=1)
    df[['open','high','low','close','volume']]=df[['open','high','low','close','volume']].astype(float)
    return(df)


# Открытие позиции для пары Symbol 

def open_position(symbol,s_l,quantity_l):
    prt('open: '+symbol+' quantity: '+str(quantity_l))
    sprice=get_symbol_price(symbol)

    if(s_l=='long'):
        close_price=str(round(sprice*(1+0.01),2))
        params = {
            "batchOrders": [
                {
                    "symbol":symbol,
                    "side": "BUY",
                    "type": "LIMIT",
                    "quantity": str(quantity_l),
                    "timeInForce":"GTC",
                    "price": close_price        

                }
            ]
        }
        responce = send_signed_request('POST', '/fapi/v1/batchOrders', params)
        #print(responce)
       
       
    if(s_l=='short'):
        close_price=str(round(sprice*(1-0.01),2))
        params = {
            "batchOrders": [
                {
                    "symbol":symbol,
                    "side": "SELL",
                    "type": "LIMIT",
                    "quantity": str(quantity_l),
                    "timeInForce":"GTC",
                    "price": close_price
                }
           ]
        }
        responce = send_signed_request('POST', '/fapi/v1/batchOrders', params)


# закрытие позиции symbol

def close_position(symbol,s_l,quantity_l):
    prt('close: '+symbol+' quantity: '+str(quantity_l))

    sprice=get_symbol_price(symbol)

    if(s_l=='long'):
        close_price=str(round(sprice*(1-0.01),2))
        params = {
                    "symbol":symbol,
                    "side": "SELL",
                    "type": "LIMIT",
                    "quantity": str(quantity_l),
                    "timeInForce":"GTC",
                    "price": close_price
                }
        responce = send_signed_request('POST', '/fapi/v1/order', params)
        print (responce)

    if(s_l=='short'):
        close_price=str(round(sprice*(1+0.01),2))
        params = {
                
                    "symbol":symbol,
                    "side": "BUY",
                    "type": "LIMIT",
                    "quantity": str(quantity_l),
                    "timeInForce":"GTC",
                    "price": close_price        
                }
        responce = send_signed_request('POST', '/fapi/v1/order', params)
        print (responce)


# Показывает открытые позиции и др. информацию

def get_opened_positions(symbol):
    status = client.futures_account()
    positions=pd.DataFrame(status['positions'])
    a = positions[positions['symbol']==symbol]['positionAmt'].astype(float).tolist()[0]
    leverage = int(positions[positions['symbol']==symbol]['leverage'].iloc[0])
    entryprice = float(positions[positions['symbol'] == symbol]['entryPrice'].iloc[0])
    profit = float(status['totalUnrealizedProfit'])
    balance = round(float(status['totalWalletBalance']),2)
    if a>0:
        pos = "long"
    elif a<0:
        pos = "short"
    else: 
        pos = ""
    return([pos,a,profit,leverage,balance,round(float(entryprice),3),0])


# закрыть все ордера

def check_and_close_orders(symbol):
    global isStop 
    a=client.futures_get_open_orders(symbol=symbol)
    if len(a)>0:
        isStop = False
        client.futures_cancel_all_open_orders(symbol=symbol)


# получить текущую цену
def get_symbol_price(symbol):
    prices = client.get_all_tickers()
    df=pd.DataFrame(prices)
    return float(df[ df['symbol']==symbol]['price'].iloc[0])