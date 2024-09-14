r"""
:mod:`cape.cfdx.archivist`: File archiving and clean-up for cases
===================================================================

This module provides the class :mod:`CaseArchivist`, which conducts the
operations of commands such as

.. code-block:: bash

    pyfun --archive
    pycart --clean
    pyover --skeleton
"""

# Standard library
import glob
import os
import re
import shutil
import sys
from collections import defaultdict
from typing import Optional, Union

# Local imports
from .caseutils import run_rootdir
from .logger import ArchivistLogger
from .options.archiveopts import ArchiveOpts
from .tarcmd import tar, untar
from ..optdict import INT_TYPES


# Known safety levels
SAFETY_LEVELS = (
    "none",
    "status",
    "report",
    "restart",
)


# Class definition
class CaseArchivist(object):
    r"""Class to archive a single CFD case

    :Call:
        >>> a = CaseArchivist(opts, where=None, casename=None)
    :Inputs:
        *opts*: :class:`ArchiveOpts`
            Case archiving options
        *where*: {``None``} | :class:`str`
            Root of CFD case folder (default: CWD)
        *casename*: {``None``} | :class:`str`
            Name of CFD case folder (default: last two levels of CWD)
    """
   # --- Class attributes ---
    # Class attributes
    __slots__ = (
        "archivedir",
        "casename",
        "logger",
        "opts",
        "root_dir",
        "_deleted_files",
        "_kept_files",
        "_safety",
        "_size",
        "_restart_files",
        "_report_files",
        "_test",
    )

    # List of file name patterns to protect
    _protected_files = (
        "case.json",
        "run.[0-9][0-9]+.[0-9]+",
    )

   # --- __dunder__ ---
    def __init__(
            self,
            opts: ArchiveOpts,
            where: Optional[str] = None,
            casename: Optional[str] = None):
        r"""Initialization method

        :Versions:
            * 2024-09-04 ``@ddalle``: v1.0
        """
        # Initialize slots
        self._reset_slots()
        # Save root dir
        if where is None:
            # Use current dir
            self.root_dir = os.getcwd()
        else:
            # User-specified
            self.root_dir = where
        # Default casename
        if casename is None:
            # Use two-levels of parent
            frun = os.path.basename(self.root_dir)
            fgrp = os.path.basename(frun)
            casename = f"{fgrp}/{frun}"
        # Save case name
        self.casename = casename
        # Save p[topms
        self.opts = opts
        # Get archive dir (absolute)
        self.archivedir = os.path.abspath(opts.get_ArchiveFolder())

   # --- General actions ---
    # Begin a general action
    def begin(self, safety: str = "archive", test: bool = False):
        # Enxure a valid input for safety level
        _validate_safety_level(safety)
        # Set safety level and test opiton
        self._test = test
        self._safety = safety
        # Test if archive exists
        self.assert_archive()
        # Make folder
        self.make_case_archivedir(test)
        # Reset size
        self._size = 0
        # Renew list of deleted files
        self._deleted_files = []

    # Delete local files
    def delete_files(self, matchdict: dict, n: int):
        # Loop through matches
        for grp, mtchs in matchdict.items():
            # Split into files to delete and files to keep
            if n == 0:
                # Delete all files
                rmfiles = mtchs[:]
                keepfiles = []
            else:
                # Delete up to last *n* files
                rmfiles = mtchs[:-n]
                keepfiles = mtchs[-n:]
            # Delete up to last *n* files
            for filename in rmfiles:
                self.delete_file(filename)
            # Keep the last *n* files
            for filename in keepfiles:
                self.keep_file(filename)

    # Delete a single file
    def delete_file(self, filename: str):
        r"""Delete a single file if allowed; log results

        :Call:
            >>> a.delete_file(filename)
        :Inputs:
            *a*: :class:`CaseArchiver`
                Archive controller for one case
            *filename*: :class:`str`
                Name of file to delete
        :Versions:
            * 2024-09-13 ``@ddalle``: v1.0
        """
        # Check if it's a folder or gone
        if os.path.isdir(filename):
            self.warn(f"cannot rm: '{filename}' is a folder")
            return
        elif not os.path.isfile(filename):
            self.warn(f"cannot rm: '{filename}' does not exist")
            return
        # Add to size
        self._size += getsize(filename)
        # Check against file lists...
        if self.check_safety(filename):
            # Generate message
            msg = f"rm '{filename}'"
            # Log it
            self.log(msg, parent=2)
            print(f"  {msg}")
            # Actual deletion (if no --test option)
            if not self._test:
                os.remove(filename)

    # Keep file
    def keep_file(self, filename: str):
        r"""Keep a file and log the action

        :Call:
            >>> a.keep_file(filename)
        :Inputs:
            *a*: :class:`CaseArchiver`
                Archive controller for one case
            *filename*: :class:`str`
                Name of file to protect
        :Versions:
            * 2024-09-13 ``@ddalle``: v1.0
        """
        # Status message
        self.log(f"  keep '{filename}'", parent=1)
        # Add to current list
        self._kept_files.append(filename)

   # --- Data ---
    # Reset all instance attributes
    def _reset_slots(self):
        # Reset counters, etc.
        self._size = 0
        self._deleted_files = []
        self._kept_files = []
        self._restart_files = []
        self._report_files = []
        # Set quick options
        self._test = False
        self._safety = "archive"

    # Check if it's safe to delete *filename*
    def check_safety(self, filename: str) -> bool:
        r"""Check if it's safe to delete a file using current settings

        This function will check *a._safety* for the current safety
        level. It will also log a warning with the reason if it's
        unsafe to delete.

        :Call:
            >>> q = a.check_safety(filename)
        :Inputs:
            *a*: :class:`CaseArchiver`
                Archive controller for one case
            *filename*: :class:`str`
                Name of prospective file/folder to delete
        :Outputs:
            *q*: :class:`bool`
                Whether it's safe to delete *a*
        :Versions:
            * 2024-09-13 ``@ddalle``: v1.0
        """
        def _genr8_msg(submsg: str) -> str:
            return f"skipping '{filename}'; safety={self._safety}; {submsg}"
        # Unpack safety level
        safety = self._safety
        # Check safety level
        if safety == "none":
            # No checks
            return True
        # Get class
        cls = self.__class__
        # Check against protected files
        if match_pats(filename, cls._protected_files):
            self.warn(_genr8_msg("protected file"))
            return False
        # Check against already protected files
        if filename in self._kept_files:
            self.warn(_genr8_msg("previously kept file"))
            return False
        # Check safety level
        if safety == "status":
            return True
        # Check against report files
        if filename in self._report_files:
            self.warn(_genr8_msg("required for reports"))
            return False
        # Check safety level
        if safety == "report":
            return True
        # Check against restart files
        if filename in self._restart_files:
            self.warn(_genr8_msg("required for restart"))
        # All checks passed
        return True

   # --- File actions ---
    # Copy one file to archive
    def archive_file(self, fname: str, parent: int = 0):
        r"""Copy a file to the archive

        :Call:
            >>> a.archive_file(fname, parent=1)
        :Inputs:
            *a*: :class:`CaseArchiver`
                Archive controller for one case
            *fname*: :class:`str`
                Name of file to copy
            *parent*: {``0``} | :class:`int`
                Additional depth of function name in log
        :Versions:
            * 2024-09-04 ``@ddalle``: v1.0
        """
        # Archive folder
        adir = self.get_archivedir()
        # Status update
        msg = f"{fname} --> ARCHIVE/{fname}"
        print(f'  {msg}')
        # Log message
        self.log(msg, parent=parent)
        # Copy file
        shutil.copy(fname, os.path.join(adir, fname))

    # Delete a file
    def remove_local(self, fname: str, parent: int = 1):
        r"""Delete a local file

        :Call:
            >>> a.remove_local(fname, parent=1)
        :Inputs:
            *a*: :class:`CaseArchiver`
                Archive controller for one case
            *fname*: :class:`str`
                Name of file to delete
            *parent*: {``0``} | :class:`int`
                Additional depth of function name in log
        :Versions:
            * 2024-09-12 ``@ddalle``: v1.0
        """
        # Absolutize
        fabs = self.abspath_local(fname)
        # Check if file exists
        if not os.path.isfile(fname):
            return
        # Status update
        msg = f"rm '{fname}'"
        print(f'  {msg}')
        # Log message
        self.log(msg, parent=parent)
        # Delete file
        os.remove(fabs)

    # Delete a local folder
    def rmtree_local(self, fdir: str, parent: int = 1):
        r"""Delete a local folder (recursively)

        :Call:
            >>> a.rmtree_local(fdir, parent=1)
        :Inputs:
            *a*: :class:`CaseArchiver`
                Archive controller for one case
            *fdir*: :class:`str`
                Name of folder to delete
            *parent*: {``0``} | :class:`int`
                Additional depth of function name in log
        :Versions:
            * 2024-09-12 ``@ddalle``: v1.0
        """
        # Absolutize
        fabs = self.abspath_local(fdir)
        # Check if file exists
        if not os.path.isdir(fdir):
            return
        # Status update
        msg = f"rm -r '{fdir}'"
        print(f'  {msg}')
        # Log message
        self.log(msg, parent=parent)
        # Delete file
        shutil.rmtree(fabs)

    # Create a single tar file
    def _tar(self, ftar: str, *a):
        # Get archive format
        fmt = self.opts.get_opt("ArchiveFormat")
        # Create tar
        tar(ftar, *a, fmt=fmt, wc=False)

    # Untar a tarfile
    def _untar(self, ftar: str):
        # Get archive format
        fmt = self.opts.get_opt("ArchiveFormat")
        # Unpack
        untar(ftar, fmt=fmt, wc=False)

   # --- File search ---
    def save_reportfiles(self, searchopt: dict):
        r"""Save list of files to protect for ``"report"`` option

        The idea is to generate and save a list of files that presently
        appear to be required in order to restart the case without
        unarchiving.

        :Call:
            >>> a.save_reportfiles(searchopt)
        :Inputs:
            *a*: :class:`CaseArchiver`
                Archive controller for one case
            *searchopt*: :class:`dict`
                Key is the regular expression (or glob), value is the
                number of files to protect that match the pattern
        :Versions:
            * 2024-09-13 ``@ddalle``: v1.0
        """
        self._report_files = self.find_keepfiles(searchopt)

    def save_restartfiles(self, searchopt: dict):
        r"""Save list of files to protect for ``"restart"`` option

        The idea is to generate and save a list of files that presently
        appear to be required in order to restart the case without
        unarchiving.

        :Call:
            >>> a.save_restartfiles(searchopt)
        :Inputs:
            *a*: :class:`CaseArchiver`
                Archive controller for one case
            *searchopt*: :class:`dict`
                Key is the regular expression (or glob), value is the
                number of files to protect that match the pattern
        :Versions:
            * 2024-09-13 ``@ddalle``: v1.0
        """
        self._restart_files = self.find_keepfiles(searchopt)

    @run_rootdir
    def find_keepfiles(self, searchopt: dict) -> list:
        r"""Generate list of files to keep based on a search option

        :Call:
            >>> a.find_keepfiles(searchopt)
        :Inputs:
            *a*: :class:`CaseArchiver`
                Archive controller for one case
            *searchopt*: :class:`dict`
                Key is the regular expression (or glob), value is the
                number of files to protect that match the pattern
        :Outputs:
            *mtches*: :class:`list`\ [:class:`str`]
                List of files [and folders] to protect
        :Versions:
            * 2024-09-13 ``@ddalle``: v1.0
        """
        # Initialize list of matches
        mtches = []
        # Loop through options
        for pat, n in searchopt.items():
            # Skip if n==0
            if n == 0:
                continue
            # Perform search
            matchdict = self.search(pat)
            # Loop through groups (just one key if no groups)
            for grpmatch in matchdict.values():
                # Add items to protected list
                if n < 0:
                    mtches.extend(grpmatch)
                else:
                    mtches.extend(grpmatch[-n:])
        # Output
        return mtches

    @run_rootdir
    def search(self, pat: str) -> dict:
        r"""Search case folder for files matching a given pattern

        :Call:
            >>> matchdict = a.search(pat)
        :Inputs:
            *a*: :class:`CaseArchiver`
                Archive controller for one case
            *pat*: :class:`str`
                Regular expression pattern
        :Outputs:
            *matchdict*: :class:`dict`\ [:class:`list`]
                Mapping of files matching *pat* keyed by identifier for
                the groups in *pat*
            *matchdict[lbl]*: :class:`list`\ [:class:`str`]
                List of files matching *pat* with group values
                in  *lbl*, sorted by ascending modification time
        """
        # Get search method
        method = self.opts.get_opt("SearchMethod", vdef="glob")
        # Check which search method we'll be using
        if method == "glob":
            # Use regular glob.glob()
            matchdict = {'': glob.glob(pat)}
        else:
            # Search by regular expression, and separate by grp vals
            matchdict = rematch(pat)
        # Sort each value by *mtime*
        for grp, matches in matchdict.items():
            # Sort by ascending modification time
            matchdict[grp] = sorted(matches, key=_safe_mtime)
        # Output
        return matchdict

   # --- Archive home ---
    # Ensure root of target archive exists
    def assert_archive(self):
        r"""Raise an exception if archive root does not exist

        :Call:
            >>> a.assert_archive()
        :Inputs:
            *a*: :class:`CaseArchiver`
                Archive controller for one case
        :Raises:
            :class:`FileNotFoundError` if *a.archivedir* does not exist
        :Versions:
            * 2024-09-04 ``@ddalle``: v1.0
        """
        # Check for "phantom"
        if self._test:
            return
        # Make sure archive root folder exists:
        if not os.path.isdir(self.archivedir):
            raise FileNotFoundError(
                "Cannot archive because archive\n" +
                f"  '{self.archivedir}' not found")

    # Make folders as needed for case
    def make_case_archivedir(self):
        r"""Create the case archive folder if needed

        :Call:
            >>> a.make_case_archivedir()
        :Inputs:
            *a*: :class:`CaseArchiver`
                Archive controller for one case
        :Versions:
            * 2024-09-04 ``@ddalle``: v1.0
        """
        # Check for "phantom"
        if self._test:
            return
        # Get full/partial type
        atype = self.opts.get_ArchiveType()
        # Split case name into parts
        caseparts = self.casename.split('/')
        # If full archive, don't create last level
        if atype == "full":
            caseparts.pop(-1)
        # Build up case archive dir, starting from archive root
        fullpath = self.archivedir
        # Loop through group folder(s)
        for part in caseparts:
            # Append
            fullpath = os.path.join(fullpath, part)
            # Create folder
            if not os.path.isdir(fullpath):
                # Log action
                self.log(f"mkdir {_posix(fullpath)}")
                # Create folder
                os.mkdir(fullpath)

    # Absolute path to file in archive folder
    def abspath_archive(self, fname: str) -> str:
        r"""Return absolute path to a file within archive folder

        :Call:
            >>> fabs = a.abspath_archive(fname)
        :Inputs:
            *a*: :class:`CaseArchiver`
                Archive controller for one case
            *fname*: :class:`str`
                Relative path to a file
        :Outputs:
            *fabs*: :class:`str`
                Absolute path
        :Versions:
            * 2024-09-12 ``@ddalle``: v1.0
        """
        # Make sure we don't have an absolute path
        _assert_relpath(fname)
        # Absolutize
        return os.path.join(self.archivedir, self.casename, fname)

    # Absolute path to file in local folder
    def abspath_local(self, fname: str) -> str:
        r"""Return absolute path to a file within local case folder

        :Call:
            >>> fabs = a.abspath_local(fname)
        :Inputs:
            *a*: :class:`CaseArchiver`
                Archive controller for one case
            *fname*: :class:`str`
                Relative path to a file
        :Outputs:
            *fabs*: :class:`str`
                Absolute path
        :Versions:
            * 2024-09-12 ``@ddalle``: v1.0
        """
        # Make sure we don't have an absolute path
        _assert_relpath(fname)
        # Absolutize
        return os.path.join(self.root_dir, fname)

   # --- Logging ---
    def log(
            self,
            msg: str,
            title: Optional[str] = None,
            parent: int = 0):
        r"""Write a message to primary log

        :Call:
            >>> a.log(msg, title, parent=0)
        :Inputs:
            *a*: :class:`CaseArchiver`
                Archive controller for one case
            *msg*: :class:`str`
                Primary content of message
            *title*: {``None``} | :class:`str`
                Manual title (default is name of calling function)
            *parent*: {``0``} | :class:`int`
                Extra levels to use for calling function name
        :Versions:
            * 2024-08-29 ``@ddalle``: v1.0
        """
        # Name of calling function
        funcname = self.get_funcname(parent + 2)
        # Check for manual title
        title = funcname if title is None else title
        # Get logger
        logger = self.get_logger()
        # Log the message
        logger.log_main(title, msg)

    def warn(
            self,
            msg: str,
            title: Optional[str] = None,
            parent: int = 0):
        r"""Write a message to verbose log

        :Call:
            >>> runner.warn(title, msg)
        :Inputs:
            *runner*: :class:`CaseRunner`
                Controller to run one case of solver
            *msg*: :class:`str`
                Primary content of message
            *title*: {``None``} | :class:`str`
                Manual title (default is name of calling function)
            *parent*: {``0``} | :class:`int`
                Extra levels to use for calling function name
        :Versions:
            * 2024-08-29 ``@ddalle``: v1.0
        """
        # Name of calling function
        funcname = self.get_funcname(parent + 2)
        # Check for manual title
        title = funcname if title is None else title
        # Get logger
        logger = self.get_logger()
        # Log the message
        logger.log_warning(title, msg)

    def get_logger(self) -> ArchivistLogger:
        r"""Get or create logger instance

        :Call:
            >>> logger = runner.get_logger()
        :Inputs:
            *runner*: :class:`CaseRunner`
                Controller to run one case of solver
        :Outputs:
            *logger*: :class:`ArchivistLogger`
                Logger instance
        :Versions:
            * 2024-08-29 ``@ddalle``: v1.0
        """
        # Initialize if it's None
        if self.logger is None:
            self.logger = ArchivistLogger(self.root_dir)
        # Output
        return self.logger

    def get_funcname(self, frame: int = 1) -> str:
        r"""Get name of calling function, mostly for log messages

        :Call:
            >>> funcname = runner.get_funcname(frame=1)
        :Inputs:
            *runner*: :class:`CaseRunner`
                Controller to run one case of solver
            *frame*: {``1``} | :class:`int`
                Depth of function to seek title of
        :Outputs:
            *funcname*: :class:`str`
                Name of calling function
        :Versions:
            * 2024-08-16 ``@ddalle``
        """
        # Get frame of function calling this one
        func = sys._getframe(frame).f_code
        # Get name
        return func.co_name


