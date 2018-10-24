# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from scipy import stats

from bs4 import BeautifulSoup
import urllib3

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import style

style.use('ggplot')

class Index:
	def __init__(self, quote):
		self.http = urllib3.PoolManager()
		urllib3.disable_warnings()

		self.quote = quote

	def getQuote(self):
		return self.quote

	def getCurrentPrice(self):
		http = urllib3.PoolManager()
		urllib3.disable_warnings()

		S = http.request('GET', 'https://finance.yahoo.com/quote/' + self.quote + '?p=^' + self.quote)
		soup = BeautifulSoup(S.data, 'lxml')
		J = soup.find('span', class_ = 'Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)')

		return float(J.text.replace(',', ''))

	def getPrices(self, return_dates = False):
		DF = pd.read_csv('hist_data/' + self.quote + '.dat')

		closeDF = DF['Adj Close']
		dates = DF['Date']

		if return_dates:
			return np.array(closeDF), np.array(dates)
		else:
			return np.array(closeDF)

	def getVolume(self):
		return np.array(pd.read_csv('hist_data/' + self.quote + '.dat')['Volume'])

	def calcLogReturns(self):
		closeDF = pd.read_csv('hist_data/' + self.quote + '.dat')['Adj Close']
		logReturns = np.log(closeDF / closeDF.shift(1)).dropna()

		return np.array(logReturns)

	def calcExpReturn(self):
		return self.calcLogReturns().mean() * 252

	def calcStd(self):
		return self.calcLogReturns().std() * np.sqrt(252)

	def normalTest(self):
		return stats.normaltest(self.calcLogReturns())[1]

	def graphPrices(self):
		closeDF, dates = self.getPrices(return_dates = True)
		rollingMean = pd.DataFrame(closeDF).rolling(window = 60, min_periods = 0).mean()
		dates = pd.to_datetime(dates)
		volume = self.getVolume()

		fig, (ax1, ax2) = plt.subplots(2, sharex = True, gridspec_kw = {'height_ratios': [4, 1]})
		fig.autofmt_xdate()

		ax1.plot(dates, closeDF, color = 'blue', linewidth = 1.8, label = "Price")
		ax1.plot(dates, rollingMean, color = 'red', linewidth = 1.0, label = "Rolling Mean")

		ax2.bar(dates, volume, width = 2, color = 'blue', label = "Volume")

		plt.suptitle(str(self.getQuote()) + " value movement and Volume", fontsize = 20)
		ax1.set_ylabel("Price", fontsize = 12)
		ax2.set_ylabel("Volume", fontsize = 12)
		ax1.legend(loc = 2)
		xfmt = mdates.DateFormatter('%Y-%m-%d')
		ax1.xaxis.set_major_formatter(xfmt)

		plt.show()

	def graphLogReturns(self):
		logReturns = self.calcLogReturns()

		fig, (ax1, ax2) = plt.subplots(1, 2)

		ax1.plot(logReturns, color = 'blue', lw = 0.4)
		ax2.hist(logReturns, bins = 40, color = 'blue')

		ax1.set_ylabel("% Change", fontsize = 12)

		ax2.set_ylabel("Density", fontsize = 12)
		ax2.set_xlabel("% Change", fontsize = 15)
		plt.suptitle(str(self.getQuote()) + " Log Returns," + " μ = " + str(round(self.calcExpReturn(), 3)) + " σ = " + str(round(self.calcStd(), 3)), fontsize = 15)
		plt.show()