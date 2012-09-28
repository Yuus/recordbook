# -*- encoding: utf-8 -*-

import urllib2
import logging
import demjson

LOGGER = logging.getLogger("AvisoSMS")

class AvisoSMS:

    def __init__(self, username, password, sourceAddress):
        self.username = username
        self.password = password
        self.sourceAddress = sourceAddress

    def send_message(self, phone, text):
        request_data = {
            'send_message':
                [{
                    'destination_address': phone,
                    'message': text,
                    'source_address': self.sourceAddress,
                }],
            'username': self.username,
            'password': self.password,
        }

        request = urllib2.Request("http://api.avisosms.ru/sms/json/1", demjson.encode(request_data).encode("utf-8"))
        try:
            response = demjson.decode(urllib2.urlopen(request).read())
            LOGGER.info("Reading response %s" % str(response))
            state = "OK_Operation_Completed" == response["status"] == response["send_message"][0]["status"]
        except (urllib2.URLError, demjson.JSONDecodeError):
            LOGGER.fatal("EXCEPTION!")
            state = False

        return state



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,)

    sms = AvisoSMS("raspisanie.ru", "HQYPswzq2k9UrSYMWVMp", "Raspisanie")
    print sms.send_message("79160700611", u"Максим получил 5 Математике 21.09")