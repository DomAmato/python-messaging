# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# Refactored using cleaner code from
# https://github.com/jezeniel/smsutil/blob/master/smsutil/codecs.py
import codecs
from array import array
import re

# default GSM 03.38 -> unicode
GSM_BASIC_CHARSET = {
    '\x00': '\u0040',  # COMMERCIAL AT
    '\x01': '\u00A3',  # POUND SIGN
    '\x02': '\u0024',  # DOLLAR SIGN
    '\x03': '\u00A5',  # YEN SIGN
    '\x04': '\u00E8',  # LATIN SMALL LETTER E WITH GRAVE
    '\x05': '\u00E9',  # LATIN SMALL LETTER E WITH ACUTE
    '\x06': '\u00F9',  # LATIN SMALL LETTER U WITH GRAVE
    '\x07': '\u00EC',  # LATIN SMALL LETTER I WITH GRAVE
    '\x08': '\u00F2',  # LATIN SMALL LETTER O WITH GRAVE
    '\x09': '\u00C7',  # LATIN CAPITAL LETTER C WITH CEDILLA
                        # The Unicode page suggests this is a mistake: but
                        # it's still in the latest version of the spec and
                        # our implementation has to be exact.

    '\x0A': '\u000A',  # LINE FEED
    '\x0B': '\u00D8',  # LATIN CAPITAL LETTER O WITH STROKE
    '\x0C': '\u00F8',  # LATIN SMALL LETTER O WITH STROKE
    '\x0D': '\u000D',  # CARRIAGE RETURN
    '\x0E': '\u00C5',  # LATIN CAPITAL LETTER A WITH RING ABOVE
    '\x0F': '\u00E5',  # LATIN SMALL LETTER A WITH RING ABOVE
    '\x10': '\u0394',  # GREEK CAPITAL LETTER DELTA
    '\x11': '\u005F',  # LOW LINE
    '\x12': '\u03A6',  # GREEK CAPITAL LETTER PHI
    '\x13': '\u0393',  # GREEK CAPITAL LETTER GAMMA
    '\x14': '\u039B',  # GREEK CAPITAL LETTER LAMDA
    '\x15': '\u03A9',  # GREEK CAPITAL LETTER OMEGA
    '\x16': '\u03A0',  # GREEK CAPITAL LETTER PI
    '\x17': '\u03A8',  # GREEK CAPITAL LETTER PSI
    '\x18': '\u03A3',  # GREEK CAPITAL LETTER SIGMA
    '\x19': '\u0398',  # GREEK CAPITAL LETTER THETA
    '\x1A': '\u039E',  # GREEK CAPITAL LETTER XI
    '\x1C': '\u00C6',  # LATIN CAPITAL LETTER AE
    '\x1D': '\u00E6',  # LATIN SMALL LETTER AE
    '\x1E': '\u00DF',  # LATIN SMALL LETTER SHARP S (German)
    '\x1F': '\u00C9',  # LATIN CAPITAL LETTER E WITH ACUTE
    '\x20': '\u0020',  # SPACE
    '\x21': '\u0021',  # EXCLAMATION MARK
    '\x22': '\u0022',  # QUOTATION MARK
    '\x23': '\u0023',  # NUMBER SIGN
    '\x24': '\u00A4',  # CURRENCY SIGN
    '\x25': '\u0025',  # PERCENT SIGN
    '\x26': '\u0026',  # AMPERSAND
    '\x27': '\u0027',  # APOSTROPHE
    '\x28': '\u0028',  # LEFT PARENTHESIS
    '\x29': '\u0029',  # RIGHT PARENTHESIS
    '\x2A': '\u002A',  # ASTERISK
    '\x2B': '\u002B',  # PLUS SIGN
    '\x2C': '\u002C',  # COMMA
    '\x2D': '\u002D',  # HYPHEN-MINUS
    '\x2E': '\u002E',  # FULL STOP
    '\x2F': '\u002F',  # SOLIDUS
    '\x30': '\u0030',  # DIGIT ZERO
    '\x31': '\u0031',  # DIGIT ONE
    '\x32': '\u0032',  # DIGIT TWO
    '\x33': '\u0033',  # DIGIT THREE
    '\x34': '\u0034',  # DIGIT FOUR
    '\x35': '\u0035',  # DIGIT FIVE
    '\x36': '\u0036',  # DIGIT SIX
    '\x37': '\u0037',  # DIGIT SEVEN
    '\x38': '\u0038',  # DIGIT EIGHT
    '\x39': '\u0039',  # DIGIT NINE
    '\x3A': '\u003A',  # COLON
    '\x3B': '\u003B',  # SEMICOLON
    '\x3C': '\u003C',  # LESS-THAN SIGN
    '\x3D': '\u003D',  # EQUALS SIGN
    '\x3E': '\u003E',  # GREATER-THAN SIGN
    '\x3F': '\u003F',  # QUESTION MARK
    '\x40': '\u00A1',  # INVERTED EXCLAMATION MARK
    '\x41': '\u0041',  # LATIN CAPITAL LETTER A
    '\x42': '\u0042',  # LATIN CAPITAL LETTER B
    '\x43': '\u0043',  # LATIN CAPITAL LETTER C
    '\x44': '\u0044',  # LATIN CAPITAL LETTER D
    '\x45': '\u0045',  # LATIN CAPITAL LETTER E
    '\x46': '\u0046',  # LATIN CAPITAL LETTER F
    '\x47': '\u0047',  # LATIN CAPITAL LETTER G
    '\x48': '\u0048',  # LATIN CAPITAL LETTER H
    '\x49': '\u0049',  # LATIN CAPITAL LETTER I
    '\x4A': '\u004A',  # LATIN CAPITAL LETTER J
    '\x4B': '\u004B',  # LATIN CAPITAL LETTER K
    '\x4C': '\u004C',  # LATIN CAPITAL LETTER L
    '\x4D': '\u004D',  # LATIN CAPITAL LETTER M
    '\x4E': '\u004E',  # LATIN CAPITAL LETTER N
    '\x4F': '\u004F',  # LATIN CAPITAL LETTER O
    '\x50': '\u0050',  # LATIN CAPITAL LETTER P
    '\x51': '\u0051',  # LATIN CAPITAL LETTER Q
    '\x52': '\u0052',  # LATIN CAPITAL LETTER R
    '\x53': '\u0053',  # LATIN CAPITAL LETTER S
    '\x54': '\u0054',  # LATIN CAPITAL LETTER T
    '\x55': '\u0055',  # LATIN CAPITAL LETTER U
    '\x56': '\u0056',  # LATIN CAPITAL LETTER V
    '\x57': '\u0057',  # LATIN CAPITAL LETTER W
    '\x58': '\u0058',  # LATIN CAPITAL LETTER X
    '\x59': '\u0059',  # LATIN CAPITAL LETTER Y
    '\x5A': '\u005A',  # LATIN CAPITAL LETTER Z
    '\x5B': '\u00C4',  # LATIN CAPITAL LETTER A WITH DIAERESIS
    '\x5C': '\u00D6',  # LATIN CAPITAL LETTER O WITH DIAERESIS
    '\x5D': '\u00D1',  # LATIN CAPITAL LETTER N WITH TILDE
    '\x5E': '\u00DC',  # LATIN CAPITAL LETTER U WITH DIAERESIS
    '\x5F': '\u00A7',  # SECTION SIGN
    '\x60': '\u00BF',  # INVERTED QUESTION MARK
    '\x61': '\u0061',  # LATIN SMALL LETTER A
    '\x62': '\u0062',  # LATIN SMALL LETTER B
    '\x63': '\u0063',  # LATIN SMALL LETTER C
    '\x64': '\u0064',  # LATIN SMALL LETTER D
    '\x65': '\u0065',  # LATIN SMALL LETTER E
    '\x66': '\u0066',  # LATIN SMALL LETTER F
    '\x67': '\u0067',  # LATIN SMALL LETTER G
    '\x68': '\u0068',  # LATIN SMALL LETTER H
    '\x69': '\u0069',  # LATIN SMALL LETTER I
    '\x6A': '\u006A',  # LATIN SMALL LETTER J
    '\x6B': '\u006B',  # LATIN SMALL LETTER K
    '\x6C': '\u006C',  # LATIN SMALL LETTER L
    '\x6D': '\u006D',  # LATIN SMALL LETTER M
    '\x6E': '\u006E',  # LATIN SMALL LETTER N
    '\x6F': '\u006F',  # LATIN SMALL LETTER O
    '\x70': '\u0070',  # LATIN SMALL LETTER P
    '\x71': '\u0071',  # LATIN SMALL LETTER Q
    '\x72': '\u0072',  # LATIN SMALL LETTER R
    '\x73': '\u0073',  # LATIN SMALL LETTER S
    '\x74': '\u0074',  # LATIN SMALL LETTER T
    '\x75': '\u0075',  # LATIN SMALL LETTER U
    '\x76': '\u0076',  # LATIN SMALL LETTER V
    '\x77': '\u0077',  # LATIN SMALL LETTER W
    '\x78': '\u0078',  # LATIN SMALL LETTER X
    '\x79': '\u0079',  # LATIN SMALL LETTER Y
    '\x7A': '\u007A',  # LATIN SMALL LETTER Z
    '\x7B': '\u00E4',  # LATIN SMALL LETTER A WITH DIAERESIS
    '\x7C': '\u00F6',  # LATIN SMALL LETTER O WITH DIAERESIS
    '\x7D': '\u00F1',  # LATIN SMALL LETTER N WITH TILDE
    '\x7E': '\u00FC',  # LATIN SMALL LETTER U WITH DIAERESIS
    '\x7F': '\u00E0',  # LATIN SMALL LETTER A WITH GRAVE
}

