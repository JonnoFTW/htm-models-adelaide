import multiprocessing


class Worker(multiprocessing.Process):
    def __init__(self, queue_in, queue_out):
        super(Worker, self).__init__()
        self.queue_in = queue_in
        self.queue_out = queue_out
        print "Made", self.name

    def run(self):
        val = self.queue_in.get_nowait()
        print "Running", self.name, "with val", val, "pid", self.pid
        self.queue_out.put(val*5)

if __name__ == "__main__":
    queue_out = multiprocessing.JoinableQueue()
    print "Main process id", multiprocessing.current_process().pid
    procs = []
    for i in xrange(0, 2):
        queue_in = multiprocessing.Queue()
        queue_in.put(i)
        queue_in.put(i*100)
        proc = Worker(queue_in, queue_out)
        procs.append({'q': queue_in, 'p': proc, 'i': i})
        proc.start()
   # for i in range(2):
   #  for j in procs:
   #      j['p'].join()
   #      j['p'].join()
    print "Results are:",
    for j in iter(queue_out.get, 'STOP'):
        print j,
    print

    print "done"