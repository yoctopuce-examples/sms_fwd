#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
from yoctopuce.yocto_api import *
from yoctopuce.yocto_messagebox import *


class SMSRules:
    def __init__(self, incoming_pattern, out_numbers):
        self._incoming_pattern = incoming_pattern
        self._targets = out_numbers

    def match(self, number):
        if (self._incoming_pattern == '' or self._incoming_pattern == "*"):
            return True
        return number == self._incoming_pattern

    def getTargets(self):
        return self._targets


class SMSForwarder:
    def __init__(self, config_file, verbose, logfile):
        self.verbose = verbose
        with open(config_file, "r") as f:
            config = json.load(f)
        self._rules = []
        for rule in config['rules']:
            self._rules.append(SMSRules(rule["pattern"], rule["out_numbers"]))
        self._logfile = logfile
        if self.verbose:
            self.log("Use Yoctopuce library : " + YAPI.GetAPIVersion())

    def log(self, line):
        if self.verbose:
            print(line.rstrip())
        if self._logfile != '':
            with open(self._logfile, "a", encoding="utf-8") as file:
                str_time = time.strftime("%a, %d %b %Y %H:%M:%S")
                file.write("[%s]:%s\n" % (str_time, line))

    def run(self):
        errmsg = YRefParam()
        if YAPI.RegisterHub("usb", errmsg) != YAPI.SUCCESS:
            sys.exit("Unable use USB port %s" % (errmsg.value))
        mbox = YMessageBox.FirstMessageBox()
        if mbox is None:
            sys.exit("No device that support YMessageBox")
        module = mbox.get_module()
        self.log("Use %s %s" % (module.get_productName(), module.get_serialNumber()))
        while True:
            messages = mbox.get_messages()
            for msg in messages:
                sender = msg.get_sender()
                self.log("New SMS from %s:" % (sender))
                self.log("   %s" % (msg.get_textData()))
                unicodeData = msg.get_unicodeData()
                for rule in self._rules:
                    if rule.match(sender):
                        targets = rule.getTargets()
                        for dst_num in targets:
                            self.log("forward it to %s" % (dst_num))
                            sms = mbox.newMessage(dst_num)
                            sms.addUnicodeData(unicodeData)
                            sms.send()
                            YAPI.Sleep(2000)
                    self.log("clear message from %s" % (sender))
                msg.deleteFromSIM()
            YAPI.Sleep(2000)


def main():
    parser = argparse.ArgumentParser(description='An SMS forwarder.')
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_true")
    parser.add_argument('-c', '--config', default='config.json',
                        help='Config files in JSON format')
    parser.add_argument('-l', '--logfile', default='',
                        help="Log all SMS transmissions")
    args = parser.parse_args()
    controller = SMSForwarder(args.config, args.verbose, args.logfile)
    controller.run()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
