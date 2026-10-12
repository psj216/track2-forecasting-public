"""## Executive summary (read this first)
Preserve the published forecast verb and arguments, with no dynamic shell evaluation.
"""
import sys
from .cli import main
args=sys.argv[1:]
if args and args[0]=='forecast':args=args[1:]
raise SystemExit(main(args))
