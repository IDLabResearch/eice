'''
Created on 25-mei-2012

@author: ldevocht
'''
#import queue
#from threading import Thread
import multiprocessing
from multiprocessing import JoinableQueue

NUM_OF_THREADS = 24

class Worker:
    def __init__(self):
        self.q = dict()
        
    def functionWorker(self, func):
        while True:
            items = self.q[func].get()
            f = items[0]
            argument = items[1]
            if not argument == None:
                #argument[-1] = f(*argument[:-1])
                #print (str(len(argument)))
                f(*argument)
            else:
                f()
            self.q[func].task_done()
    
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
            self.q[function] = JoinableQueue()
    
    def startQueue(self, function, num_of_threads=NUM_OF_THREADS):
        self.createQueue(function)
        for i in range(num_of_threads):
            t = multiprocessing.Process(target=self.functionWorker, args=([function]))
            t.daemon = True
            t.start()