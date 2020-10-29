from multiprocessing import Pool, Manager
from threading import Thread, Lock
from array_tool import queue_sort
import time
from gevent import monkey, pool
from queue import PriorityQueue

class CyclicTask(Thread):
    def __init__(self, task, param, interval):
        super(CyclicTask, self).__init__()
        self.is_running = True
        self.task = task
        self.param = param
        self.interval = interval

    def quit(self):
        self.is_running = False

    def run(self):
        while self.is_running:
            time.sleep(self.interval)
            if (self.param):
                self.task(*self.param)
            else:
                self.task()


def _task(idx, task, params, queue):
    print('task idx=', idx)
    result = task(*params)
    queue.put((idx, result))

class MultiTask:

    def __init__(self, pool_size, queue_size):
        self.pool = Pool(processes=pool_size)
        self.queue = Manager().Queue(maxsize=queue_size)
        self.idx = 0

    def submit(self, task, params):
        '''submit task and params
        '''
        idx = self.idx;
        self.pool.apply_async(_task, args=(idx, task, params, self.queue))
        self.idx += 1

    def subscribe(self):
        '''synchronous subscribe by waiting for the results
        can be called in thread to avoid main thread blocking
        called only once
        :return result, sorted results by the order submitted
        '''

        self.pool.close()
        self.pool.join()
        result = queue_sort(self.queue)
        return result


class WorkerThread(Thread):
    def __init__(self, taskQueue, lock, interval = 0.05):
        Thread.__init__(self)
        self.taskQueue = taskQueue
        self.isRunning = True
        self.lock = lock
        self.interval = interval

    def run(self):
        while True:
            if not self.isRunning:
                break
            time.sleep(self.interval)
            if self.taskQueue.empty():
                continue
            try:
                taskBundle = self.taskQueue.get(False)
            except:
                continue

            if len(taskBundle[2]) <= 0:
                taskBundle[1]()
            else:
                taskBundle[1](**taskBundle[2])

class ThreadPool(Thread):
    def __init__(self, numWorker, interval = 0.05, timeout = 5, queueMax = 100):
        Thread.__init__(self)
        self.taskQueue = PriorityQueue(maxsize=queueMax)

        self.workers = []
        self.lock = Lock()
        self.interval = interval

        for m in range(numWorker):
            self.workers.append(WorkerThread(self.taskQueue, self.lock, self.interval))

    def run(self):
        for worker in self.workers:
            worker.start()
        for worker in self.workers:
            worker.join()

    # release tasks
    def clear_tasks(self):
        self.taskQueue.clear()

    def submit(self, task, kargs, priority = 9):
        self.taskQueue.put( (priority, task, kargs) )
