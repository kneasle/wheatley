"""
A module to store functions related to parsing the HTML of the Ringing Room tower pages to find
things like the load-balanced URL of the socket-io server.
"""

import urllib

import requests


def get_load_balancing_url(tower_id, http_server_url):
    """
    Get the URL of the socket server which (since the addition of load balancing) is not
    necessarily the same as the URL of the http server that people will put into their browser URL
    bars.
    """

    url = urllib.parse.urljoin(http_server_url, str(tower_id))
    html = requests.get(url).text

    string_that_starts_with_url = html[html.index("server_ip") + len('server_ip: "'):]
    load_balancing_url = string_that_starts_with_url[:string_that_starts_with_url.index('"')]

    return load_balancing_url
