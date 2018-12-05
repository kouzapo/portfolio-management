# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
from scipy.optimize import minimize

import matplotlib.pyplot as plt
from matplotlib import style

from Stock import *
from Index import *
from fixed_income import getRiskFreeRate

style.use('ggplot')

class StockPortfolio:
	def __init__(self, stocks):
		self.__stocks = stocks

	def getStocks(self):
		return self.__stocks

	def addStock(self, stock):
		self.getStocks().append(stock)

	def getStocksWeights(self):
		return np.array([stock.getWeight() for stock in self.__stocks])

	def __calcCovMatrix(self):
		ret = {}

		for stock in self.__stocks:
			ret[stock.getQuote()] = stock.calcLogReturns()

		ret = pd.DataFrame(ret)
		covMatrix = ret.cov()

		return ret, covMatrix

	def calcMinVarAlloc(self, save = True, allow_sort = False):
		n = len(self.__stocks)
		rets, covMatrix = self.__calcCovMatrix()

		#Formula calculation solution.
		'''C_inv = np.linalg.inv(covMatrix.values)
		e = np.ones(len(self.__stocks))

		weights = np.dot(e, C_inv) / np.dot(e, np.dot(C_inv, e))'''

		#Optimization solution.
		minFun = lambda weights: np.sqrt(np.dot(weights.T, np.dot(rets.cov() * 252, weights)))

		cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})

		if allow_sort:
			bnds = tuple((-1, 1) for _ in range(n))
		else:
			bnds = tuple((0, 1) for _ in range(n))

		res = minimize(minFun, n * [1 / n], method = 'SLSQP', bounds = bnds, constraints = cons)
		weights = res.get('x')
		i = 0

		if save:
			for stock in self.__stocks:
				stock.setWeight(weights[i])
				i += 1

		return weights

	def calcMinVarLine(self, mv, save = True, allow_sort = False):
		n = len(self.__stocks)
		rets, covMatrix = self.__calcCovMatrix()

		#Formula calculation solution.
		'''m = rets.mean() * 252
		C_inv = np.linalg.inv(covMatrix.values)
		e = np.ones(len(self.getStocks()))

		eC_invM = np.dot(np.dot(e, C_inv), m)
		mC_invM = np.dot(np.dot(m, C_inv), m)
		mC_invE = np.dot(np.dot(m, C_inv), e)
		eC_invE = np.dot(np.dot(e, C_inv), e)

		eC_inv = np.dot(e, C_inv)
		mC_inv = np.dot(m, C_inv)

		A = np.linalg.det([[1, eC_invM], [mv, mC_invM]])
		B = np.linalg.det([[eC_invE, 1], [mC_invE, mv]])
		C = np.linalg.det([[eC_invE, eC_invM], [mC_invE, mC_invM]])

		weights = (A * eC_inv + B * mC_inv) / C'''

		#Optimization solution.
		minFun = lambda weights: np.sqrt(np.dot(weights.T, np.dot(rets.cov() * 252, weights)))

		cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1}, {'type': 'eq', 'fun': lambda x: np.sum(rets.mean() * x) * 252 - mv})

		if allow_sort:
			bnds = tuple((-1, 1) for _ in range(n))
		else:
			bnds = tuple((0, 1) for _ in range(n))

		res = minimize(minFun, n * [1 / n], method = 'SLSQP', bounds = bnds, constraints = cons)
		weights = res.get('x')
		i = 0

		if save:
			for stock in self.getStocks():
				stock.setWeight(weights[i])
				i += 1

		return weights

	def maximizeSharpeRatio(self, rf, save = True):
		n = len(self.__stocks)
		rets, cov = self.__calcCovMatrix()

		def __minFunc(weights):
			weights = np.array(weights)
			portExpRet = np.sum(rets.mean() * weights) * 252
			portStd = np.sqrt(np.dot(weights.T, np.dot(rets.cov() * 252, weights)))

			return -((portExpRet - rf) / portStd)

		cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
		bnds = tuple((0, 1) for _ in range(n))

		res = minimize(__minFunc, n * [1 / n], method = 'SLSQP', bounds = bnds, constraints = cons)
		weights = res.get('x')
		i = 0

		if save:
			for stock in self.__stocks:
				stock.setWeight(weights[i])
				i += 1

		return weights

	def calcPerformance(self, *rf):
		rets, covMatrix = self.__calcCovMatrix()
		weights = self.getStocksWeights()

		exRet = np.dot(rets.mean(), weights) * 252
		std = np.sqrt(np.dot(weights, np.dot(covMatrix, weights))) * np.sqrt(252)

		if rf:
			benchmark = Index('^GSPC')

			sharpeRatio = (exRet - rf[0]) / std
			stocksBetas = np.array([s.calcBetaAlpha(benchmark)['beta'] for s in self.__stocks])
			stocksAlphas = np.array([s.calcBetaAlpha(benchmark)['alpha'] for s in self.__stocks])

			beta = stocksBetas.dot(weights)
			alpha = stocksAlphas.dot(weights)

			res = {'return': round(exRet, 5), 'std': round(std, 5), 'sharpe': round(sharpeRatio, 5), 'beta': round(beta, 5), 'alpha': round(alpha, 5)}
		else:
			res = {'return': round(exRet, 5), 'std': round(std, 5)}

		return res

	def graphEfficientFrontier(self):
		R = np.arange(0, 0.35, 0.01)

		portExpRet = []
		portStd = []

		for i in R:
			self.calcMinVarLine(i)
			res = self.calcPerformance()
			m = res['return']
			s = res['std']

			portExpRet.append(m)
			portStd.append(s)

		stockExpRet = []
		stockStd = []

		for stock in self.__stocks:
			stockExpRet.append(stock.calcExpReturn())
			stockStd.append(stock.calcStd())

		plt.plot(portStd, portExpRet, color = 'blue', linewidth = 2, label = "Efficient Frontier")
		plt.scatter(stockStd, stockExpRet, s = 30, color = 'red', label = "Asset")
		plt.ylabel("Expected return")
		plt.xlabel("Standard deviation")
		plt.title("Efficient Frontier with individual assets")
		plt.legend(loc = 2)
		plt.show()

		return portExpRet, portStd

	def __genRandomPortfolios(self, n):
		results = []

		for i in range(n):
			weights = np.random.random(len(self.__stocks))
			weights /= np.sum(weights)

			quotes = [s.getQuote() for s in self.__stocks]
			stocks = []
			j = 0

			for q in quotes:
				stocks.append(Stock(q, weights[j]))
				j += 1

			results.append(StockPortfolio(stocks))

		return results

	def graphSimulatedRandomProtfolios(self, I):
		P = self.__genRandomPortfolios(I)
		rf = getRiskFreeRate()['10Y']

		M = []
		S = []
		i = 0

		for p in P:
			res = p.calcPerformance()
			m = res['return']
			s = res['std']
			print(i)

			i += 1
			M.append(m)
			S.append(s)

		M = np.array(M)
		S = np.array(S)

		plt.scatter(S, M, s = 12, c = (M - rf) / S, alpha = 1, label = "Portfolio")
		plt.ylabel("Expected return")
		plt.xlabel("Standard deviation")
		plt.title("Simulated Random Portfolios")
		plt.colorbar(label = "Sharpe Ratio")
		plt.legend(loc = 2)
		plt.show()

class BondPortfolio:
	pass