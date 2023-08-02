# -*- coding: utf-8 -*-
"""
Created on Tue Jun  6 09:14:36 2023

@author: mlevine4
"""

import numpy as np  # type: ignore
from scipy.stats import beta as bt # type: ignore
import matplotlib.pyplot as plt # type: ignore


class BetaGen():
    
    def __init__(self, alpha, beta, t_start = 0, t_end = 1):
        self.alpha= alpha
        self.beta = beta
        self.t_start = t_start
        self.t_end = t_end
        
        self.fig, self.ax = plt.subplots(1,1)
        self.mean, self.var, self.skew, self.kurt = bt.stats(alpha, beta, t_start, t_end, moments = 'mvsk')
        
        self.t = np.linspace(0, t_end, 100)
        y = bt.pdf(self.t, alpha, beta, t_start, t_end)
        self.y = bt.pdf(self.t, alpha, beta, t_start, t_end)/max(y)
        self.ax.plot(self.t, self.y, 'r-', lw=5, alpha=0.6, label = 'predicted utility (beta pdf)')

        self.ax.plot(self.t, bt.pdf(self.t, alpha, beta, t_start, t_end)/max(y), 'k-', lw=2, label = 'predicted utility (frozen pdf)')

        self.vals = bt.ppf([0, t_end/100, t_end], alpha, beta, t_start, t_end)/max(y)
        np.allclose([0, t_end/100, t_end], bt.cdf(self.vals, alpha, beta, t_start, t_end)/max(y))
        self.r = bt.rvs(alpha, beta, t_start, t_end, size=1000)

        # self.ax.hist(self.r, density=True, bins='auto', histtype='stepfilled', alpha = 0.2)
        self.ax.set_xlim([self.t[0], self.t[-1]])
        self.ax.legend(loc='best', frameon=False)
        # plt.show()
        
    def tweak(self):
        self.alpha_actual = np.random.default_rng().normal(self.alpha, 0.25, size=None)
        self.beta_actual = np.random.default_rng().normal(self.beta, 0.25, size=None)
        self.t_start_actual = np.random.default_rng().normal(self.t_start, 2.5, size = None)
        self.t_end_actual = np.random.default_rng().normal(self.t_end, 24, size = None)
        
        self.t_actual = np.linspace(0, self.t_end_actual, 100)
        if self.t_actual[-1] > self.t[-1]:
            self.ax.set_xlim(self.t_actual[0], self.t_actual[-1])
        y_actual = bt.pdf(self.t_actual, self.alpha_actual, self.beta_actual, self.t_start_actual, self.t_end_actual)
        self.y_actual = bt.pdf(self.t_actual, self.alpha_actual, self.beta_actual, self.t_start_actual, self.t_end_actual)/max(y_actual)
        self.ax.plot(self.t_actual, self.y_actual, 'b--', lw=5, alpha = 0.6, label = 'actual utility (beta pdf tweak)')
        self.ax.plot(self.t_actual, bt.pdf(self.t_actual, self.alpha_actual, self.beta_actual, self.t_start_actual, self.t_end_actual)/max(y_actual), 'k--', lw=2, label = 'actual utility (frozen pdf tweak)')
        self.ax.legend(loc='best', frameon=False)
        plt.xlabel('Time Since Tasking Window Opened [hrs]', fontsize=12)
        plt.ylabel('Normalized Science Utility', fontsize=12)
        plt.show()
        return self.alpha_actual, self.beta_actual, self.t_start_actual, self.t_end_actual
    
# name guard used to ensure script only executes if it is run as the __main__
if __name__ == "__main__":
    alpha_predict = 2 # First parameter defining beta distribution
    beta_predict =  6.5 # Second parameter defining beta distribution
    t_start_predict = 5 # Offset delay from t = 0
    t_end_predict = 72 # Defines upper bound of x-axis (time)
    
    NewBeta = BetaGen(alpha_predict, beta_predict, t_start_predict, t_end_predict)
    alpha_actual, beta_actual, t_start_actual, t_end_actual = NewBeta.tweak()