# Filter single file name against list of regexs
def match_pats(name: str, pats: list) -> bool:
    r"""Match a single file name against a list of regular expressions

    :Call:
        >>> q = match_pats(name, pats)
    :Inputs:
        *name*: :class:`str`
            Name of file or other string to test
        *pats*: :class:`list`\ [:class:`str` | :class:`re.Pattern`]
            List of patterns or compiled regexs
    :Outputs:
        *q*: :class:`bool`
            Whether *name* matches any pattern in *pats*
    :Versions:
        * 2024-09-13 ``@ddalle``: v1.0
    """
    # Loop through patterns
    for j, pat in enumerate(pats):
        # Check if string
        if isinstance(pat, str):
            # Compile it
            regex = re.compile(pat)
            # Save compiled version in place
            pats[j] = regex
        else:
            # Use as-is
            regex = pat
        # Check for match
        if regex.fullmatch(name):
            return True
    # No matches
    return False


# Search for file/folders matching regex, sorting by group
def rematch(pat: str) -> dict:
    r"""Search for file and folder names matching regular expression

    If the regex contains groups (parentheses), the results are grouped
    by the values of those groups. If the regex does not contain groups,
    the results are all in a single group called ``''``.

    :Call:
        >>> matchdict = rematch(pat)
    :Inputs:
        *pat*: :class:`str`
            Regular expression pattern
    :Outputs:
        *matchdict*: :class:`dict`\ [:class:`list`]
            Mapping of files matching *pat* keyed by identifier for the
            groups in *pat*
        *matchdict[lbl]*: :class:`list`\ [:class:`str`]
            List of files matching *pat* with group values identified in
            *lbl*
    :Versions:
        * 2024-09-02 ``@ddalle``: v1.0
    """
    # Split into parts
    pats = pat.split(os.sep)
    # Compile full regex
    regex = re.compile(pat)
    # Construct cumulative patterns (by folder depth level)
    fullpat = ""
    regexs = []
    cumpats = []
    for subpat in pats:
        # Combine path so far
        fullpat = os.path.join(fullpat, subpat)
        # Save it
        regexs.append(re.compile(subpat))
        cumpats.append(fullpat)
    # Get depth
    maxdepth = len(pats) - 1
    # Initialize matches
    matchdict = defaultdict(list)
    # Walk through file tree
    for root, dirnames, filenames in os.walk('.'):
        # Get depth
        depth = root.count(os.sep)
        # Check if final level
        if depth == maxdepth:
            # Final level; check folders and files
            for name in dirnames + filenames:
                # Full path
                fullpath = os.path.relpath(os.path.join(root, name), '.')
                # Check against full regex
                re_match = regex.fullmatch(fullpath)
                # Skip if no match
                if re_match is None:
                    continue
                # Compile label
                lbl = _match2str(re_match)
                # Add this match
                matchdict[lbl].append(fullpath)
            # Do not continue search deeper
            dirnames.clear()
        # Get regex for sub-level
        regexj = regexs[depth]
        # Get matches
        matchesj = _refilter(dirnames, regexj)
        # Replace full list with matches
        dirnames.clear()
        dirnames.extend(matchesj)
    # Output
    return dict(matchdict)


