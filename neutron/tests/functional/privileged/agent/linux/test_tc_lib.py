# Copyright 2018 Red Hat, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_utils import uuidutils
from pyroute2.netlink import rtnl

from neutron.agent.linux import tc_lib
from neutron.privileged.agent.linux import ip_lib as priv_ip_lib
from neutron.privileged.agent.linux import tc_lib as priv_tc_lib
from neutron.tests.functional import base as functional_base


class TcQdiscTestCase(functional_base.BaseSudoTestCase):

    def setUp(self):
        super(TcQdiscTestCase, self).setUp()
        self.namespace = 'ns_test-' + uuidutils.generate_uuid()
        priv_ip_lib.create_netns(self.namespace)
        self.addCleanup(self._remove_ns, self.namespace)
        self.device = 'int_dummy'
        priv_ip_lib.create_interface(self.device, self.namespace, 'dummy')

    def _remove_ns(self, namespace):
        priv_ip_lib.remove_netns(namespace)

    def test_add_tc_qdisc_htb(self):
        priv_tc_lib.add_tc_qdisc(
            self.device, parent=rtnl.TC_H_ROOT, kind='htb', handle='5:',
            namespace=self.namespace)
        qdiscs = priv_tc_lib.list_tc_qdiscs(self.device,
                                            namespace=self.namespace)
        self.assertEqual(1, len(qdiscs))
        self.assertEqual(rtnl.TC_H_ROOT, qdiscs[0]['parent'])
        self.assertEqual(0x50000, qdiscs[0]['handle'])
        self.assertEqual('htb', tc_lib._get_attr(qdiscs[0], 'TCA_KIND'))

    def test_add_tc_qdisc_htb_no_handle(self):
        priv_tc_lib.add_tc_qdisc(
            self.device, parent=rtnl.TC_H_ROOT, kind='htb',
            namespace=self.namespace)
        qdiscs = priv_tc_lib.list_tc_qdiscs(self.device,
                                            namespace=self.namespace)
        self.assertEqual(1, len(qdiscs))
        self.assertEqual(rtnl.TC_H_ROOT, qdiscs[0]['parent'])
        self.assertEqual(0, qdiscs[0]['handle'] & 0xFFFF)
        self.assertEqual('htb', tc_lib._get_attr(qdiscs[0], 'TCA_KIND'))

    def test_add_tc_qdisc_tbf(self):
        burst = 192000
        rate = 320000
        latency = 50000
        priv_tc_lib.add_tc_qdisc(
            self.device, parent=rtnl.TC_H_ROOT, kind='tbf', burst=burst,
            rate=rate, latency=latency, namespace=self.namespace)
        qdiscs = priv_tc_lib.list_tc_qdiscs(self.device,
                                            namespace=self.namespace)
        self.assertEqual(1, len(qdiscs))
        self.assertEqual(rtnl.TC_H_ROOT, qdiscs[0]['parent'])
        self.assertEqual('tbf', tc_lib._get_attr(qdiscs[0], 'TCA_KIND'))
        tca_options = tc_lib._get_attr(qdiscs[0], 'TCA_OPTIONS')
        tca_tbf_parms = tc_lib._get_attr(tca_options, 'TCA_TBF_PARMS')
        self.assertEqual(rate, tca_tbf_parms['rate'])
        self.assertEqual(burst, tc_lib._calc_burst(tca_tbf_parms['rate'],
                                                   tca_tbf_parms['buffer']))
        self.assertEqual(latency, tc_lib._calc_latency_ms(
            tca_tbf_parms['limit'], burst, tca_tbf_parms['rate']) * 1000)

    def test_add_tc_qdisc_ingress(self):
        priv_tc_lib.add_tc_qdisc(self.device, kind='ingress',
                                 namespace=self.namespace)
        qdiscs = priv_tc_lib.list_tc_qdiscs(self.device,
                                            namespace=self.namespace)
        self.assertEqual(1, len(qdiscs))
        self.assertEqual('ingress', tc_lib._get_attr(qdiscs[0], 'TCA_KIND'))
        self.assertEqual(rtnl.TC_H_INGRESS, qdiscs[0]['parent'])
        self.assertEqual(0xffff0000, qdiscs[0]['handle'])