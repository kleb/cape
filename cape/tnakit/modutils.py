#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
%(hline_after-)s
%(mod)s: Module Documentation Utilities
%(hline=)s


    %(submodules)s

"""

# Standard library modules
import glob
import os
import re

# Local modules
from . import rstutils
from . import typeutils


# Get three groups for each match:
#    * indent: leading white space
#    * key: name, main required part
#    * char: single character modifier at the end for \hline
_re_indent = r"(?P<indent>^[ ]+)?"
_re_keyval = r"%\((?P<key>\w+)(?P<char>[=*+^-]?)\)s"
# Combined regular expression to find replacement macros
regex_repl = re.compile(_re_indent + _re_keyval)


# Modify docstring
def rst_docstring(modname, modfile, doc, meta=None, **kw):
    r"""Modify a docstring with automatic expansions

    :Call:
        >>> txt = rst_docstring(doc, meta=None, **kw)
    :Inputs:
        *doc*: :class:`str`
            Raw docstring with macros to expande
    :Versions:
        * 2019-12-27 ``@ddalle``: First version
    """
    # Initialize text
    lines_out = []
    # Global replacements
    opts = {}
    # Split docstring into lines
    # (have to do this beforehand because of pesky *hline_after*)
    lines = doc.split("\n")
    # Flag for *hline_after*
    waiting_hline = False
    # Loop through docstring lines
    for (i, line) in enumerate(lines):
        # Get matches
        matches = regex_repl.findall(line)
        # Count matches
        n_match = len(matches)
        # Initialize dictionary of expansions
        fmt = {}
        # Flags
        broken_line = False
        # Loop through matches
        for (tab, key, char) in matches:
            # Check indentation level
            indent = len(tab)
            # Check for hard-coded expansions
            if key == "hline_after":
                # "hlines" must be the whole line
                if n_match > 1:
                    # Just get out of here
                    broken_line = True
                    break
                # Have to wait until following line has been expanded
                waiting_hline = True
                waiting_line = line.rstrip()
                waiting_char = char
            elif key == "hline":
                # "hlines" must be the whole line
                if n_match > 1:
                    # Just get out of here
                    broken_line = True
                    break
                # Replaced text
                txt_in = r"%%(hline%s)s" % char
                # Replacement text
                if char == '':
                    # Use default character of '-'
                    txt_out = '-' * len(lines_out[-1])
                else:
                    # Use specified character
                    txt_out = char * len(lines_out[-1])
                # Replace the text
                line = line.replace(txt_in, txt_out)
            elif key in kw:
                # Format something specified in the keywords
                v = kw[key]
                # Check type
                if typeutils.isstr(v):
                    # Already a string
                    fmt[key] = v
                else:
                    # Convert to string
                    fmt[key] = rstutils.py2rst(v, indent=indent).lstrip()
            elif key == "meta":
                # Check type
                if typeutils.isstr(meta):
                    # Already formatted
                    fmt["meta"] = meta
                elif isinstance(meta, dict):
                    # Convert to :class:`dict` to reST text
                    curtxt = rstutils.py2rst(meta, indent=indent)
                    # Save to dictionary
                    fmt["meta"] = curtxt.lstrip()
                else:
                    # Broken or empty metadata
                    fmt["meta"] = ""
            elif key == "submodules":
                # Specific options
                kw_submod = {
                    "maxdepth": kw.get("maxdepth", 2),
                    "indent": indent,
                    "tab": kw.get("tab", 4),
                }
                # Create list of submodules
                curtxt = rst_submodules(modfile, **kw_submod)
                # Save to dictionary
                fmt["submodules"] = curtxt.lstrip()
            elif key == "mod":
                # Module name with reST markup
                fmt[key] = ":mod:`%s`" % modname
            elif key == "pymod":
                # Module name without markup
                fmt[key] = modname
            elif key == "file":
                # Module file (just last part)
                fmt[key] = os.path.split(modfile)[-1]
            elif key == "absfile":
                # Whole file path
                fmt[key] = os.path.abspath(modfile)
            elif key == "relative_file":
                # Get extension
                fext = modfile.split(".")[-1]
                # Use module name
                fmt[key] = modname.replace(".", os.sep) + "." + fext
            else:
                # Broken line
                broken_line = True
                break
                    
        # Check for substitutions
        if n_match == 0:
            # Just strip
            line = line.rstrip()
        elif broken_line:
            # Something didn't work out; don't raise exception
            line = line.rstrip()
        elif key == "hline_after":
            # Don't save yet
            continue
        else:
            # Apply formatting
            line = line % fmt
            # Strip each line (necessary if *fmt* puts '\n's in)
            line = "\n".join([li.rstrip() for li in line.split("\n")])
        # Final processing
        if waiting_hline:
            # Replaced text from preceding line
            txt_in = r"%%(hline_after%s)s" % waiting_char
            # Replacement text
            if waiting_char == '':
                # Use default character of '-'
                txt_out = '-' * len(lines_out[-1])
            else:
                # Use specified character
                txt_out = waiting_char * len(line)
            # Replace the text and add to the list
            lines_out.append(waiting_line.replace(txt_in, txt_out))
            # Turn off preceding hline flag
            waiting_hline = False
        # Append the line
        lines_out.append(line)
    # Combine lines (append newline)
    txt = "\n".join(lines_out)
    # End with exactly one blank line
    txt = txt.rstrip("\n") + "\n"
    # Output
    return txt


# List modules
def rst_submodules(fname, indent=4, maxdepth=2, tab=4, depth=0, prefix=""):
    r"""Create a bullet list of submodules from folder of *fname*
    
    :Call:
        >>> txt = rst_submodules(fname, indent=4, maxdepth=2, tab=4)
    :Inputs:
        *fname*: :class:`str`
            Name of (Python module) file from which list is started
        *indent*: {``4``} | :class:`int` > 0
            Number of white spaces at the beginning of line
        *maxdepth*: {``2``} | ``None`` | :class:`int` >= 0
            Maximum number of sublevels
        *tab*: {``4``} | :class:`int` > 0
            Number of additional spaces in an indentation
        *depth*: {``0``} | :class:`int` >= 0
            Current depth level (for recursion)
        *prefix*: {``""``} | :class:`str`
            Prefix to add to each module's name (mostly for recursion)
    :Outputs:
        *txt*: :class:`str`
            RST-formatted outline
    :Versions:
        * 2018-07-03 ``@ddalle``: First version
        * 2019-12-27 ``@ddalle``: Split part to :func:`list_modules`
    """
    # Text conversion function for recursion
    def modlist_bullets(modlist, idepth, prefix):
        # Initialize text
        txt = ""
        # Prefix for next depth
        prefixj = prefix
        # Loop through modules
        for modname in modlist:
            # Check type
            if isinstance(modname, list):
                # Recurse
                txt += modlist_bullets(modname, idepth+1, prefixj)
                continue
            # Get bullet
            if idepth % 2:
                # Odd depth: -
                bullet = '-'
            else:
                # Even depth: *
                bullet = '*'
            # Indentation
            line = " " * (indent + idepth*tab)
            # Text
            line += "%s :mod:`%s%s`\n" % (bullet, prefix, modname)
            # Save text
            txt += line
            # Prefix in case this module has submodules
            prefixj = prefix + modname + "."
        # Output
        return txt
        
    # Get modules
    modlist = list_modules(fname, maxdepth=maxdepth, depth=depth)
    # Form list
    txt = modlist_bullets(modlist, 0, prefix)
    # Remove final newline character
    return txt.rstrip("\n")


# Find modules
def list_modules(fname, maxdepth=2, depth=0):
    r"""Create a list of lists of submodules from *fname*

    :Call:
        >>> modlist = list_modules(fname, maxdepth=2, depth=0)
    :Inputs:
        *fname*: :class:`str`
            Name of (Python module) file from which list is started
        *maxdepth*: {``2``} | ``None`` | :class:`int` >= 0
            Maximum number of sublevels
        *depth*: {``0``} | :class:`int` >= 0
            Current depth
    :Outputs:
        *modlist*: :class:`list`\ [:class:`str` | :class:`list`]
            Recursive list of module names
    :Versions:
        * 2019-12-27 ``@ddalle``: First version
    """
    # Initialize list
    modlist = []
    # Ensure full path of *fname*
    fname = os.path.abspath(fname)
    # Separate out folder part
    fdir = os.path.dirname(fname)
    # Perform split
    fpth, fmod = os.path.split(fname)
    # Check for broken situation
    if (fpth == fdir) and (fmod not in ["__init__.py", "__init__.pyc"]):
        # Wrong type of module or not a module at all
        return modlist

    # Name of the current module
    fmod = os.path.split(fdir)[-1]

    # Get folder
    fglob = os.listdir(fdir)
    # Sort them (ASCII order)
    fglob.sort()
    # Check for folder without "__init__.py"
    if (fpth != fdir) and ("__init__.py" not in fglob):
        return modlist

    # Loop through ".py" folders
    for fn in fglob:
        # Check for extension
        if "." not in fn:
            continue
        # Split extension
        fmod, fext = fn.split(".", 1)
        # Check if it is a "*.py"
        if fext not in ["py", "so"]:
            continue
        # Check for "__init__.py" (handled as special case)
        if fmod == "__init__":
            continue
        # Append module to the list
        modlist.append(fmod)

    # Loop through subfolders
    for fn in fglob:
        # Full name
        fa = os.path.join(fdir, fn)
        # Check if it's a folder
        if not os.path.isdir(fa):
            continue
        # Construct name of __init__.py definition
        fi = os.path.join(fa, "__init__.py")
        # Check if the folder contains an initialization
        if not os.path.isfile(fi):
            continue
        # Append to the module list
        modlist.append(fn)
        # Check depth limits
        if (maxdepth is None):
            # Unlimited depth
            if depth > 8:
                # Ok, 8 levels is too many
                continue
        elif depth+1 > maxdepth:
            # Hit depth limit
            continue
        # Recurse
        modlisti = list_modules(fi, maxdepth=maxdepth, depth=depth+1)
        # Add if there's anything there
        if len(modlist) > 0:
            modlist.append(modlisti)

    # Output
    return modlist