# Search for file/folders matching regex, sorting by group
def reglob(pat: str) -> list:
    r"""Search for file and folder names matching regular expression

    This function is constructed as a regular-expression version of
    :func:`glob.glob`, but it does not work with absolute paths.

    :Call:
        >>> matchlist = reglob(pat)
    :Inputs:
        *pat*: :class:`str`
            Regular expression pattern
    :Outputs:
        *matchlist*: :class:`list`\ [:class:`str`]
            Files and folders matching regular expression *pat* relative
            to current working directory
    :Versions:
        * 2024-09-02 ``@ddalle``: v1.0
    """
    # Split into parts
    pats = pat.split(os.sep)
    # Construct cumulative patterns (by folder depth level)
    fullpat = ""
    regexs = []
    cumpats = []
    for subpat in pats:
        # Combine path so far
        fullpat = os.path.join(fullpat, subpat)
        # Save it
        regexs.append(re.compile(subpat))
        cumpats.append(fullpat)
    # Get depth
    maxdepth = len(pats) - 1
    # Initialize matches
    matches = []
    # Walk through file tree
    for root, dirnames, filenames in os.walk('.'):
        # Get depth
        depth = root.count(os.sep)
        # Get regex for sub-level
        regexj = regexs[depth]
        # Check if final level
        if depth == maxdepth:
            # Final level; check folders and files
            submatches = _refilter(dirnames + filenames, regexj)
            # Construct complete paths
            for name in submatches:
                # Full path
                fullpath = os.path.relpath(os.path.join(root, name), '.')
                matches.append(fullpath)
            # Do not continue search deeper
            dirnames.clear()
        # Get matches
        matchesj = _refilter(dirnames, regexj)
        # Replace full list with matches
        dirnames.clear()
        dirnames.extend(matchesj)
    # Output
    return matches


