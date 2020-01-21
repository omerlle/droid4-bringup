import software.modem_helpers as helpers
import logging
import string
import math
import datetime

import utils.date_helper as date_helper
gsm_byte_to_char = (u"@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ`¿abcdefghijklmnopqrstuvwxyzäöñüà")
gsm_special={10:'0x0C',20:'^',40:'{',41:'}',47:'\\',60:'[',61:'~',62:']',64:'|',101:'€'}
gsm_special_chars={'0x0C':10,'^':20,'{':40,'}':41,'\\':47,'[':60,'~':61,']':62,'|':64,'€':101}
gsm_chars={'@': 0, '£': 1, '$': 2, '¥': 3, 'è': 4, 'é': 5, 'ù': 6, 'ì': 7, 'ò': 8, 'Ç': 9, '\n': 10, 'Ø': 11, 'ø': 12, '\r': 13, 'Å': 14, 'å': 15, 'Δ': 16, '_': 17, 'Φ': 18, 'Γ': 19, 'Λ': 20, 'Ω': 21, 'Π': 22, 'Ψ': 23, 'Σ': 24, 'Θ': 25, 'Ξ': 26, '\x1b': 27, 'Æ': 28, 'æ': 29, 'ß': 30, 'É': 31, ' ': 32, '!': 33, '"': 34, '#': 35, '¤': 36, '%': 37, '&': 38, "'": 39, '(': 40, ')': 41, '*': 42, '+': 43, ',': 44, '-': 45, '.': 46, '/': 47, '0': 48, '1': 49, '2': 50, '3': 51, '4': 52, '5': 53, '6': 54, '7': 55, '8': 56, '9': 57, ':': 58, ';': 59, '<': 60, '=': 61, '>': 62, '?': 63, '¡': 64, 'A': 65, 'B': 66, 'C': 67, 'D': 68, 'E': 69, 'F': 70, 'G': 71, 'H': 72, 'I': 73, 'J': 74, 'K': 75, 'L': 76, 'M': 77, 'N': 78, 'O': 79, 'P': 80, 'Q': 81, 'R': 82, 'S': 83, 'T': 84, 'U': 85, 'V': 86, 'W': 87, 'X': 88, 'Y': 89, 'Z': 90, 'Ä': 91, 'Ö': 92, 'Ñ': 93, 'Ü': 94, '`': 95, '¿': 96, 'a': 97, 'b': 98, 'c': 99, 'd': 100, 'e': 101, 'f': 102, 'g': 103, 'h': 104, 'i': 105, 'j': 106, 'k': 107, 'l': 108, 'm': 109, 'n': 110, 'o': 111, 'p': 112, 'q': 113, 'r': 114, 's': 115, 't': 116, 'u': 117, 'v': 118, 'w': 119, 'x': 120, 'y': 121, 'z': 122, 'ä': 123, 'ö': 124, 'ñ': 125, 'ü': 126, 'à': 127,'^':27,'{':27,'}':27,'\\':27,'[':27,'~':27,']':27,'|':27,'€':27}
def gsm7_decode(gsm7):
	msg=''
	escape=False
	l=len(gsm7)
	if l%2!=0:raise error
	buffer = 0
	did=True
	l=len(gsm7)
	if l%2!=0:raise error
	buffer = 0
	did=True
	i=0
	while i < int(l/2):
		x=i*2
		shift = i%7
		if shift==0 and not did:did=True
		else:
			buffer = buffer+(int(gsm7[x:x+2], 16) << shift)
			i=i+1
			did=False
		gsm7_byte = buffer & 127
		buffer = buffer >> 7
		if gsm7_byte == 27:
			escape=True
			continue
		if escape:
			msg=msg+gsm_special[gsm7_byte]
			escape=False
		else:msg=msg+gsm_byte_to_char[gsm7_byte]
	return msg
def is_gsm(msg):
	for c in msg:
		if gsm_chars.get(c) == None:return False
	return True
def gsm7_encode(msg):
	shift=0
	prev=curt=next = extra= None
	gsm7=""
	end=False
	i=0
	l=len(msg)
	while not end:
		if curt != None:
			gsm7=gsm7+"%02x"%((prev >> shift) + ((curt << (7-shift)) & 255))
			shift=(shift+1)%7
			prev=curt if shift>0 else None
			curt=None
		if next == None:
			if i<l:
				next=gsm_chars[msg[i]]
				if next == 27:extra=gsm_special_chars[msg[i]]
				i=i+1
		if prev == None:
			if next == None:end=True
			else:
				prev = next
				next = extra
				extra = None
		else:#curt == None
			if next == None:
				gsm7=gsm7+"%02x"%(prev >> shift)
				prev=None
			else:
				curt= next
				next = extra
				extra = None
	return gsm7
class PDUReceive:
	def __init__(self, pdu):
		self.tpdu=pdu.decode()
		if not all(c in string.hexdigits for c in self.tpdu): raise helpers.ModemError("error-not hex:"+self.tpdu)
		tpdu_length=len(self.tpdu)
		if tpdu_length < 20:raise helpers.ModemError("error-small tpdu<20("+str(tpdu_length)+").")
