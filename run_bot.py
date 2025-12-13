#!/usr/bin/env python3
"""
Simple runner script for the refactored forecasting bot.

This provides an easy entry point to run the bot without needing to use
the -m flag.
"""
import asyncio
import sys

# Add src to path
sys.path.insert(0, '.')

from src.main import main

if __name__ == "__main__":
    asyncio.run(main())
