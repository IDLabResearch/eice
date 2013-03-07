'''
Created on 25-mei-2012

@author: ldevocht
'''
import gevent
from gevent import monkey
from gevent import Greenlet
from gevent.pool import Pool
from gevent import queue

monkey.patch_thread()
monkey.patch_socket()

NUM_OF_THREADS = 24

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
    
    def startFunctionWorker(self):
        self.startQueue(num_of_threads=NUM_OF_THREADS)
        
    def queueFunction(self, function, argument=None):
        items = [function, argument]
        self.getQueue(function).put(items)
    
    def waitforFunctionsFinish(self, function):
        try:
            self.getQueue(function).join()
        except:
            pass
    
    def getQueue(self, function):
        return self.q[function]
    
    def createQueue(self, function):
        if not function in self.q:
            self.q[function] = gevent.queue.JoinableQueue()
    
    def startQueue(self, function, num_of_threads=NUM_OF_THREADS):
        self.createQueue(function)
        for i in range(num_of_threads):
            gevent.spawn(self.functionWorker, function)
            
print ('Hello')