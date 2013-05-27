'''
Created on 25-mei-2012

@author: ldevocht
'''
import gevent
from gevent import monkey
from gevent import Greenlet
from gevent.pool import Pool
from gevent import queue

monkey.patch_socket()
#monkey.patch_thread()

NUM_OF_THREADS = 24

class Worker:
    def __init__(self):
        self.q = dict()
    
    def startFunctionWorker(self):
        self.startQueue(num_of_threads=NUM_OF_THREADS)
        
    def queueFunction(self, function, argument=None):
        if not argument == None:
            thread = gevent.spawn(function, *argument)
        else:
            thread = gevent.spawn(function)
        self.getQueue(function).add(thread)
    
    def waitforFunctionsFinish(self, function):
        try:
            gevent.joinall(self.getQueue(function))
            del self.q[function]
        except:
            pass
    
    def getQueue(self, function):
        return self.q[function]
    
    def createQueue(self, function):
        if not function in self.q:
            self.q[function] = set()
    
    def startQueue(self, function, num_of_threads=NUM_OF_THREADS):
        self.createQueue(function)