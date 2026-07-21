#!/usr/bin/env python3
"""Run the current encrypted public-only versus private-mandate benchmark.

Kept as the conventional evaluation entry point. The benchmark itself lives in
compare_examples.py so `make compare` and `make evaluate` cannot drift apart.
"""
from compare_examples import main


if __name__ == "__main__":
    main()
