import sys
import os
from mesos.interface import mesos_pb2
import mesos.native

from relay.scheduler import Scheduler
from relay.relay_logging import configure_logging
configure_logging('relay.runtest')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage: %s master" % sys.argv[0]
        sys.exit(1)

    executor = mesos_pb2.ExecutorInfo()
    executor.executor_id.value = "default"
    executor.command.value = "python -m relay.executor"
    executor.name = "Relay executor"
    executor.source = "relay_test"

    framework = mesos_pb2.FrameworkInfo()
    framework.user = ""  # Have Mesos fill in the current user.
    framework.name = "Relay Test Framework"

    # TODO(vinod): Make checkpointing the default when it is default
    # on the slave.
    if os.getenv("MESOS_CHECKPOINT"):
        print "Enabling checkpoint for the framework"
        framework.checkpoint = True

    if os.getenv("MESOS_AUTHENTICATE"):
        print "Enabling authentication for the framework"

        if not os.getenv("DEFAULT_PRINCIPAL"):
            print "Expecting authentication principal in the environment"
            sys.exit(1)

        if not os.getenv("DEFAULT_SECRET"):
            print "Expecting authentication secret in the environment"
            sys.exit(1)

        credential = mesos_pb2.Credential()
        credential.principal = os.getenv("DEFAULT_PRINCIPAL")
        credential.secret = os.getenv("DEFAULT_SECRET")

        framework.principal = os.getenv("DEFAULT_PRINCIPAL")

        driver = mesos.native.MesosSchedulerDriver(
            Scheduler(executor),
            framework,
            sys.argv[1],
            credential)
    else:
        framework.principal = "relay-test-framework"

        driver = mesos.native.MesosSchedulerDriver(
            Scheduler(executor),
            framework,
            sys.argv[1])

    status = 0 if driver.run() == mesos_pb2.DRIVER_STOPPED else 1

    # Ensure that the driver process terminates.
    driver.stop()

    sys.exit(status)
