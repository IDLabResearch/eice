'''
Created on 25-mei-2012

@author: ldevocht
'''
import queue
from threading import Thread

NUM_OF_THREADS = 24

class Worker:
    def __init__(self):
        self.q = dict()
        
    def functionWorker(self):
        while True:
            items = self.q.get()
            f = items[0]
            argument = items[1]
            if not argument == None:
                argument[-1] = f(*argument[:-1])
            else:
                f()
            self.q.task_done()
    
    def startFunctionWorker(self):
        self.startQueue(num_of_threads=NUM_OF_THREADS)
        
    def queueFunction(self, function, argument=None):
        items = [function, argument]
        self.getQueue().put(items)
    
    def waitforFunctionsFinish(self):
        try:
            self.getQueue().join()
        except:
            pass
    
    def getQueue(self, function):
        return self.q[function]
    
    def createQueue(self, function):
        if not function in self.q:
            self.q[function] = queue.Queue()
    
    def startQueue(self, function, num_of_threads=NUM_OF_THREADS):
        self.createQueue(function)
        for i in range(num_of_threads):
            t = Thread(target=function)
            t.daemon = True
            t.start()