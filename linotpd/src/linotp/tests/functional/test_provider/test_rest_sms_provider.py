# -*- coding: utf-8 -*-
#
#    LinOTP - the open source solution for two factor authentication
#    Copyright (C) 2010 - 2018 KeyIdentity GmbH
#
#    This file is part of LinOTP server.
#
#    This program is free software: you can redistribute it and/or
#    modify it under the terms of the GNU Affero General Public
#    License, version 3, as published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the
#               GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#    E-mail: linotp@keyidentity.com
#    Contact: www.linotp.org
#    Support: www.keyidentity.com
#


"""
Test REST Sms Gateway

These tests will only pass if you start a LinOTP server on 127.0.0.1.
For example with paster:

    paster serve test.ini

We assume port 5001 is used (default). If you want to use another port you can
specify it with nose-testconfig (e.g. --tc=paster.port:5005).
"""


import logging
import urlparse
import requests

from mock import patch

from linotp.tests.functional_special import TestSpecialController

import linotp.provider.smsprovider.RestSMSProvider

# mocking hook is startting here
HTTP_RESPONSE_FUNC = None
HTTP_RESPONSE = None


def mocked_http_request(HttpObject, *argparams, **kwparams):

    class Response:
        pass

    r = Response()

    request_url = argparams[0]
    request_body = kwparams['json']

    r.status = 200
    r.text = ""  # rest does not return a body

    if r.status == 200:
        r.ok = True
        r.content = ""
        return r

    return r


import json

log = logging.getLogger(__name__)


class TestRestSmsController(TestSpecialController):
    '''
    Here the HTTP SMS Gateway functionality is tested.
    '''

    def setUp(self):
        '''
        This sets up all the resolvers and realms
        '''
        TestSpecialController.setUp(self)

        self.create_common_resolvers()
        self.create_common_realms()

    def tearDown(self):
        self.delete_all_policies()
        self.delete_all_token()
        self.delete_all_realms()
        self.delete_all_resolvers()

        TestSpecialController.tearDown(self)

###############################################################################

    @patch('requests.Session.post', mocked_http_request)
    def test_succesful_auth(self):
        '''
        Successful SMS sending (via smspin) and authentication
        '''
        sms_url = 'http://myfake.com/'

        sms_conf = {"URL": sms_url,
                    'PAYLOAD': {
                        'text': 'my <message> to you',
                        'destination': ''
                        },
                    "PASSWORD": "v3ry53cr3t",
                    'USERNAME': 'heinz',
                    "SMS_TEXT_KEY": "text",
                    "SMS_PHONENUMBER_KEY": "destination",
                    "RETURN_SUCCESS": "ID"
                    }


        params = {'name': 'newone',
                  'config': json.dumps(sms_conf),
                  'timeout': '301',
                  'type': 'sms',
                  'class': 'RestSMSProvider'
                  }

        response = self.make_system_request('setProvider', params=params)
        self.assertTrue('"value": true' in response, response)

        # ------------------------------------------------------------------ --

        # next we have to make it the default provider

        params = {'name': 'smsprovider_newone',
                  'scope': 'authentication',
                  'realm': '*',
                  'action': 'sms_provider=newone',
                  'user': '*',
                  }

        response = self.make_system_request(action='setPolicy',
                                            params=params)
        self.assertTrue('false' not in response, response)

        parameters = {'serial': 'SMS_4_REST',
                      'realm': 'myDefRealm',
                      'type': 'sms',
                      'user': 'passthru_user1',
                      'pin': '1234',
                      'phone': '016012345678',
                      }
        response = self.make_admin_request('init', params=parameters)

        self.assertTrue('"value": true' in response, response)

        params = {
            'user': 'passthru_user1',
            'pass': '1234'
        }
        response = self.make_validate_request('check', params=params)

        self.assertTrue('"value": false' in response, response)
        self.assertTrue('transactionid' in response, response)

        return
###eof#########################################################################
