#! /usr/bin/env python3

# (c) Kazansky137 - Wed Apr 22 22:09:50 UTC 2020

import sys
import os
from common import log, load_config

import smtplib
from email.message import EmailMessage


class SendMail():

    def __init__(self):
        self.params = {}
        load_config(self.params, "config/config.txt")
        pass

    def send(self, _subj, _msg):
        smtp = smtplib.SMTP(self.params["server"])
        msg = EmailMessage()
        msg['From'] = self.params["from"]
        msg['To'] = self.params["to"]
        msg['Reply-To'] = self.params["reply"]
        msg['Subject'] = self.params["prefix"] + ": " + _subj
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