# default GSM 03.38 escaped characters -> unicode
GSM_EXT_CHARSET = {
    '\x1B\x0A': '\u000C',  # FORM FEED
    '\x1B\x14': '\u005E',  # CIRCUMFLEX ACCENT
    '\x1B\x28': '\u007B',  # LEFT CURLY BRACKET
    '\x1B\x29': '\u007D',  # RIGHT CURLY BRACKET
    '\x1B\x2F': '\u005C',  # REVERSE SOLIDUS
    '\x1B\x3C': '\u005B',  # LEFT SQUARE BRACKET
    '\x1B\x3D': '\u007E',  # TILDE
    '\x1B\x3E': '\u005D',  # RIGHT SQUARE BRACKET
    '\x1B\x40': '\u007C',  # VERTICAL LINE
    '\x1B\x65': '\u20AC',  # EURO SIGN
}

# Replacement characters, default is question mark. Used when it is not too
# important to ensure exact UTF-8 -> GSM -> UTF-8 equivilence, such as when
# humans read and write SMS. But for USSD and other M2M applications it's
# important to ensure the conversion is exact.
GSM_REPLACE_CHARSET = {
    '\u00E7': '\x09',  # LATIN SMALL LETTER C WITH CEDILLA

    '\u0391': '\x41',  # GREEK CAPITAL LETTER ALPHA
    '\u0392': '\x42',  # GREEK CAPITAL LETTER BETA
    '\u0395': '\x45',  # GREEK CAPITAL LETTER EPSILON
    '\u0397': '\x48',  # GREEK CAPITAL LETTER ETA
    '\u0399': '\x49',  # GREEK CAPITAL LETTER IOTA
    '\u039A': '\x4B',  # GREEK CAPITAL LETTER KAPPA
    '\u039C': '\x4D',  # GREEK CAPITAL LETTER MU
    '\u039D': '\x4E',  # GREEK CAPITAL LETTER NU
    '\u039F': '\x4F',  # GREEK CAPITAL LETTER OMICRON
    '\u03A1': '\x50',  # GREEK CAPITAL LETTER RHO
    '\u03A4': '\x54',  # GREEK CAPITAL LETTER TAU
    '\u03A7': '\x58',  # GREEK CAPITAL LETTER CHI
    '\u03A5': '\x59',  # GREEK CAPITAL LETTER UPSILON
    '\u0396': '\x5A',  # GREEK CAPITAL LETTER ZETA
}

