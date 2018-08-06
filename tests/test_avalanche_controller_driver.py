#!/usr/bin/python
# -*- coding: utf-8 -*-

from os import path
import sys
import unittest
import logging
import json
import time

from cloudshell.traffic.tg_helper import get_reservation_resources, set_family_attribute
from shellfoundry.releasetools.test_helper import create_session_from_cloudshell_config, create_command_context

from src.driver import AvalancheControllerDriver

avalanche_install_path = 'C:/Program Files (x86)/Spirent Communications/Spirent TestCenter 4.69'
tcllib_install_path = 'C:/CS-Yoram/Tcl/lib/Tcllib1.16'

ports = ['yoram-av-as-stc/Module1/PG1/Port1', 'yoram-av-as-stc/Module1/PG1/Port2']
attributes = {'Client Install Path': avalanche_install_path,
              'Tcllib Install Path': tcllib_install_path}


class TestAvalancheControllerDriver(unittest.TestCase):

    def setUp(self):
        self.session = create_session_from_cloudshell_config()
        self.context = create_command_context(self.session, ports, 'Avalanche Controller', attributes)
        self.driver = AvalancheControllerDriver()
        self.driver.initialize(self.context)
        print self.driver.logger.handlers[0].baseFilename
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger().addHandler(logging.FileHandler(self.driver.logger.handlers[0].baseFilename))

    def tearDown(self):
        self.driver.cleanup()
        self.session.EndReservation(self.context.reservation.reservation_id)

    def test_init(self):
        pass

    def test_get_set(self):
        print('session_id = {}'.format(self.driver.get_session_id(self.context)))
        project = self.driver.get_children(self.context, 'system1', 'project')[0]
        print('project = {}'.format(project))
        print('all children = {}'.format(self.driver.get_children(self.context, 'system1')))

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

    def negative_tests(self):
        reservation_ports = get_reservation_resources(self.session, self.context.reservation.reservation_id,
                                                      'Generic Traffic Generator Port',
                                                      'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                      'STC Chassis Shell 2G.GenericTrafficGeneratorPort')
        assert(len(reservation_ports) == 2)
        set_family_attribute(self.session, reservation_ports[0], 'Logical Name', 'Port 1')
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', '')
        self.assertRaises(Exception, self.driver.load_config, self.context,
                          path.join(path.dirname(__file__), 'test_config.spf'))
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Port 1')
        self.assertRaises(Exception, self.driver.load_config, self.context,
                          path.join(path.dirname(__file__), 'test_config.spf'))
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Port x')
        self.assertRaises(Exception, self.driver.load_config, self.context,
                          path.join(path.dirname(__file__), 'test_config.spf'))
        # cleanup
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Port 2')


if __name__ == '__main__':
    sys.exit(unittest.main())
