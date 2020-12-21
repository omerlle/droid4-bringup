#!/usr/bin/python3
# -*- coding: utf-8 -*-

# @author: omerlle (omer levin; omerlle@gmail.com)
# Copyright 2020 omer levin

import sys
import datetime
import software.sms_parser as pdu
#import sms.receiver as sms_receiver

__author__ = "omer levin"
__email__ = "omerlle@gmail.com"


sms=pdu.PDUReceive(sys.argv[1])
print(sms.SenderPhoneNumber+","+sms.ServiceCenterDateStamp+",'"+sms.msg+"'")
if sms.total_parts_number > 1:print(str(sms.reference_number)+","+str(sms.sequence_part_number)+"/"+str(sms.total_parts_number))
#print sms.msg