# Convert one of several deletion opts into common format
def expand_fileopt(rawval: Union[list, dict, str], vdef: int = 0) -> dict:
    r"""Expand *Archive* file name/list/dict to common format

    The output is a :class:`dict` where the key is the pattern of file
    names to process and the value is an :class:`int` that represents
    the number of most recent files matching that pattern to keep.

    :Call:
        >>> patdict = expand_fileopt(rawstr, vdef=0)
        >>> patdict = expand_fileopt(rawlist, vdef=0)
        >>> patdict = expand_fileopt(rawdict, vdef=0)
    :Inputs:
        *rawstr*: :class:`str`
            Pattern of file names to process
        *rawlist*: :class:`list`\ [:class:`str`]
            List of filee name patterns to process
        *rawdict*: :class:`dict`\ [:class:`int`]
            Dictionary of file name patterns to process and *n* to keep
    :Outputs:
        *patdict*: :class:`dict`\ [:class:`int`]
            File name patterns as desribed above
    :Versions:
        * 2024-09-02 ``@ddalle``: v1.0
    """
    # Check for dict
    if isinstance(rawval, dict):
        # Copy it
        optval = dict(rawval)
        # Remove any non-int
        for k, v in rawval.items():
            # Check type
            if not isinstance(v, INT_TYPES):
                optval.pop(k)
        # Output
        return optval
    # Check for string
    if isinstance(rawval, str):
        return {rawval: vdef}
    # Initialize output for list
    optval = {}
    # Loop through items of list
    for rawj in rawval:
        # Check type
        if not isinstance(rawj, (dict, str, list, tuple)):
            continue
        # Recurse
        valj = expand_fileopt(rawj)
        # Save to total dict
        optval.update(valj)
    # Output
    return optval


