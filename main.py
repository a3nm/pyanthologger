""" Ici le super message d'aide d'a3nm
"""

class Logger:
  def __init__(self, log_file, mem_size):
    self.f = log_file
    self.mem = []
    self.MAX_MEM_SIZE = mem_size

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
    if size is None: size = 0
    with open(self.f, 'a') as f:
      f.writelines(self.mem[:size])
    self.mem = self.mem[size:]

  def find_quote(self, begin, end=None):
    if end is None: end = begin
    result, matched = [], False
    for line in self:
      if line.find(begin) != -1: matched = True
      if matched:
        result.insert(0, line)
        if line.find(end) != -1: break
    if matched:
      return result
    elif result == []:
      return 'Je ne saisis pas à quoi vous faites allusion. Essayez "help".'
    else:
      return "Je perçois bien la fin, mais n'entrevois pas le début."

if __name__ == "__main__":
  import sys, argparse, re, atexit, time
  from random import choice
  parser = argparse.ArgumentParser(description='Quote bot')
  parser.add_argument('--name', default='anthologger', help='name of the bot (anthologger)')
  parser.add_argument('--quote-prefix', default='quote_', help='prefix for the quote files (quote_)')
  parser.add_argument('--log-prefix', default='/tmp/log_', help='prefix for the chan log files (/tmp/log_)')
  parser.add_argument('--mem-size', default=1000, type=int, help='maximum number of messages to keep in RAM (1000)')
  parser.add_argument('--replies-file', help='file containing the replies', required=True)
  args = parser.parse_args()
  talk = sys.stdout
  irctk = re.compile('^\[(?P<chan>[^]]*)\] <(?P<author>[^>]*)> (?:(?:' + args.name + ':\\s*(?P<cmd>.*))|(?P<msg>.*))$')
  regex = re.compile('^(?P<begin>.*?)\\s*(?:\.\.\.\\s*(?P<end>.*?)\\s*)?$')
  with open(args.replies_file, 'r') as f:
    replies = f.readlines()
  chans = {}

  def save():
    for chan in chans:
      chans[chan].flush()
  atexit.register(save)

  for line in sys.stdin:
    infos = irctk.match(line)
    if infos is None: # Should never happen
      continue
    chan, author, cmd, msg = infos.groups()
    if chan not in chans:
      chans[chan] = Logger(args.log_prefix + chan, args.mem_size)
    if cmd is None: # Message
      chans[chan].log('%d [%s] <%s> %s' % (time.time(), chan, author, msg))
    elif cmd.strip() == 'help':
      talk.writelines('[' + chan + '] ' + line + '\n' for line in __doc__.split())
    else:
      begin, end = regex.match(cmd).groups()
      res = chans[chan].find_quote(begin, end)
      if type(res) == list:
        with open(args.quote_prefix + chan, 'a') as f:
          f.writelines(res + ['\n'])
        talk.write('[' + chan + '] ' + choice(replies))
      else:
        talk.write('[' + chan + '] ' + res + '\n')