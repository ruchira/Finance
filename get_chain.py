#!/usr/bin/env python

# Module get_chain.py
# Procedure to retrieve an option chain from Yahoo! Finance, parse it and write
# it to a CSV (comma-separated-values) format file.
# 
# Author: Ruchira S. Datta
#
# Copyright 2011 by Ruchira S. Datta
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation fies (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM< DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM<
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import urllib2
import os, sys, re

  
def get_chain(symbol, year, month):
  """Retrieve an option chain from Yahoo! Finance into a CSV file."""
  month_of_name = { 'January': 1, 'February': 2, 'March': 3, 'April': 4,
                'May': 5, 'June': 6, 'Jun': 6, 'July': 7, 'August': 8,
                'September': 9, 'October': 10, 'November': 11, 'December': 12 }
  try:
    response = urllib2.urlopen('http://finance.yahoo.com/q/op?s=%s&m=%d-%02d'
                % (symbol, year, month))
  except urllib2.HTTPError:
    return
  html = response.read()
  market_time_re = re.compile('"yfs_market_time">([^,]+), ([^ ]+) (\d+), (\d+), ([^:]+):([^AP]+)([AP]M)')
  m = market_time_re.search(html)
  day_of_week, month_name, day_of_month, year, hour, minute, ampm \
      = m.groups()
  if ampm == 'PM':
    if hour != '12':
      hour = int(hour) + 12
    else:
      hour = 12
  elif ampm == 'AM':
    hour = int(hour)
  else:
    print "Weird market time:", m.groups()
    return
  month = month_of_name[month_name]
  dayspec = "%s%02d%s" % (year, month, day_of_month)
  basename="%s_%s_%s_%02d%s" % (symbol.replace('/','_'),dayspec,day_of_week, hour, minute)

  put_re = re.compile('Put Options')
  sections = put_re.split(html)
  if len(sections) == 2:
    call_html, put_html = sections
  else:
    call_html = html
    put_html = None
  strike_re = re.compile('k=')
  numeric_re = re.compile('\d+\.\d*')
  optsym_re = re.compile('%s\d+[CP]\d+' % symbol.replace('-',''))
  symdir = symbol.replace('/','_')
  if not os.path.exists(symdir):
    os.mkdir(symdir)
  dir = os.path.join(symdir, dayspec)
  if not os.path.exists(dir):
    os.mkdir(dir)
  outf = open(os.path.join(dir,"%s_Options.csv" % basename), 'w')
  outf.write("CallOrPut,Strike,Symbol,Last,Change,Bid,Ask,Volume,OpInt\n")
  last_re = re.compile('yfs_l\d+_%s">([^<]*)<' % symbol.lower())
  last = last_re.search(html).group(1)
  change_re = re.compile('yfs_c\d+_%s"> <b style="color:#000000;">([^<]*)<'
                          % symbol.lower())
  m = change_re.search(html)
  if m:
    change = m.group(1)
  else:
    change = 'N/A'
  field_re = re.compile('<td class="yfnc_(h|tabledata1)" align="right">([^<]*)</td>')
  outf.write("S,N/A,%s,%s,%s,N/A,N/A,N/A,N/A\n" % (symbol,last,change))
  def parse_option_info(outf, big_token, is_call):
    m = numeric_re.match(big_token)
    strike = m.group(0)
    rest = big_token[m.end():]
    m = optsym_re.search(rest)
    optsym = m.group(0)
    rest = rest[m.end():]
    last_re = re.compile('yfs_l\d+_%s">([^<]*)<' % optsym.lower())
    m = last_re.search(rest)
    if not m:
      m = field_re.search(rest)
    last = m.group(1)
    rest = rest[m.end():]
    change_re = re.compile('yfs_c\d+_%s"> <b style="color:#000000;">([^<]*)</b></span></td>' % optsym.lower())
    m = change_re.search(rest)
    if m:
      change = m.group(1)
      rest = rest[m.end():]
    else:
      change_re = re.compile('yfs_c\d+_%s"><img width="10" height="14" border="0" src="http://l.yimg.com/a/i/us/fi/03rd/[^\.]*\.gif" alt="[^"]*"> <b style="color:#008800;">([^<]*)</b></span></td>' % optsym.lower())
      m = change_re.search(rest)
      if m:
        change = m.group(1)
        rest = rest[m.end():]
      else:
        change_re = re.compile('yfs_c\d+_%s"><img width="10" height="14" border="0" src="http://l.yimg.com/a/i/us/fi/03rd/[^\.]*\.gif" alt="[^"]*"> <b style="color:#cc0000;">([^<]*)</b></span></td>' % optsym.lower())
        m = change_re.search(rest)
        if m:
          change = '-' + m.group(1)
          rest = rest[m.end():]
        else:
          change = 'N/A'
    bid_re = re.compile('yfs_b\d+_%s">([^<]*)</span></td>' % optsym.lower())
    m = bid_re.search(rest)
    if m:
      bid = m.group(1)
      rest = rest[m.end():]
    else:
      m = field_re.match(rest)
      if m:
        bid = m.group(2)
        rest = rest[m.end():]
      else:
        bid = 'N/A'
    ask_re = re.compile('yfs_a\d+_%s">([^<]*)</span></td>' % optsym.lower())
    m = ask_re.search(rest)
    if m:
      ask = m.group(1)
    else:
      m = field_re.match(rest)
      if m:
        ask = m.group(2)
        rest = rest[m.end():]
      else:
        ask = 'N/A'
    volume_re = re.compile('yfs_v\d*_%s">([^<]*)</span></td>' % optsym.lower())
    m = volume_re.search(rest)
    volume = m.group(1).replace(',','')
    rest = rest[m.end():]
    m = field_re.search(rest)
    opint = m.group(2).replace(',','')
    if is_call:
      outf.write("C,")
    else:
      outf.write("P,")
    outf.write("%s,%s,%s,%s,%s,%s,%s,%s\n" % (strike, optsym, last, change, bid, ask,volume,opint))
    
  call_tokens = strike_re.split(call_html)
  for token in call_tokens[1:]:
      parse_option_info(outf, token, True)
  if put_html:
    put_tokens = strike_re.split(put_html)
    for token in put_tokens[1:]:
        parse_option_info(outf, token, False)
  outf.close()
