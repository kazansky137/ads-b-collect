#! /usr/bin/env python3

# (c) Kazansky137 - Thu May 28 20:49:27 UTC 2020

import sys
import os
from common import log, load_config

import smtplib
from email.message import EmailMessage
params     = {}
load_config(params, "config/config.txt")


class SendMail():

    def __init__(self):
        pass

    def send(self, _subj, _msg):
        if params["arg_mail"] is False:
            return
        smtp = smtplib.SMTP(params["server"])
        msg = EmailMessage()
        msg['From'] = params["from"]
        msg['To'] = params["to"]
        msg['Reply-To'] = params["reply"]
        msg['Subject'] = params["pref"] + ": " + _subj
        msg.set_content(_msg)
        smtp.send_message(msg)
        smtp.quit()


if __name__ == "__main__":

    """
    sm = SendMail()
    sm.send("Test1", "Message1")
    sm.send("Test2", "Message2")
    """

    sys.exit(0)
