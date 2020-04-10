from array import array
from datetime import timedelta, tzinfo
from math import floor
import re
import binascii

HEX_STR = re.compile(r"^[0-9A-Fa-f]+$")

class FixedOffset(tzinfo):
    """Fixed offset in minutes east from UTC."""

    def __init__(self, offset, name):
        if isinstance(offset, timedelta):
            self.offset = offset
        else:
            self.offset = timedelta(minutes=offset)

        self.__name = name

    @classmethod
    def from_timezone(cls, tz_str, name):
        # no timezone, GMT+3, GMT-3
        # '', '+0330', '-0300'
        if not tz_str:
            return cls(timedelta(0), name)

        sign = 1 if '+' in tz_str else -1
        offset = tz_str.replace('+', '').replace('-', '')
        hours, minutes = int(offset[:2]), int(offset[2:])
        minutes += hours * 60

        if sign == 1:
            td = timedelta(minutes=minutes)
        elif sign == -1:
            td = timedelta(days=-1, minutes=minutes)

        return cls(td, name)

    def utcoffset(self, dt):
        return self.offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return timedelta(0)


def bytes_to_str(b):
    if isinstance(b, bytes):
        return b.decode()
    return b


def hex_to_int_array(pdu):
    return array('B', [int(pdu[i:i + 2], 16) for i in range(0, len(pdu), 2)])


def swap(s):
    """Swaps ``s`` according to GSM 23.040"""
    what = s[:]
    for n in range(1, len(what), 2):
        what[n - 1], what[n] = what[n], what[n - 1]

    return what


def swap_number(n):
    data = swap(list(n.replace('f', '')))
    return ''.join(data)


def clean_number(n):
    return n.strip().replace(' ', '')


def encode_str(s):
    """
    Convert a string to hexidecimal values

    :param s: string
    :type s: str
    :return: hexidecimal representation of given string
    :rtype: str
    """
    # return binascii.hexlify(s.encode()).decode()
    return ''.join(["%02x" % ord(n) for n in s])


def encode_bytes(b):
    """
    Convert to hexidecimal representation

    :param b: byte array
    :type b: bytes
    :return: Byte string converted to hex and returned as a string
    :rtype: str
    """
    return binascii.hexlify(b).decode()


def pack_8bits_to_7bits(message, udh=None):
    pdu = ""
    txt = bytes_to_str(message)
    if udh is None:
        tl = len(txt)
        txt += '\x00'
        msgl = int(len(txt) * 7 / 8)
        op = [-1] * msgl
        c = shift = 0

        for n in range(msgl):
            if shift == 6:
                c += 1

            shift = n % 7
            lb = ord(txt[c]) >> shift
            hb = (ord(txt[c + 1]) << (7 - shift) & 255)
            op[n] = lb + hb
            c += 1

        pdu = chr(tl) + ''.join(map(chr, op))
    else:
        txt = "\x00\x00\x00\x00\x00\x00" + txt
        tl = len(txt)

        txt += '\x00'
        msgl = int(len(txt) * 7 / 8)
        op = [-1] * msgl
        c = shift = 0

        for n in range(msgl):
            if shift == 6:
                c += 1

            shift = n % 7
            lb = ord(txt[c]) >> shift
            hb = (ord(txt[c + 1]) << (7 - shift) & 255)
            op[n] = lb + hb
            c += 1

        for i, char in enumerate(udh):
            op[i] = ord(char)

        pdu = chr(tl) + ''.join(map(chr, op))

    return encode_str(pdu)


def pack_8bits_to_8bit(message, udh=None):
    text = message
    if udh is not None:
        if isinstance(udh, bytes):
            udh = udh.decode()
        text = udh + text

    mlen = len(text)
    message = chr(mlen) + message
    return encode_str(message)


def pack_8bits_to_ucs2(message, udh=None):
    # XXX: This does not control the size respect to UDH
    text = message
    nmesg = ''

    if udh is not None:
        if isinstance(udh, bytes):
            udh = udh.decode()
        text = udh + text

    for n in text:
        nmesg += chr(ord(n) >> 8) + chr(ord(n) & 0xFF)

    mlen = len(text) * 2
    message = chr(mlen) + nmesg
    return encode_str(message)

