
from avl_handler import AvlHandler

from cloudshell.traffic.driver import TrafficControllerDriver


class AvalancheControllerDriver(TrafficControllerDriver):

    def __init__(self):
        super(self.__class__, self).__init__()
        self.handler = AvlHandler()

    def load_config(self, context, avl_config_file_name):
        """ Load Avalanche configuration file and reserve ports.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param avl_config_file_name: Full path to Avalanache configuration file name - tcc or xml
        """

        super(self.__class__, self).load_config(context)
        self.handler.load_config(context, avl_config_file_name)
        return avl_config_file_name + ' loaded, ports reserved'

    def start_test(self, context, blocking):
        """ Start test.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param blocking: True - return after test finish to run, False - return immediately.
        """

        self.handler.start_test(blocking)
        return 'traffic started in {} mode'.format(blocking)

    def stop_test(self, context):
        """ Stop test.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        self.handler.stop_test()

    def get_statistics(self, context, view_name, output_type):
        """ Get view statistics.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param view_name: client/server http/tcp,  etc.
        :param output_type: CSV or JSON.
        """

        return self.handler.get_statistics(context, view_name, output_type)

    #
    # Parent commands are not visible so we re define them in child.
    #

    def initialize(self, context):
        super(self.__class__, self).initialize(context)

    def cleanup(self):
        super(self.__class__, self).cleanup()

    def keep_alive(self, context, cancellation_context):
        super(self.__class__, self).keep_alive(context, cancellation_context)

    #
    # Hidden commands for developers only.
    #

    def get_project_id(self, context):
        """ Returns project ID.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """

        return self.handler.get_session_id()

    def get_children(self, context, obj_ref, child_type=''):
        """ Returns all children of object.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param obj_ref: valid Avalanche object reference.
        :param child_type: requested children type. If None returns all children.
        :return: list of children.
        """

        return self.handler.get_children(obj_ref, child_type)

    def get_attributes(self, context, obj_ref):
        """ Returns all attributes of object.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param obj_ref: valid Avalanche object reference.
        :return: list of <attribute, value>.
        """

        return self.handler.get_attributes(obj_ref)

    def set_attribute(self, context, obj_ref, attr_name, attr_value):
        """ Set object attribute.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param obj_ref: valid Avalanche object reference.
        :param attr_name: Avalanche attribue name.
        :param attr_value: Avalanche attribue value.
        """

        self.handler.set_attribute(obj_ref, attr_name, attr_value)

    def perform_command(self, context, command, **parameters):
        """ Set object attribute.

        :type context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        :param command: valid Avalanche object reference.
        :param parameters: parameters dict {name: value}.
        """

        return self.handler.perform_command(command, **parameters)
