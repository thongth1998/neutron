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

# rule types are so different from other objects that we don't base the test
# class on the common base class for all objects

from unittest import mock

from neutron_lib import constants as lib_consts
from neutron_lib.db import constants as db_consts
from neutron_lib.services.qos import constants as qos_consts
from oslo_config import cfg

from neutron import manager
from neutron.objects.qos import rule_type
from neutron.services.qos import qos_plugin
from neutron.tests import base as test_base


DB_PLUGIN_KLASS = 'neutron.db.db_base_plugin_v2.NeutronDbPluginV2'

DRIVER_SUPPORTED_PARAMETERS = [
    {
        'parameter_name': qos_consts.MAX_KBPS,
        'parameter_type': lib_consts.VALUES_TYPE_RANGE,
        'parameter_values': {"start": 0, "end": db_consts.DB_INTEGER_MAX_VALUE}
    }, {
        'parameter_name': qos_consts.MAX_BURST,
        'parameter_type': lib_consts.VALUES_TYPE_RANGE,
        'parameter_values': {"start": 0, "end": db_consts.DB_INTEGER_MAX_VALUE}
    }, {
        'parameter_name': qos_consts.DIRECTION,
        'parameter_type': lib_consts.VALUES_TYPE_CHOICES,
        'parameter_values': lib_consts.VALID_DIRECTIONS
    }
]


class QosRuleTypeObjectTestCase(test_base.BaseTestCase):

    def setUp(self):
        super().setUp()
        self.config_parse()

        self.setup_coreplugin(load_plugins=False)
        cfg.CONF.set_override("core_plugin", DB_PLUGIN_KLASS)
        cfg.CONF.set_override("service_plugins", ["qos"])
        manager.init()

    def test_get_object(self):
        driver_details = {
            'name': "backend_driver",
            'supported_parameters': DRIVER_SUPPORTED_PARAMETERS
        }
        with mock.patch.object(
            qos_plugin.QoSPlugin, 'supported_rule_type_details',
            return_value=[driver_details]
        ):
            rule_type_details = rule_type.QosRuleType.get_object(
                qos_consts.RULE_TYPE_BANDWIDTH_LIMIT)
            self.assertEqual(
                driver_details['name'], rule_type_details.drivers[0].name)
            self.assertEqual(
                driver_details['supported_parameters'],
                rule_type_details.drivers[0].supported_parameters)
            self.assertEqual(1, len(rule_type_details.drivers))
            self.assertEqual(
                qos_consts.RULE_TYPE_BANDWIDTH_LIMIT, rule_type_details.type)

    def test_get_objects(self):
        with mock.patch.object(qos_plugin.QoSPlugin, 'supported_rule_types',
                               return_value=set(qos_consts.VALID_RULE_TYPES)):
            types = rule_type.QosRuleType.get_objects()
            self.assertEqual(sorted(qos_consts.VALID_RULE_TYPES),
                             sorted(type_['type'] for type_ in types))

    def test_wrong_type(self):
        self.assertRaises(ValueError, rule_type.QosRuleType, type='bad_type')