def unpack_msg(pdu):
    if isinstance(pdu, (array, list)):
        return unpack_list_msg(pdu)
    
    if isinstance(pdu, bytes):
        return unpack_hex_bytes_msg(pdu)
    
    if isinstance(pdu, str) and HEX_STR.match(pdu):
        return unpack_hex_str_msg(pdu)
    
    raise TypeError('Unhandled Type %s' % type(pdu))

def unpack_hex_str_msg(pdu):
    """Unpacks ``pdu`` into septets and returns the decoded string"""
    # Taken/modified from Dave Berkeley's pysms package
    count = last = 0
    result = []

    prev_char = ''
    count = last = 0
    result = []

    for index, char in enumerate(pdu):
        if index % 2 == 1:
            byte = int(prev_char + char, 16)
        else:
            prev_char = char
            continue
        mask = 0x7F >> count
        out = ((byte & mask) << count) + last
        last = byte >> (7 - count)
        result.append(out)

        if len(result) >= 0xa0:
            break

        if count == 6:
            result.append(last)
            last = 0

        count = (count + 1) % 7

    return bytes(result)


def unpack_hex_bytes_msg(pdu):
    """Unpacks ``pdu`` into septets and returns the decoded string"""
    # Taken/modified from Dave Berkeley's pysms package
    count = last = 0
    result = []

    prev_byte = b''
    count = last = 0
    result = []

    for index, byte in enumerate(pdu):
        if index % 2 == 1:
            byte = int(bytes([prev_byte, byte]), 16)
        else:
            prev_byte = byte
            continue
        mask = 0x7F >> count
        out = ((byte & mask) << count) + last
        last = byte >> (7 - count)
        result.append(out)

        if len(result) >= 0xa0:
            break

        if count == 6:
            result.append(last)
            last = 0

        count = (count + 1) % 7

    return bytes(result)


def unpack_list_msg(pdu):
    """Unpacks ``pdu`` into septets and returns the decoded string"""
    # Taken/modified from Dave Berkeley's pysms package
    count = last = 0
    result = []

    for byte in pdu:
        mask = 0x7F >> count
        out = ((byte & mask) << count) + last
        last = byte >> (7 - count)
        result.append(out)

        if len(result) >= 0xa0:
            break

        if count == 6:
            result.append(last)
            last = 0

        count = (count + 1) % 7

    return bytes(result)


def timedelta_to_relative_validity(t):
    """
    Convert ``t`` to its relative validity period

    In case the resolution of ``t`` is too small for a time unit,
    it will be floor-rounded to the previous sane value

    :type t: datetime.timedelta

    :return int
    """
    if t < timedelta(minutes=5):
        raise ValueError("Min resolution is five minutes")

    if t > timedelta(weeks=63):
        raise ValueError("Max validity is 63 weeks")

    if t <= timedelta(hours=12):
        return int(floor(t.seconds / (60 * 5))) - 1

    if t <= timedelta(hours=24):
        t -= timedelta(hours=12)
        return int(floor(t.seconds / (60 * 30))) + 143

    if t <= timedelta(days=30):
        return t.days + 166

    if t <= timedelta(weeks=63):
        return int(floor(t.days / 7)) + 192


def datetime_to_absolute_validity(d, tzname='Unknown'):
    """Convert ``d`` to its integer representation"""
    n = d.strftime("%y %m %d %H %M %S %z").split(" ")
    # compute offset
    offset = FixedOffset.from_timezone(n[-1], tzname).offset
    # one unit is 15 minutes
    s = "%02d" % int(floor(offset.seconds / (60 * 15)))

    if offset.days < 0:
        # set MSB to 1
        s = "%02x" % ((int(s[0]) << 4) | int(s[1]) | 0x80)

    n[-1] = s

    return [int(c[::-1], 16) for c in n]
