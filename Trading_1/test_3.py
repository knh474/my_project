import pandas as pd
import requests
import time
import sys
t= time.gmtime()

file_today = '{}-{}-{}'.format(t.tm_year, t.tm_mon, t.tm_mday)

kospi_url = 'https://finance.naver.com/sise/sise_quant_high.nhn'
kosdaq_url = 'https://finance.naver.com/sise/sise_quant_high.nhn?sosok=1'

df = pd.DataFrame()

html_1 = requests.get(kospi_url).text
df = df.append(pd.read_html(html_1, header=0)[1])
html_2 = requests.get(kosdaq_url).text
df = df.append(pd.read_html(html_2, header=0)[1])
del df['PER']
df = df.dropna()
df = df.rename(columns={'N': 'num', '증가율': 'rate', '종목명': 'name', '현재가': 'price', '전일비': 'diff', '등락률': 'updown',
                             '매수호가': 'buy_hoga',
                             '매도호가': 'sell_hoga', '거래량': 'volume', '전일거래량': 'yes_volume'})
df = df.set_index(['num']) #크롤링완료

df.to_csv(sys.path[0] + '\\backup\\' + file_today+'_volume.csv',encoding='cp949')