GSM_CHARSET = {**GSM_BASIC_CHARSET, **GSM_EXT_CHARSET}

QUESTION_MARK = ord('\u003F')
ESCAPE = ord('\x1B')
NBSP = ord('\u00A0')

decoding_map = dict((ord(k), ord(v)) if len(k) == 1 else (bytes([ord(k[0]), ord(k[1])]), ord(v)) for k, v in GSM_CHARSET.items())

encoding_map = dict((ord(v), ord(k)) for k, v in GSM_BASIC_CHARSET.items())

ext_encoding_map = dict((ord(v), ord(k[1])) for k, v in GSM_EXT_CHARSET.items())

replace_encode_map = dict((ord(k), ord(v)) for k, v in GSM_REPLACE_CHARSET.items())

def encode_gsm0338(text, errors, encoding_map, ext_encoding_map, replace_encode_map):
    encoded = b''
    for char in text:
        ochar = ord(char)
        ec = b''
        if ochar in encoding_map:
            ec = encoding_map.get(ochar)
        else:
            if ochar in ext_encoding_map:
                encoded += bytes([ESCAPE])
                ec = ext_encoding_map.get(ochar)
            elif errors == 'strict':
                raise UnicodeError("Invalid GSM character")
            elif errors == 'replace':
                ec = replace_encode_map.get(ochar, QUESTION_MARK)
            elif errors == 'ignore':
                pass
            else:
                raise UnicodeError("Unknown error handling")
        if isinstance(ec, int):
            ec = bytes([ec])
        encoded += ec
    return encoded, len(encoded)

