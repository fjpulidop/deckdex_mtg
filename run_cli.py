#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to run the interactive command line interface for DeckDex MTG
"""

import sys
import os

try:
    from cli_interactive import DeckDexCLI
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you are in the project root directory.")
    sys.exit(1)

def main():
    """Main function to run the application"""
    try:
        cli = DeckDexCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\nProgram terminated by user.")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 