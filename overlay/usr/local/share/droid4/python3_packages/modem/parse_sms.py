#!/usr/bin/python3
import sys
import datetime
from software.sms import pdu
#import sms.receiver as sms_receiver
sms=pdu.PDUReceive(sys.argv[1])
print(sms.SenderPhoneNumber+","+sms.ServiceCenterTimeStamp.strftime("%Y-%m-%d %H:%M:%S")+",'"+sms.msg+"'")
if sms.total_parts_number > 1:print(str(sms.reference_number)+","+str(sms.sequence_part_number)+"/"+str(sms.total_parts_number))
#print sms.msg
