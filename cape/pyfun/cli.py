#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
:mod:`cape.pyfun.cli`: Interface to ``pyfun`` executable
===========================================================

This module provides the Python function :func:`main`, which is
executed whenever ``pyfun`` is used.
"""

# Standard library modules
import sys

# CAPE modules
from .. import argread
from .. import text as textutils
from .cntl import Cntl
from .cli_doc import PYFUN_HELP


# Primary interface
def main():
    r"""Main interface to ``pyfun``

    This turns ``sys.argv`` into Python arguments and calls
    :func:`cape.pyfun.cntl.Cntl.cli`. 

    :Call:
        >>> main()
    :Versions:
        * 2021-03-03 ``@ddalle``: Version 1.0
    """
    # Parse inputs
    a, kw = argread.readflagstar(sys.argv)
    
    # Check for a help flag
    if kw.get('h') or kw.get("help"):
        # Display help
        print(textutils.markdown(PYFUN_HELP))
        return
        
    # Get file name
    fname = kw.get('f', "pyFun.json")
    
    # Try to read it
    cntl = Cntl(fname)
    
    # Call the command-line interface
    cntl.cli(*a, **kw)


# Check if run as a script.
if __name__ == "__main__":
    main()

