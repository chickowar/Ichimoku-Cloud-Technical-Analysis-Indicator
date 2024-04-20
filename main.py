from tinkoff.invest import Client

TOKEN = '' # не указываю

from tinkoff.invest import Client, SecurityTradingStatus, CandleInterval
from tinkoff.invest.services import InstrumentsService
from tinkoff.invest.utils import quotation_to_decimal, now
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go

from datetime import timedelta


def unit_to_float(u_and_n):
    return float(u_and_n.units + u_and_n.nano/1e9)

def max_in_n(l, n):
    ret = []
    #ret = [0 for i in range(n-1)] # первые n-1 элементов оставляем 0
    size = len(l)
    previous_maxel_ind = -1 # храним индекс наибольшего элемента
    for i in range(n-1, size): # запускаем цикл от n-го элемента
        maxel = 0
        for j in range( max(i-n+1, previous_maxel_ind), i): # нижнюю границу будем ставить на пердыдущем максимуме, ведь элементы до него его меньше
            if l[j] >= maxel:
                maxel = l[j]
                previous_maxel_ind = j
        ret.append(maxel)
    # first = ret[n-1]
    # for i in range(n-1): # заполняем нулевые элементы первым ненулевым
    #     ret[i] = first
    return ret

def min_in_n(l, n):
    ret = []
    #ret = [10e15 for i in range(n - 1)]  # первые n-1 элементов оставляем безумно большими
    size = len(l)
    previous_minel_ind = -1  # храним индекс наименьшего элемента
    for i in range(n - 1, size):  # запускаем цикл от n-го элемента
        minel = 10e15
        for j in range(max(i - n + 1, previous_minel_ind), i):  # нижнюю границу будем ставить на пердыдущем минимуме, ведь элементы до него его больше
            if l[j] <= minel:
                minel = l[j]
                previous_minel_ind = j
        ret.append(minel)
    # first = ret[n - 1]
    # for i in range(n - 1):  # заполняем нулевые элементы первым негигантским
    #     ret[i] = first
    return ret

def average_list(h : list, l : list, s = 0, e = -1):
    if e == -1:
        e = len(h)

    ret = []
    for i in range(s, e):
        ret.append((h[i]+l[i])/2)
    return ret

def change_color(fig, color):
    fig.update_traces(line=dict(color=color))

with Client(TOKEN) as client:
    instruments: InstrumentsService = client.instruments
    tickers = []
    for method in ["shares", "bonds", "etfs", "currencies", "futures"]:
        for item in getattr(instruments, method)().instruments:
            tickers.append(
                {
                    "name": item.name,
                    "ticker": item.ticker,
                    "class_code": item.class_code,
                    "figi": item.figi,
                    "uid": item.uid,
                    "type": method,
                    "min_price_increment": quotation_to_decimal(
                        item.min_price_increment
                    ),
                    "scale": 9 - len(str(item.min_price_increment.nano)) + 1,
                    "lot": item.lot,
                    "trading_status": str(
                        SecurityTradingStatus(item.trading_status).name
                    ),
                    "api_trade_available_flag": item.api_trade_available_flag,
                    "currency": item.currency,
                    "exchange": item.exchange,
                    "buy_available_flag": item.buy_available_flag,
                    "sell_available_flag": item.sell_available_flag,
                    "short_enabled_flag": item.short_enabled_flag,
                    "klong": quotation_to_decimal(item.klong),
                    "kshort": quotation_to_decimal(item.kshort),
                }
            )
    tickers_df = pd.DataFrame(tickers)
    tickers_df.to_csv('tickers.csv')
    ticker = "SNGS"

    ticker_df = tickers_df[tickers_df["ticker"] == ticker]
    ticker_df.to_csv('our_tickers.csv')
    figi = str(ticker_df['figi']).split()[1]

    # candles
    prices = []
    times = []
    lows = []
    highs = []
    days = int(input("Введите количество дней для анализа: "))
    if days<7:
        days=7
        print("мало. давай 7")
    for candle in client.get_all_candles(
            figi=figi,
            from_=now() - timedelta(days=days),
            interval=CandleInterval.CANDLE_INTERVAL_HOUR,
    ):
        print(candle)
        prices.append( unit_to_float(candle.open) )
        lows.append(unit_to_float(candle.low))
        highs.append(unit_to_float(candle.high))
        current_time = str(candle.time).split()
        current_hour = current_time[1][0:5]
        current_date = current_time[0].split('-')
        current_date = f"{current_date[2]}.{current_date[1]}.{current_date[0][2:]}"
        print(current_date, current_hour)
        times.append(f"{current_date} {current_hour}")
    for i in range(1, 27):
        times.append(f"+ {str(2*i)} часов")
    # print(prices)

    # позорнейший поиск минимума и максимума в тупую
    highs_max_in_9 = max_in_n(highs, 9)
    lows_min_in_9 = min_in_n(lows, 9)
    tenkan = average_list(highs_max_in_9, lows_min_in_9)
    highs_max_in_26 = max_in_n(highs, 26)
    lows_min_in_26 = min_in_n(lows, 26)
    kijun = average_list(highs_max_in_26, lows_min_in_26)
    senkou1 = average_list(tenkan[26-9:], kijun)
    highs_max_in_52 = max_in_n(highs, 52)
    lows_min_in_52 = min_in_n(lows, 52)
    senkou2 = average_list(highs_max_in_52, lows_min_in_52)
    chinkou = prices[26:]

    lt = len(times)

    # plotting
    fig = px.line(x=times[:lt-26], y=prices, labels={'x': 'Время', 'y': 'Цена'})
    fig1 = px.line(x=times[8:lt-26], y=tenkan, labels={'x': 'Время', 'y': 'Цена'})
    fig2 = px.line(x=times[25:lt-26], y=kijun, labels={'x': 'Время', 'y': 'Цена'})
    fig3 = px.line(x=times[25+26:], y=senkou1, labels={'x': 'Время', 'y': 'Цена'})
    fig4 = px.line(x=times[51+26:], y=senkou2, labels={'x': 'Время', 'y': 'Цена'})
    fig5 = px.line(x=times[:lt-52], y=chinkou, labels={'x': 'Время', 'y': 'Цена'})

    change_color(fig, 'lightgray')
    change_color(fig1, 'lime')
    change_color(fig2, 'darkgreen')
    change_color(fig3, 'red')
    change_color(fig4, 'blue')
    change_color(fig5, 'darkgray')

    fig.write_image("price.png")
    fig1.write_image("tenkan.png")
    fig2.write_image("kijun.png")
    fig3.write_image("senkou1.png")
    fig4.write_image("senkou2.png")
    fig5.write_image("chinkou.png")

    colored_fig = go.Figure()

    colored_fig.add_trace(go.Scatter(x=times[52 + 25:],
                                     y=senkou2,
                                     fill='none',
                                     showlegend=False,
                                     line=dict(color='rgba(255,255,255,0)'),
                                     name='Закрашенная область1'))
    colored_fig.add_trace(go.Scatter(x=times[52 + 25:],
                             y= senkou1[26:],
                             fill='tonexty',
                             fillcolor='rgba(128,0,128,0.3)',
                             line=dict(color='rgba(255,255,255,0)'),
                             showlegend=False,
                             name='Закрашенная область'))

    colored_fig.write_image("cf.png")

    figbig = go.Figure(data = fig.data + fig5.data + fig1.data + fig2.data + colored_fig.data + fig3.data + fig4.data)


    figbig.write_image("combined.png")