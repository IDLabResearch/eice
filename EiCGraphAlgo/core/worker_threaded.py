'''
Created on 25-mei-2012

@author: ldevocht
'''
import queue
from threading import Thread
import logging

logger = logging.getLogger('worker')

NUM_OF_THREADS = 64

class Worker:
    def __init__(self):
        self.q = dict()
        
    def functionWorker(self, function):
        while True:
            items = self.q[function].get()
            f = items[0]
            argument = items[1]
            #if 'resourceFetcher' in str(function):
            #    print ('RF')
            if not argument == None:
                #argument[-1] = f(*argument[:-1])
                f(*argument)
            else:
                f()
            self.q[function].task_done()
            
    def startFunctionWorker(self, function):
        self.startQueue(function, NUM_OF_THREADS)
        
    def queueFunction(self, function, argument=None):
        items = [function, argument]
        self.getQueue(function).put(items)
    
    def waitforFunctionsFinish(self, function):
        try:
            self.getQueue(function).join()
            del self.q[function]
        except:
            logger.warning('No functions to wait for')
    
    def getQueue(self, function):
        if not function in self.q:
            self.createQueue(function)
        return self.q[function]
    
    def createQueue(self, function):
        if not function in self.q:
            self.q[function] = queue.Queue()
    
    def startQueue(self, function, num_of_threads=NUM_OF_THREADS):
        self.createQueue(function)
        for i in range(num_of_threads):
            t = Thread(target=self.functionWorker, args=([function]))
            t.daemon = True
            t.start()
   
    def joinAll(self):
        for function in self.q:
            self.getQueue(function).join()