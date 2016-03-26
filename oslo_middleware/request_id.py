# Copyright (c) 2013 NEC Corporation
# All Rights Reserved.
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

from oslo_context import context
import webob.dec

from oslo_config import cfg
from oslo_log import log
from oslo_middleware import base
from metricgenerator.logger import Logger as metricLogger

ENV_REQUEST_ID = 'openstack.request_id'
HTTP_RESP_HEADER_REQUEST_ID = 'Request-Id'

ec2_opts = [
    cfg.StrOpt('monitoring_config',
               default='/tmp/config.cfg',
               help='Config for details on emitting metrics')
]

CONF = cfg.CONF
CONF.register_opts(ec2_opts)

metricLog = metricLogger("iam-api", CONF.monitoring_config)

class RequestId(base.Middleware):
    """Middleware that ensures request ID.

    It ensures to assign request ID for each API request and set it to
    request environment. The request ID is also added to API response.
    """
    @webob.dec.wsgify
    def __call__(self, req):
        req_id = context.generate_request_id()
        metricLog.startTime()
        if (req.headers.get('Request-Id') != None) and\
        (req.path == '/v3/token-auth' or\
        req.path == '/v3/sign-auth' or\
        req.path == '/v3/ec2-auth' or\
        req.path == '/v3/token-auth-ex' or\
        req.path == '/v3/sign-auth-ex' or\
        req.path == '/v3/ec2-auth-ex' or\
        req.path == '/token-auth' or\
        req.path == '/sign-auth' or\
        req.path == '/ec2-auth' or\
        req.path == '/token-auth-ex' or\
        req.path == '/sign-auth-ex' or\
        req.path == '/ec2-auth-ex'):
            req_id = req.headers.get('Request-Id')
        actionName = ""
        if req.path == '/':
            query = req.query_string
            try:
                d = dict([x.split("=") for x in query.split("&")])
                actionName = d['Action']
            except:
                actionName = req.path.split('/')[-1]
        else:
            actionName = req.path.split('/')[-1]
        req.environ[ENV_REQUEST_ID] = req_id
        appendRequestDict = {'requestid' : req_id}
        response = req.get_response(self.application)
        metricLog.reportTime(actionName, addOnInfoPairs = appendRequestDict)
        if HTTP_RESP_HEADER_REQUEST_ID not in response.headers:
            response.headers.add(HTTP_RESP_HEADER_REQUEST_ID, req_id)
        return response
