# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A module to get an http proxy information."""


import urllib
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
import httplib2


def GetDefaultProxyInfo(method='http'):
  """Get ProxyInfo from environment.

  This function is meant to mimic httplib2.proxy_info_from_environment, but get
  the proxy information from urllib.getproxies instead. urllib can also get
  proxy information from Windows Internet Explorer settings or MacOSX framework
  SystemConfiguration.

  Args:
    method: protocol string
  Returns:
    httplib2 ProxyInfo object or None
  """

  proxy_dict = urllib.getproxies()
  proxy_url = proxy_dict.get(method, None)
  if not proxy_url:
    return None

  pi = httplib2.proxy_info_from_url(proxy_url, method)

  # The ProxyInfo object has a bypass_host method that takes the hostname as an
  # argument and it returns 1 or 0 based on if the hostname should bypass the
  # proxy or not. We could either build the bypassed hosts list and pass it to
  # pi.bypass_hosts, or we can just replace the method with the function in
  # urllib, and completely mimic urllib logic. We do the latter.
  # Since the urllib.proxy_bypass _function_ (no self arg) is not "bound" to the
  # class instance, it doesn't receive the self arg when its called. We don't
  # need to "bind" it via types.MethodType(urllib.proxy_bypass, pi).
  pi.bypass_host = urllib.proxy_bypass

  return pi


def GetHttpProxyInfo():
  """Get ProxyInfo object or callable to be passed to httplib2.Http.

  httplib2.Http can issue requests through a proxy. That information is passed
  via either ProxyInfo objects or a callback function that receives the protocol
  the request is made on and returns the proxy address. If users set the gcloud
  properties, we create a ProxyInfo object with those settings. If users do not
  set gcloud properties, we return a function that can be called to get default
  settings.

  Returns:
    httplib2 ProxyInfo object or callable function that returns a Proxy Info
    object given the protocol (http, https)
  """

  proxy_type_map = config.GetProxyTypeMap()
  proxy_type = properties.VALUES.proxy.proxy_type.Get()
  proxy_address = properties.VALUES.proxy.address.Get()
  proxy_port = properties.VALUES.proxy.port.GetInt()
  proxy_prop_set = len(filter(None, (proxy_type, proxy_address, proxy_port)))
  if proxy_prop_set > 0 and proxy_prop_set != 3:
    raise properties.InvalidValueError(
        'Please set all or none of the following properties: '
        'proxy/type, proxy/address and proxy/port')

  if proxy_prop_set > 0:
    return httplib2.ProxyInfo(
        proxy_type_map[proxy_type],
        proxy_address,
        proxy_port,
        proxy_user=properties.VALUES.proxy.username.Get(),
        proxy_pass=properties.VALUES.proxy.password.Get())

  return GetDefaultProxyInfo