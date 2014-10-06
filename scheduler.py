import random
import sys
import mesos.native
import mesos.interface
from mesos.interface import mesos_pb2

from relay import log


# TODO: remove this
TOTAL_TASKS = 10


def create_task(tid, offer, executor, resources={}):
    """
    `tid` (str) task id
    `offer` a mesos Offer instance
    `executor` a mesos Executor instance
    `resources` the stuff this task consumes:
        {"cpus": 10,
            "mem": 1,
            "disk": 12,
            "ports": [(20, 34), (35, 35)],
            "disks": ["sda1"]}
    """
    task = mesos_pb2.TaskInfo()
    task.task_id.value = tid
    task.slave_id.value = offer.slave_id.value
    task.name = "task %s" % tid
    task.executor.MergeFrom(executor)

    scalar_keys = ['cpus', 'mem', 'disk']
    range_keys = ['ports']
    set_keys = ['disks']

    for key in set(scalar_keys).intersection(resources):
        resource = task.resources.add()
        resource.name = key
        resource.type = mesos_pb2.Value.SCALAR
        resource.scalar.value = resources[key]

    for key in set(range_keys).intersection(resources):
        resource = task.resources.add()
        resource.name = key
        resource.type = mesos_pb2.Value.RANGES
        for range_data in resources[key]:
            inst = resource.ranges.range.add()
            inst.begin = range_data[0]
            inst.end = range_data[1]

    for key in set(set_keys).intersection(resources):
        resource = task.resources.add()
        resource.name = key
        resource.type = mesos_pb2.Value.SET
        for elem in resources[key]:
            resource.set.item.append(elem)

    return task


class Scheduler(mesos.interface.Scheduler):
    def __init__(self, executor):
        self.executor = executor
        # self.taskData = {}
        # self.tasksLaunched = 0
        # self.tasksFinished = 0
        # self.messagesSent = 0
        # self.messagesReceived = 0

    def registered(self, driver, frameworkId, masterInfo):
        """
        Invoked when the scheduler re-registers with a newly elected Mesos
        master.  This is only called when the scheduler has previously been
        registered.

        MasterInfo containing the updated information about the elected master
        is provided as an argument.
        """
        log.info(
            "Registered with framework", extra=dict(framework_id=frameworkId))

    def resourceOffers(self, driver, offers):
        """
        Invoked when resources have been offered to this framework. A single
        offer will only contain resources from a single slave.  Resources
        associated with an offer will not be re-offered to _this_ framework
        until either (a) this framework has rejected those resources (see
        SchedulerDriver.launchTasks) or (b) those resources have been
        rescinded (see Scheduler.offerRescinded).  Note that resources may be
        concurrently offered to more than one framework at a time (depending
        on the allocator being used).  In that case, the first framework to
        launch tasks using those resources will be able to use them while the
        other frameworks will have those resources rescinded (or if a
        framework has already launched tasks with those resources then those
        tasks will fail with a TASK_LOST status and a message saying as much).
        """
        log.debug("Got resource offers", extra=dict(num_offers=len(offers)))
        if True:  # TODO: get metric data vs num running tasks
            return

        for offer in offers:
            tasks = []
            log.debug(
                "Considering a resource offer",
                extra=dict(offer_id=offer.id.value))
            tid = str(random.randint(1, sys.maxint))

            log.debug(
                "Accepting offer to start a task",
                extra=dict(offer_host=offer.hostname, task_id=tid))

            task = create_task(tid, offer, self.executor)
            tasks.append(task)

            # TODO: what's this for?
            self.taskData[task.task_id.value] = (
                offer.slave_id, task.executor.executor_id)
        driver.launchTasks(offer.id, tasks)

    def statusUpdate(self, driver, update):
        # TODO: continue from here
        print "Task %s is in state %d" % (update.task_id.value, update.state)

        # Ensure the binary data came through.
        if update.data != "data with a \0 byte":
            print "The update data did not match!"
            print "  Expected: 'data with a \\x00 byte'"
            print "  Actual:  ", repr(str(update.data))
            sys.exit(1)

        if update.state == mesos_pb2.TASK_FINISHED:
            self.tasksFinished += 1
            if self.tasksFinished == TOTAL_TASKS:
                print "All tasks done, waiting for final framework message"

            slave_id, executor_id = self.taskData[update.task_id.value]

            self.messagesSent += 1
            driver.sendFrameworkMessage(
                executor_id,
                slave_id,
                'data with a \0 byte')

    def frameworkMessage(self, driver, executorId, slaveId, message):
        self.messagesReceived += 1

        # The message bounced back as expected.
        if message != "data with a \0 byte":
            print "The returned message data did not match!"
            print "  Expected: 'data with a \\x00 byte'"
            print "  Actual:  ", repr(str(message))
            sys.exit(1)
        print "Received message:", repr(str(message))

        if self.messagesReceived == TOTAL_TASKS:
            if self.messagesReceived != self.messagesSent:
                print "Sent", self.messagesSent,
                print "but received", self.messagesReceived
                sys.exit(1)
            print "All tasks done, and all messages received, exiting"
            driver.stop()
