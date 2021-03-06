﻿#!/usr/bin/env python3

class Logger:
  def __init__(self, log_file, mem_size, max_len):
    self.f = log_file
    self.mem = []
    self.MAX_MEM_SIZE = mem_size
    self.MAX_LENGTH = max_len

  def __iter__(self):
    for line in reversed(self.mem):
      yield line
    with open(self.f, 'r') as f:
      for line in reversed(f.readlines()): # TODO: improve
        yield line

  def log(self, line):
    self.mem.append(line + '\n')
    if len(self.mem) > self.MAX_MEM_SIZE:
      self.flush(int(len(self.mem)/2))

  def flush(self, size=None):
    if size is None: size = len(self.mem)
    with open(self.f, 'a') as f:
      f.writelines(self.mem[:size])
    self.mem = self.mem[size:]

  def find(self, begin, end=None):
    if end is None: end = begin
    result, matched = [], False
    for line in self:
      if len(result) > self.MAX_LENGTH:
        return "Désolé, cette citation est trop longue (plus de %s lignes)." % str(self.MAX_LENGTH)
      if line.find(end) != -1:
        matched = True
        result = [] # log until the *last* occurrence of end
      if matched:
        result.insert(0, line)
        if line.find(begin) != -1: break
    if matched:
      return result
    elif result == []:
      return 'Je ne saisis pas à quoi vous faites allusion. Essayez "help".'
    else:
      return "Je perçois bien la fin, mais n'entrevois pas le début."

if __name__ == "__main__":
  import sys, argparse, re, atexit, time, os
  from random import choice
  parser = argparse.ArgumentParser(description='Quote bot')
  parser.add_argument('--name', default='anthologger', help='name of the bot (anthologger)')
  parser.add_argument('--quote-prefix', default='quote_', help='prefix for the quote files (quote_)')
  parser.add_argument('--log-prefix', default='/tmp/log_', help='prefix for the chan log files (/tmp/log_)')
  parser.add_argument('--mem-size', default=1000, type=int, help='maximum number of messages to keep in RAM (1000)')
  parser.add_argument('--replies-file', default='replies', help='file containing the replies (replies)')
  parser.add_argument('--help-prefix', default='./', help='prefix for help files (./)')
  parser.add_argument('--max-len', default=100, type=int, help='maximum length of a quote (in lines, 100)')
  args = parser.parse_args()
  talk = sys.stdout
  irctk = re.compile('^\[(?P<chan>[^]]*)\](?P<content>.*)$')
  command = re.compile('^ <(?P<author>[^>]*)>\\s*' + args.name + '\\s*:\\s*(?P<cmd>.*)$')
  regex = re.compile('^(?P<begin>.*?)\\s*(?:\.\.\.\\s*(?P<end>.*?)\\s*)?$')
  with open(args.replies_file, 'r') as f:
    replies = f.readlines()
  chans, helps = {}, {}

  def save():
    for chan in chans:
      chans[chan].flush()
  atexit.register(save)

  for line in sys.stdin:
    infos = irctk.match(line)
    if infos is None: # Should never happen
      continue
    chan, content = infos.groups()
    # Load chan at first use
    if chan not in chans:
      chans[chan] = Logger(args.log_prefix + chan, args.mem_size, args.max_len)
      helps[chan] = []
      if os.path.exists(args.help_prefix + chan):
        with open(args.help_prefix + chan, 'r') as f:
          helps[chan] = f.readlines()

    cmdinfos = command.match(content)
    if cmdinfos is None:
      chans[chan].log('%d [%s] %s' % (time.time(), chan, content))
    else:
      author, cmd = cmdinfos.groups()
      if cmd.strip() == 'help':
        talk.writelines('[' + chan + ']' + line + '\n' for line in helps[chan])
        talk.flush()
      else:
        begin, end = regex.match(cmd).groups()
        res = chans[chan].find(begin, end)
        if type(res) == list:
          with open(args.quote_prefix + chan, 'a') as f:
            f.writelines(res + ['\n'])
          talk.write('[' + chan + '] ' + choice(replies))
          talk.flush()
        else:
          talk.write('[' + chan + '] ' + res + '\n')
          talk.flush()
