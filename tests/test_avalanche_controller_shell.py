#!/usr/bin/python
# -*- coding: utf-8 -*-

from os import path
import time
import json

from cloudshell.api.cloudshell_api import AttributeNameValue, InputNameValue
from cloudshell.traffic.tg_helper import get_reservation_resources, set_family_attribute
from shellfoundry.releasetools.test_helper import create_session_from_cloudshell_config, create_command_context

avalanche_install_path = 'C:/Program Files (x86)/Spirent Communications/Spirent TestCenter 4.84'
tcllib_install_path = 'E:/Tcl/Tcl8532/lib/Tcllib1.16'

ports = ['swisscom/Module1/PG1/Port1', 'swisscom/Module1/PG1/Port2']
attributes = [AttributeNameValue('Client Install Path', avalanche_install_path),
              AttributeNameValue('Tcllib Install Path', tcllib_install_path)]


class TestAvalancheControllerShell(object):

    def setup(self):
        self.session = create_session_from_cloudshell_config()
        self.context = create_command_context(self.session, ports, 'Avalanche Controller', attributes)

    def teardown(self):
        reservation_id = self.context.reservation.reservation_id
        self.session.EndReservation(reservation_id)
        while self.session.GetReservationDetails(reservation_id).ReservationDescription.Status != 'Completed':
            time.sleep(1)
        self.session.DeleteReservation(reservation_id)

    def test_load_config(self):
        self._load_config(path.join(path.dirname(__file__), 'test_config.spf'))

    def test_get_set(self):
        self.test_load_config()
        project_ref = self.session.ExecuteCommand(self.context.reservation.reservation_id, 'Avalanche Controller',
                                                  'Service', 'get_project_id').Output
        print('project_ref = {}'.format(project_ref))
        tests = self.session.ExecuteCommand(self.context.reservation.reservation_id, 'Avalanche Controller',
                                            'Service', 'get_children',
                                            [InputNameValue('obj_ref', project_ref),
                                             InputNameValue('child_type', 'tests')]).Output
        print tests
        print('tests = {}'.format(json.loads(tests)))
        project_attrs = self.session.ExecuteCommand(self.context.reservation.reservation_id, 'Avalanche Controller',
                                                    'Service', 'get_attributes',
                                                    [InputNameValue('obj_ref', project_ref)]).Output
        print('project attributes = {}'.format(json.loads(project_attrs)))
        print('project name = {}'.format(json.loads(project_attrs)['name']))
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'Avalanche Controller',
                                    'Service', 'set_attribute',
                                    [InputNameValue('obj_ref', project_ref),
                                     InputNameValue('attr_name', 'name'),
                                     InputNameValue('attr_value', 'Newname')])

    def test_run_traffic(self):
        self._load_config(path.join(path.dirname(__file__), 'test_config.spf'))
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'Avalanche Controller', 'Service',
                                    'send_arp')
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'Avalanche Controller', 'Service',
                                    'start_devices')
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'Avalanche Controller', 'Service',
                                    'start_traffic', [InputNameValue('blocking', 'True')])
        stats = self.session.ExecuteCommand(self.context.reservation.reservation_id,
                                            'Avalanche Controller', 'Service', 'get_statistics',
                                            [InputNameValue('view_name', 'generatorportresults'),
                                             InputNameValue('output_type', 'JSON')])
        assert(int(json.loads(stats.Output)['Port 1']['TotalFrameCount']) == 4000)

    def _load_config(self, config):
        reservation_ports = get_reservation_resources(self.session, self.context.reservation.reservation_id,
                                                      'Generic Traffic Generator Port',
                                                      'STC Chassis Shell 2G.GenericTrafficGeneratorPort')
        set_family_attribute(self.session, reservation_ports[0], 'Logical Name', 'Client 1')
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Server 1')
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'Avalanche Controller', 'Service',
                                    'load_config', [InputNameValue('avl_config_file_name', config)])
