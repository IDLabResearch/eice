'''
Created on 25-mei-2012

@author: ldevocht
'''
import queue
from threading import Thread

q = dict()

NUM_OF_THREADS = 64

def functionWorker():
    q = getQueue(functionWorker)
    while True:
        items = q.get()
        f = items[0]
        argument = items[1]
        if not argument == None:
            f(argument)
        else:
            f()
        q.task_done()

def startFunctionWorker():
    startQueue(functionWorker, NUM_OF_THREADS)
    
def queueFunction(function, argument=None):
    items = [function, argument]
    getQueue(functionWorker).put(items)

def waitforFunctionsFinish():
    try:
        getQueue(functionWorker).join()
    except:
        pass

def getQueue(function):
    return q[function]

def createQueue(function):
    if not function in q:
        q[function] = queue.Queue()

def startQueue(function, num_of_threads=NUM_OF_THREADS):
    createQueue(function)
    for i in range(num_of_threads):
        t = Thread(target=function)
        t.daemon = True
        t.start()