# Get size of file
def getsize(file_or_folder: str) -> int:
    r"""Get size of file or folder, like ``du -sh``

    :Call:
        >>> total_size = getsize(file_or_folder)
    :Inputs:
        *file_or_folder*: :class:`str`
            Name of file or folder
    :Outputs:
        *total_size*: :class:`int`
            Size of file or folder in bytes (``0`` if no such file)
    :Versions:
        * 2024-09-12 ``@ddalle``: v1.0
    """
    # Skip if no such file/folder or if it's a link
    if not os.path.exists(file_or_folder) or os.path.islink(file_or_folder):
        return 0
    # Check if file
    if os.path.isfile(file_or_folder):
        return os.path.getsize(file_or_folder)
    # Initialize total size with the small empty-folder size
    total_size = os.path.getsize(file_or_folder)
    # Loop through contents
    for fname in os.listdir(file_or_folder):
        # Absolutize
        fabs = os.path.join(file_or_folder, fname)
        # Include size thereof (may recurse)
        total_size += getsize(fabs)
    # Output
    return total_size


# Filter list by regex
def _refilter(names: list, regex) -> list:
    r"""Filter a list of strings that full-match a regex"""
    # Initialize matches
    matches = []
    # Loop through candidates
    for name in names:
        if regex.fullmatch(name):
            matches.append(name)
    # Output
    return matches


