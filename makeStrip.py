#! /usr/bin/env python3

"""python program to solve the world problems..."""

import os, sys, string, time, logging, argparse

import PIL
import PIL.Image
import PIL.ImageDraw

_version = "0.1"

def start(args):
  size = (150, 768)
  margin = 10

  dest = PIL.Image.new("RGBA", size)

  draw = PIL.ImageDraw.Draw(dest)

  #draw.rectangle((0, 0, size[0], size[1]), "white")

  draw.rectangle((0, 0, margin, size[1]), "black")
  draw.rectangle((size[0]-margin, 0, size[0], size[1]), "black")

  if 1:
    w = size[0]-55
    dy = (size[1]/len(args.files))
    
    for n,fn in enumerate(args.files):
      i = PIL.Image.open(fn)
      ratio = (i.size[0]/i.size[1])
      h = w / ratio

      i = i.resize((int(w),int(h)), PIL.Image.BICUBIC)
      x = (size[0]/2) - (i.size[0] / 2)
      y = (n * dy + dy/2) - (i.size[1]/2)

      dest.paste(i, (int(x), int(y)))

  print (args.dest)
  dest.save(args.dest, "PNG")

def test():
  logging.warn("Testing")

def parse_args(argv):
  parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description=__doc__)

  parser.add_argument("-t", "--test", dest="test_flag", 
                    default=False,
                    action="store_true",
                    help="Run test function")
  parser.add_argument("--log-level", type=str,
                      choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                      help="Desired console log level")
  parser.add_argument("-d", "--debug", dest="log_level", action="store_const",
                      const="DEBUG",
                      help="Activate debugging")
  parser.add_argument("-q", "--quiet", dest="log_level", action="store_const",
                      const="CRITICAL",
                      help="Quite mode")
  parser.add_argument("-o", "--dest", dest="dest", type=str)
  parser.add_argument("files", type=str, nargs='+')

  args = parser.parse_args(argv[1:])

  return parser, args

def main(argv, stdout, environ):
  if sys.version_info < (3, 0): reload(sys); sys.setdefaultencoding('utf8')

  parser, args = parse_args(argv)

  logging.basicConfig(format="[%(asctime)s] %(levelname)-8s %(message)s", 
                    datefmt="%m/%d %H:%M:%S", level=args.log_level)

  if args.test_flag:  test();   return

  start(args)

if __name__ == "__main__":
  main(sys.argv, sys.stdout, os.environ)
