import requests
import json

from time import sleep

with open('spam_generator_config.json') as config_file:
    settings = json.load(config_file)

ip = settings['ip']
port = settings['port']

while True:
    for request in settings['requests']:
        url = "http://{0}:{1}{2}".format(ip, port, request.keys()[0])
        data = request[request.keys()[0]]
        print "Sending to url='{0}' content='{1}'".format(url, data)
        response = requests.post(url, data=data)
        if response is None:
            print "FATAL ERROR!!! SERVER NOT RESPOND!!!"
        print "Response from server = '{0}:{1}'".format(response.status_code, response.text)
        sleep(settings['delay'])