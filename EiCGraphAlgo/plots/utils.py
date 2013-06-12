'''
Created on Mar 12, 2013

@author: ldevocht
'''
import math
import time
import numpy

def average(a, b):
    return (a + b) / 2.0
def improve(guess, x):
    return average(guess, x/guess)
def good_enough(guess, x):
    d = abs(guess*guess - x)
    return (d < 0.001)
def square_root(guess, x):
    while(not good_enough(guess, x)):
        guess = improve(guess, x)
    return guess
def my_sqrt(x):
    r = square_root(1, x)
    return r

def approximate_log(n):
    if n < 1.1:
        return n-1
    else:
        return approximate_log(math.sqrt(n)) + approximate_log(math.sqrt(n))
    
def approximate_log2(n):
    return (n**n - 1.0) / n

def timeit1(arg=approximate_log2):
    s = time.time()
    for i in range(1,75000):
        z=arg(i)
    print ("Took %f seconds" % (time.time() - s))

def timeit2(arg=math.log10):
    s = time.time()
    for i in range(1,75000):
        z=arg(i)
    print ("Took %f seconds" % (time.time() - s))
    
def timeit3(arg=numpy.log10):
    s = time.time()
    for i in range(1,75000):
        z=arg(i)
    print ("Took %f seconds" % (time.time() - s))

timeit1()
timeit2()
timeit3()

print (math.log10(100))
print (approximate_log(100))