"""Subprocess inference entry point; stdout contains only the generated prompt."""
import argparse
import json
import sys
from pipeline import infer

parser = argparse.ArgumentParser()
parser.add_argument("--model", required=True)
args = parser.parse_args()
print(infer(json.load(sys.stdin), args.model))