def decode_gsm0338(text, decoding_map):
    decoded = ''
    skip = None
    for index, char in enumerate(bytes(text)):
        next_char = index + 1
        if skip == index:
            continue
        if char != ESCAPE:
            d = decoding_map.get(char)
        elif char == ESCAPE and next_char < len(text):
            ext_char = bytes([ESCAPE, text[next_char]])
            d = decoding_map.get(ext_char, NBSP)
            if d != NBSP:
                skip = next_char
        else:
            d = NBSP
        decoded += chr(d)
    return decoded, len(decoded)


class GSM0338Codec(codecs.Codec):
    def encode(self, input_, errors='strict'):
        return encode_gsm0338(input_, errors, encoding_map, ext_encoding_map, replace_encode_map)

    def decode(self, input_, errors='strict'):
        return decode_gsm0338(input_, decoding_map)


class GSM0338IncrementalEncoder(codecs.IncrementalEncoder):
    def encode(self, input_, final=False):
        return encode_gsm0338(input_, self.errors, encoding_map, ext_encoding_map, replace_encode_map)[0]


class GSM0338IncrementalDecoder(codecs.IncrementalDecoder):
    def decode(self, input_, final=False):
        return decode_gsm0338(input_, decoding_map)[0]


class GSM0338StreamReader(GSM0338Codec, codecs.StreamReader):
    pass


class GSM0338StreamWriter(GSM0338Codec, codecs.StreamWriter):
    pass


def search_gsm0338(encoding):
    if encoding in ('gsm0338', 'gsm7'):
        return codecs.CodecInfo(
            name='gsm0338',
            encode=GSM0338Codec().encode,
            decode=GSM0338Codec().decode,
            incrementalencoder=GSM0338IncrementalEncoder,
            incrementaldecoder=GSM0338IncrementalDecoder,
            streamwriter=GSM0338StreamWriter,
            streamreader=GSM0338StreamReader
        )
    return None


def is_valid_gsm(text):
    ''' Validate if `text` is a valid gsm 03.338.  '''
    r = '^[' + re.escape(''.join(list(GSM_CHARSET.values()))) + ']+$'
    return re.match(r, text, re.UNICODE) is not None


codecs.register(search_gsm0338)