# Match with groups
def _regroup(regex, name: str) -> str:
    r"""Check if a string matches a regex and return group info

    :Call:
        >>> lbl = _regroup(regex, name)
    :Inputs:
        *regex*: :mod:`re.Pattern`
            Compiled regular expression
        *name*: :class:`str`
            String to test against *regex*
    :Outputs:
        *lbl*: :class:`str`
            String showing groups of ``regex.fullmatch(name)``
    """
    # Match
    re_match = regex.fullmatch(name)
    # Check match
    if re_match is None:
        return None
    # Convert group info to string
    return _match2str(re_match)


# Convert match groups to string
def _match2str(re_match) -> str:
    r"""Create a tag describing the groups in a regex match object

    :Call:
        >>> lbl = _match2str(re_match)
    :Inputs:
        re_match: :mod:`re.Match`
            Regex match instance
    :Outputs:
        *lbl*: :class:`str`
            String describing contents of groups in *re_match*
    """
    # Initialize string
    lbl = ""
    # Get named groups
    groups = re_match.groupdict()
    # Loop through groups
    for j, group in enumerate(re_match.groups()):
        # Check for named group
        for k, v in groups.items():
            # Check this named group
            if v == group:
                # Found match
                lblj = f"{k}='{v}'"
                break
        else:
            # No named group; use index for key
            lblj = f"{j}='{group}'"
        # Add a space if necessary
        if lbl:
            lbl += " " + lblj
        else:
            lbl += lblj
    # Output
    return lbl


# Ensure a path is not absolute
def _assert_relpath(fname: str):
    if os.path.isabs(fname):
        raise ValueError(f"Expected relative path, got '{fname}'")


# Convert path to POSIX path (\\ -> / on Windows)
def _posix(path: str) -> str:
    return path.replace(os.sep, '/')


# Get mtime, but return 0 if file was deleted
def _safe_mtime(fname: str) -> float:
    return 0.0 if not os.path.isfile(fname) else os.path.getmtime(fname)


# Validate name of safety level
def _validate_safety_level(safety: str):
    if safety not in SAFETY_LEVELS:
        raise ValueError(
            f"Unrecognized safety level '{safety}'; known options are " +
            " | ".join(SAFETY_LEVELS))
