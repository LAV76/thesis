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


# Индикаторы

# поиск линии цены
def indSlope(series,n):
    
    array_sl = [j*0 for j in range(n-1)]
    
    for j in range(n,len(series)+1):
        y = series[j-n:j]
        x = np.array(range(n))
        x_sc = (x - x.min())/(x.max() - x.min())
        y_sc = (y - y.min())/(y.max() - y.min())
        x_sc = sm.add_constant(x_sc)
        model = sm.OLS(y_sc,x_sc)
        results = model.fit()
        array_sl.append(results.params.iloc[-1])
    slope_angle = (np.rad2deg(np.arctan(np.array(array_sl))))
    return np.array(slope_angle)


def indATR(source_DF,n):
    df = source_DF.copy()
    df['H-L']=abs(df['high']-df['low'])
    df['H-PC']=abs(df['high']-df['close'].shift(1))
    df['L-PC']=abs(df['low']-df['close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    df_temp = df.drop(['H-L','H-PC','L-PC'],axis=1)
    return df_temp


# ишем локальный min / max
def isLCC(DF,i):
    df=DF.copy()
    LCC=0
    
    if df['close'][i]<=df['close'][i+1] and df['close'][i]<=df['close'][i-1] and df['close'][i+1]>df['close'][i-1]:
        #найдено дно
        LCC = i-1;
    return LCC

def isHCC(DF,i):
    df=DF.copy()
    HCC=0
    if df['close'][i]>=df['close'][i+1] and df['close'][i]>=df['close'][i-1] and df['close'][i+1]<df['close'][i-1]:
        #найдена вершина
        HCC = i;
    return HCC


# получить ценовой канал
def getMaxMinChannel(DF, n):
    maxx=0
    minn=DF['low'].max()
    for i in range (1,n):
        if maxx<DF['high'][len(DF)-i]:
            maxx=DF['high'][len(DF)-i]
        if minn>DF['low'][len(DF)-i]:
            minn=DF['low'][len(DF)-i]
    return(maxx,minn)


# Добавляем новые данные
def PrepareDF(DF):
    ohlc = DF.iloc[:,[0,1,2,3,4,5]]
    ohlc.columns = ["date","open","high","low","close","volume"]
    ohlc=ohlc.set_index('date')
    df = indATR(ohlc,14).reset_index()
    df['slope'] = indSlope(df['close'],5)
    df['channel_max'] = df['high'].rolling(10).max()
    df['channel_min'] = df['low'].rolling(10).min()
    df['position_in_channel'] = (df['close']-df['channel_min']) / (df['channel_max']-df['channel_min'])
    df = df.set_index('date')
    df = df.reset_index()
    return(df)


def check_if_signal(symbol):
    ohlc = get_futures_klines(symbol,100)
    prepared_df = PrepareDF(ohlc)
    signal=""
    
    i=98
    
    if isLCC(prepared_df,i-1)>0:
       # найдкно дно - OPEN LONG
        if prepared_df['position_in_channel'][i-1]<0.5:
            # близко к вершине канала
            if prepared_df['slope'][i-1]<-20:
                # точка входа в LONG
                signal='long'

    if isHCC(prepared_df,i-1)>0:
       # найден максимум - OPEN SHORT
        if prepared_df['position_in_channel'][i-1]>0.5:
            # близко к вершине канала
            if prepared_df['slope'][i-1]>20:
                # точка входа в SHORT
                signal='short'

    return signal