#		self.SMSC_p=self.tpdu[:16]
		FirstOctet=int(self.tpdu[16:18], 16)
		logging.debug('FirstOctet:'+self.tpdu[16:18])
		hes_header=True if (FirstOctet & 64) == 64 else False
		LengthSenderPhoneNumber=int(self.tpdu[18:20], 16)
		NumberType=self.tpdu[20:22]
#		logging.debug('NumberType:'+NumberType)
		ProtocolIdentifierIndex=22+int((LengthSenderPhoneNumber+1)/2)*2
		if tpdu_length < ProtocolIdentifierIndex+20:raise helpers.ModemError("error-small tpdu<"+str(ProtocolIdentifierIndex+20)+"("+str(tpdu_length)+").")
		if NumberType == '91' or NumberType == '81':
			self.SenderPhoneNumber=''.join([ self.tpdu[22+x:24+x][::-1] for x in range(0, LengthSenderPhoneNumber, 2) ])
		elif NumberType == 'D0':
			self.SenderPhoneNumber='type-D0:'+gsm7_decode(self.tpdu[22:22+LengthSenderPhoneNumber])
		else:
			self.SenderPhoneNumber='type-'+NumberType+":"+self.tpdu[22:22+LengthSenderPhoneNumber]
			logging.error("bad NumberType:"+NumberType)
		logging.debug('Phone:'+self.SenderPhoneNumber)
		sub_tpdu=self.tpdu[ProtocolIdentifierIndex:]
		DataCodingScheme=sub_tpdu[2:4]
		date=[ sub_tpdu[4+x:6+x][::-1] for x in range(0, 13, 2) ]
		date=datetime.datetime.strptime(''.join(date[:6]), "%y%m%d%H%M%S")
		self.ServiceCenterDateStamp=date_helper.date_to_string(date)
		LengthSmsBody=sub_tpdu[18:20]
		if hes_header:
			LengthUserDataHeader=int(sub_tpdu[20:22], 16)
			UserDataHeader=sub_tpdu[22:22+LengthUserDataHeader*2]
			msg_index=22+LengthUserDataHeader*2
			end_ref_inx=0
			if LengthUserDataHeader == 6 and UserDataHeader[:4] == '0804':end_ref_inx=8
			elif LengthUserDataHeader == 5 and UserDataHeader[:4] == '0003':end_ref_inx=6
			else: raise helpers.ModemError("error-bad Header. LengthUserDataHeader:"+str(LengthUserDataHeader)+", UserDataHeader:"+UserDataHeader)
			self.reference_number=int(UserDataHeader[4:end_ref_inx],16)
			self.total_parts_number=int(UserDataHeader[end_ref_inx:end_ref_inx+2],16)
			self.sequence_part_number=int(UserDataHeader[end_ref_inx+2:end_ref_inx+4],16)
		else:
			msg_index=20
			self.total_parts_number=1
		SmsBody=sub_tpdu[msg_index:]
		if DataCodingScheme=='00':
			self.msg=gsm7_decode(SmsBody)
		elif DataCodingScheme=='08':
			self.msg=int(SmsBody,16).to_bytes(int(len(SmsBody)/2),byteorder='big').decode("utf-16-be")
		else: raise helpers.ModemError("error-bad DataCodingScheme:"+DataCodingScheme)
class PDUSend:
	def __init__(self, phone, message, nickname, db):
		self.nickname=nickname
		self.message=message
		self.phone=phone
		self.tpdus=[]
		msg="000c91"+''.join([ phone[x:2+x][::-1] for x in range(0, 11, 2) ])+"00"
		if is_gsm(message):
			data_coding_scheme="00"
			smsBody=gsm7_encode(message)
		else:
			data_coding_scheme="08"
			#smsBody=unicode(message, "utf8").encode("utf-16-be").encode("hex")
			big=str('{:0'+str(len(message)*4+4)+'x}').format(int.from_bytes(message.encode('utf16'), "big"))[4:]
			smsBody=''.join([ big[2+x:4+x]+big[x:2+x] for x in range(0, len(big), 4) ])
		length=int(len(smsBody)/2)
		if length>140:
			reference_number='%04x'%(db.get_and_set_reference_number(phone))
			logging.debug(reference_number)
			pdu_type="41"
			count=int(math.ceil(length/124.0))
			count_hex='%02x'%(count)
			information_element_identifier="08"# 0x08 for concatenated short message 16-bit reference number
			for x in range(count):
				information_element_data=reference_number+count_hex+'%02x'%(x+1)
				user_data_header=information_element_identifier+'%02x'%(int(len(information_element_data)/2))+information_element_data
				p_sms_body=smsBody[x*248:x*248+248]
				header='%02x'%(int(len(user_data_header)/2))+user_data_header
				data=header+p_sms_body
				self.tpdus.append('41'+msg+data_coding_scheme+'%02x'%(int(len(data)/2))+data)
		else:
			self.tpdus.append('01'+msg+data_coding_scheme+'%02x'%length+smsBody)
