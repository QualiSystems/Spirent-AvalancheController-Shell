#!/usr/bin/python
# -*- coding: utf-8 -*-

from os import path
import logging
import json
import time

from cloudshell.traffic.tg_helper import get_reservation_resources, set_family_attribute
from shellfoundry.releasetools.test_helper import create_session_from_cloudshell_config, create_command_context

from src.driver import AvalancheControllerDriver

avalanche_install_path = 'C:/Program Files (x86)/Spirent Communications/Spirent TestCenter 4.84'
tcllib_install_path = 'E:/Tcl/Tcl8532/lib/Tcllib1.16'

ports = ['swisscom/Module1/PG1/Port1', 'swisscom/Module1/PG1/Port2']
attributes = {'Client Install Path': avalanche_install_path,
              'Tcllib Install Path': tcllib_install_path}


class TestAvalancheControllerDriver(object):

    def setup(self):
        self.session = create_session_from_cloudshell_config()
        self.context = create_command_context(self.session, ports, 'Avalanche Controller', attributes)
        self.driver = AvalancheControllerDriver()
        self.driver.initialize(self.context)
        print self.driver.logger.handlers[0].baseFilename
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger().addHandler(logging.FileHandler(self.driver.logger.handlers[0].baseFilename))

    def teardown(self):
        self.driver.cleanup()
        self.session.EndReservation(self.context.reservation.reservation_id)

    def test_init(self):
        pass

    def test_get_set(self):
        self.test_load_config()
        project_ref = self.driver.get_project_id(self.context)
        print('project ref = {}'.format(project_ref))
        tests = self.driver.get_children(self.context, project_ref, 'tests')
        print(tests)
        attributes = self.driver.get_attributes(self.context, project_ref)
        print(attributes)
        print(attributes['name'])
        self.driver.set_attribute(self.context, project_ref, 'name', 'NewName')
        attributes = self.driver.get_attributes(self.context, project_ref)
        print(attributes['name'])

    def test_load_config(self):
        reservation_ports = get_reservation_resources(self.session, self.context.reservation.reservation_id,
                                                      'Generic Traffic Generator Port',
                                                      'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                      'STC Chassis Shell 2G.GenericTrafficGeneratorPort')
        set_family_attribute(self.session, reservation_ports[0], 'Logical Name', 'Client 1')
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Server 1')
        self.driver.load_config(self.context, path.join(path.dirname(__file__), 'test_config.spf'), 'Test')

    def test_run_traffic(self):
        self.test_load_config()
        self.driver.start_test(self.context, 'True')
        time.sleep(4)
        stats = self.driver.get_statistics(self.context, 'client http', 'JSON')
        print(json.dumps(stats, indent=2))
        stats = self.driver.get_statistics(self.context, 'client http', 'CSV')
        print(stats)
