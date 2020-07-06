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

    # Trying to extract the following line in the rendered html:
    # server_ip: "{{server_ip}}"
    # See https://github.com/lelandpaul/virtual-ringing-room/blob/
    #     ec00927ca57ab94fa2ff6a978ffaff707ab23a57/app/templates/ringing_room.html#L46
    url = urllib.parse.urljoin(http_server_url, str(tower_id))
    html = requests.get(url).text

    url_start_index = html.index("server_ip") + len('server_ip: "')
    string_that_starts_with_url = html[url_start_index:]
    load_balancing_url = string_that_starts_with_url[:string_that_starts_with_url.index('"')]

    return load_balancing_url
