
from os import path
import json
import csv
import io
import logging

from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext
from cloudshell.traffic.tg_helper import (get_reservation_resources, get_address, is_blocking, attach_stats_csv,
                                          get_family_attribute)

from avalanche.avl_app import init_avl
from avalanche.avl_statistics_view import AvlStats


class AvlHandler(object):

    def initialize(self, context, logger):

        self.logger = logger
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger().addHandler(logging.FileHandler(self.logger.handlers[0].baseFilename))

        client_install_path = context.resource.attributes['Client Install Path']
        tcllib_install_path = path.dirname(context.resource.attributes['Tcllib Install Path'])
        self.avl = init_avl(self.logger, tcl_lib_install_dir=tcllib_install_path, avl_install_dir=client_install_path)
        self.avl.connect()

    def tearDown(self):
        self.avl.disconnect()

    def load_config(self, context, avl_config_file_name, avl_test_name):

        self.avl.load_config(avl_config_file_name)
        if avl_test_name:
            self.test = self.avl.project.tests[avl_test_name]
        else:
            self.test = self.avl.project.tests.values()[0]

        reservation_id = context.reservation.reservation_id
        my_api = CloudShellSessionContext(context).get_api()

        reservation_ports = {}
        reservation_ports['client'] = {}
        reservation_ports['server'] = {}
        for port in get_reservation_resources(my_api, reservation_id,
                                              'Generic Traffic Generator Port',
                                              'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                              'STC Chassis Shell 2G.GenericTrafficGeneratorPort'):
            side, index = get_family_attribute(my_api, port, 'Logical Name').Value.strip().split(' ')
            reservation_ports[side.lower()][int(index)] = port

        locations = []
        for index, association in self.test.client.associations.items():
            if index in reservation_ports['client']:
                address = get_address(reservation_ports['client'][index])
                self.logger.debug('client association {} will be reserved on Physical location {}'.
                                  format(index, address))
                locations.append(address)
                association.interface.set_port(address)
            else:
                self._association_not_found('client', index, reservation_ports['client'])

        for index, association in self.test.server.associations.items():
            if index in reservation_ports['server']:
                address = get_address(reservation_ports['server'][index])
                self.logger.debug('server association {} will be reserved on Physical location {}'.
                                  format(index, address))
                locations.append(address)
                association.interface.set_port(address)
            else:
                self._association_not_found('server', index, reservation_ports['server'])

        self._reserve_ports(*locations)
        self.logger.info('Port Reservation Completed')

    def _association_not_found(self, side, port, reservation_ports):
        message = '{} association {} not found in reservation ports {}'.format(side, port, reservation_ports.keys())
        self.logger.error(message)
        raise Exception(message)

    def _reserve_ports(self, *locations):
        chassis_list = []
        for location in locations:
            ip, module, port = location.split('/')
            chassis = self.avl.hw.get_chassis(ip)
            if chassis not in chassis_list:
                chassis.get_inventory()
                chassis_list.append(chassis)
            chassis.modules[int(module)].ports[int(port)].reserve()

    def start_test(self, blocking):
        self.test.start(blocking=is_blocking(blocking), trial=True)

    def stop_test(self):
        self.test.stop()

    def get_statistics(self, context, view_name, output_type):

        side, results = view_name.split()
        stats_obj = AvlStats(self.avl.project, side, results)
        stats_obj.read_stats()
        statistics = stats_obj.statistics

        if output_type.strip().lower() == 'json':
            statistics_str = json.dumps(statistics, indent=4, sort_keys=True, ensure_ascii=False)
            return json.loads(statistics_str)
        elif output_type.strip().lower() == 'csv':
            captions = ['timestamp'] + statistics['0'].keys()
            output = io.BytesIO()
            w = csv.DictWriter(output, captions)
            w.writeheader()
            for timestamp, stats in statistics.items():
                stats.update({'timestamp': timestamp})
                w.writerow(stats)
            attach_stats_csv(context, self.logger, view_name, output.getvalue().strip())
            return output.getvalue().strip()
        else:
            raise Exception('Output type should be CSV/JSON - got "{}"'.format(output_type))

    def get_project_ref(self):
        return self.avl.project.ref

    def get_children(self, obj_ref, child_type):
        return self.avl.api.get(obj_ref, child_type).split()

    def get_attributes(self, obj_ref):
        return self.avl.api.get(obj_ref)

    def set_attribute(self, obj_ref, attr_name, attr_value):
        return self.avl.api.config(obj_ref, **{attr_name: attr_value})

    def perform_command(self, command, **parameters):
        return self.avl.api.perform(command, **parameters)
