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
import math
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

   # --- Top-level archive actions ---
    def run_progress(self, test: bool = False):
        r"""Run the ``--progress`` action

        :Call:
            >>> a.run_progress(test=False)
        :Inputs:
            *a*: :class:`CaseArchivist`
                Archive controller for one case
            *test*: ``True`` | {``False``}
                Option to log all actions but not actually copy/delete
        :Versions:
            * 2024-09-15 ``@ddalle`: v1.0
        """
        # Begin
        self.begin("restart", test)
        # Log overall action
        self.log("run *Progress*")
        # Run level-2 actions
        self._progress_copy_files()
        self._progress_tar_files()
        self._progress_delete_files()
        self._progress_delete_dirs()

   # --- Level 2: progress ---
    def _progress_copy_files(self):
        # Get list of files to copy
        rawval = self.opts.get_opt("ProgressArchiveFiles")
        # Convert to unified format
        searchopt = expand_fileopt(rawval)
        # Log message
        self.log("begin *ProgressArchiveFiles*", parent=1)
        # Loop through patterns
        for pat, n in searchopt.items():
            # Conduct search
            matchdict = self.search(pat)
            # Copy the files
            self.archive_files(matchdict, n)

    def _progress_tar_files(self):
        # Get list of tar groups
        taropt = self.opts.get_opt("ProgressTarGroups")
        # Log message
        self.log("begin *ProgressTarGroups*", parent=1)
        # Loop through groups
        for tarname, searchopt in taropt.items():
            self.tar_archive(tarname, searchopt)

    def _progress_delete_files(self):
        # Get list of files to delete
        rawval = self.opts.get_opt("ProgressDeleteFiles")
        # Convert to unified format
        searchopt = expand_fileopt(rawval)
        # Log message
        self.log("begin *ProgressDeleteFiles*", parent=1)
        # Loop through files
        for pat, n in searchopt.items():
            # Conduct search
            matchdict = self.search(pat)
            # Delete the files
            self.delete_files(matchdict, n)

    def _progress_delete_dirs(self):
        # Get list of files to delete
        rawval = self.opts.get_opt("ProgressDeleteDirs")
        # Convert to unified format
        searchopt = expand_fileopt(rawval)
        # Log message
        self.log("begin *ProgressDeleteDirs*", parent=1)
        # Loop through files
        for pat, n in searchopt.items():
            # Conduct search
            matchdict = self.search(pat)
            # Delete the files
            self.delete_dirs(matchdict, n)

   # --- General actions ---
    # Begin a general action
    def begin(self, safety: str = "archive", test: bool = False):
        r"""Initialize counters and lsits for new archiving action

        :Call:
            >>> a.begin(safety="archive", test=False)
        :Inputs:
            *a*: :class:`CaseArchivist`
                Archive controller for one case
            *safety*: {``"archive"``} | :class:`str`
                Level of safety, determines which files to protect
            *test*: ``True`` | {``False``}
                If ``True``, log which files would be deleted, but don't
                actually delete, copy, or tar anything
        :Versions:
            * 2024-09-12 ``@ddalle``: v1.0
        """
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

    # Tar files to archive
    @run_rootdir
    def tar_archive(self, tarname: str, searchopt: dict):
        r"""Archive one or more files in a tarball/zip

        :Call:
            >>> a.tar_archive(tarname, searchopt)
        :Inputs:
            *a*: :class:`CaseArchivist`
                Archive controller for one case
            *tarname*: :class:`str`
                Name of tar/zip file to create, without file extension
            *searchopt*: :class:`dict`
                Patterns of file names to include in archive, key is
                regex/glob and value is *n*, number of files to include
        :Versions:
            * 2024-09-15 ``@ddalle``: v1.0
        """
        # Find files matching patterns
        filelist = self._search_targroups(searchopt)
        # Get file extension
        ext = self.opts.get_ArchiveExtension()
        # Name of tarball
        ftar = tarname + ext
        # Absolutize
        ftar_abs = self.abspath_archive(ftar)
        # Check if target already exists
        if os.path.isfile(ftar_abs):
            # Get modification times (recursive for *filelist*)
            mtime1 = getmtime(ftar_abs)
            mtime2 = getmtime(*filelist)
            # Check if up-to-date
            if mtime1 >= mtime2:
                # Log that tar-ball is up-to-date
                self.log(f"ARCHIVE/{ftar} up-to-date")
                return
        # Log message
        args = " ".join(searchopt.keys())
        self.log(f"tar ARCHIVE/{ftar} {args}")
        # Log each file ...
        for filename in filelist:
            self.log(f"  add '{filename}' => ARCHIVE/{ftar}")
        # Otherwise run the command
        if not self._test:
            self._tar(ftar_abs, filelist)

    # Tar files to archive
    @run_rootdir
    def tar_local(self, tarname: str, searchopt: dict):
        r"""Archive one or more files in local case folder

        :Call:
            >>> a.tar_local(tarname, searchopt)
        :Inputs:
            *a*: :class:`CaseArchivist`
                Archive controller for one case
            *tarname*: :class:`str`
                Name of tar/zip file to create, without file extension
            *searchopt*: :class:`dict`
                Patterns of file names to include in archive, key is
                regex/glob and value is *n*, number of files to include
        :Versions:
            * 2024-09-15 ``@ddalle``: v1.0
        """
        # Find files matching patterns
        filelist = self._search_targroups(searchopt)
        # Get file extension
        ext = self.opts.get_ArchiveExtension()
        # Name of tarball
        ftar = tarname + ext
        # Absolutize
        ftar_abs = self.abspath_local(ftar)
        # Check if target already exists
        if os.path.isfile(ftar_abs):
            # Get modification times (recursive for *filelist*)
            mtime1 = getmtime(ftar_abs)
            mtime2 = getmtime(*filelist)
            # Check if up-to-date
            if mtime1 >= mtime2:
                # Log that tar-ball is up-to-date
                self.log(f"{ftar} up-to-date")
                return
        # Log message
        args = " ".join(searchopt.keys())
        self.log(f"tar {ftar} {args}")
        # Log each file ...
        for filename in filelist:
            self.log(f"  add '{filename}' => {ftar}")
        # Otherwise run the command
        if not self._test:
            self._tar(ftar_abs, filelist)

    # Copy files to archive
    def archive_files(self, matchdict: dict, n: int):
        r"""Copy collection(s) of files from a single search

        :Call:
            >>> a.archive_files(matchdict, n)
        :Inputs:
            *a*: :class:`CaseArchivist`
                Archive controller for one case
            *matchdict*: :class:`dict`
                List of files to archive for each regex group value
            *n*: :class:`int`
                Number of files to keep for each list
        :Versions:
            * 2024-09-13 ``@ddalle``: v1.0
        """
        # Loop through matches
        for grp, mtchs in matchdict.items():
            # Log the group
            self.log(f"regex groups: {grp}")
            # Split into files to delete and files to keep
            if n < 0:
                # Copy only the oldest files
                copyfiles = mtchs[:-n]
            else:
                # Copy only the newest files (all if n==0)
                copyfiles = mtchs[-n:]
            # Copy files
            for filename in copyfiles:
                self.archive_file(filename)

    # Delete local folders
    def delete_dirs(self, matchdict: dict, n: int):
        r"""Delete collection(s) of folders from a single search

        :Call:
            >>> a.delete_dirs(matchdict, n)
        :Inputs:
            *a*: :class:`CaseArchivist`
                Archive controller for one case
            *matchdict*: :class:`dict`
                List of dirs to delete for each regex group value
            *n*: :class:`int`
                Number of files to keep for each list
        :Versions:
            * 2024-09-13 ``@ddalle``: v1.0
        """
        # Loop through matches
        for grp, mtchs in matchdict.items():
            # Log the group
            self.log(f"regex groups: {grp}")
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
                self.delete_dir(filename)
            # Keep the last *n* files
            for filename in keepfiles:
                self.keep_file(filename)

    # Delete local files
    def delete_files(self, matchdict: dict, n: int):
        r"""Delete collection(s) of files from a single search

        :Call:
            >>> a.delete_files(matchdict, n)
        :Inputs:
            *a*: :class:`CaseArchivist`
                Archive controller for one case
            *matchdict*: :class:`dict`
                List of files to delete for each regex group value
            *n*: :class:`int`
                Number of files to keep for each list
        :Versions:
            * 2024-09-13 ``@ddalle``: v1.0
        """
        # Loop through matches
        for grp, mtchs in matchdict.items():
            # Log the group
            self.log(f"regex groups: {grp}")
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

    # Delete a single folder
    def delete_dir(self, filename: str):
        r"""Delete a single folder if allowed; log results

        :Call:
            >>> a.delete_file(filename)
        :Inputs:
            *a*: :class:`CaseArchivist`
                Archive controller for one case
            *filename*: :class:`str`
                Name of file to delete
        :Versions:
            * 2024-09-13 ``@ddalle``: v1.0
        """
        # Check if it's a folder or gone
        if os.path.isfile(filename):
            self.warn(f"cannot rmdir: '{filename}' is a file")
            return
        elif not os.path.isdir(filename):
            self.warn(f"cannot rmdir: '{filename}' does not exist")
            return
        # Add to size
        self._size += getsize(filename)
        # Check against file lists...
        if self.check_safety(filename):
            # Generate message
            msg = f"rm -r '{filename}'"
            # Log it
            self.log(msg, parent=2)
            # Actual deletion (if no --test option)
            if not self._test:
                shutil.rmtree(filename)

    # Delete a single file
    def delete_file(self, filename: str):
        r"""Delete a single file if allowed; log results

        :Call:
            >>> a.delete_file(filename)
        :Inputs:
            *a*: :class:`CaseArchivist`
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
            # Actual deletion (if no --test option)
            if not self._test:
                os.remove(filename)

    # Keep file
    def keep_file(self, filename: str):
        r"""Keep a file and log the action

        :Call:
            >>> a.keep_file(filename)
        :Inputs:
            *a*: :class:`CaseArchivist`
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
            *a*: :class:`CaseArchivist`
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
            *a*: :class:`CaseArchivist`
                Archive controller for one case
            *fname*: :class:`str`
                Name of file to copy
            *parent*: {``0``} | :class:`int`
                Additional depth of function name in log
        :Versions:
            * 2024-09-04 ``@ddalle``: v1.0
            * 2024-09-15 ``@ddalle``: v1.1; add mtime checks
        """
        # Archive folder
        adir = self.get_archivedir()
        # Absolute paths
        fname_local = self.abspath_local(fname)
        fname_archive = self.abspath_archive(fname)
        # Check file statuses
        if not os.path.isfile(fname_local):
            self.warn(f"cannot cp '{fname}'; no such file")
            return
        elif os.path.isfile(fname_archive):
            # Get modification times
            s1 = os.path.getmtime(fname_local)
            s2 = os.path.getmtime(fname_archive)
            # Check if up-to-date
            if s2 > s1:
                # Archive up-to-date
                self.log(f"ARCHIVE/{fname} up-to-date", parent=parent)
                return
            else:
                # Out-of-date file in archive
                self.log(f"rm ARCHIVE/{fname} (updating)")
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
            *a*: :class:`CaseArchivist`
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
            *a*: :class:`CaseArchivist`
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
    def _tar(self, ftar: str, filelist: list):
        # Get archive format
        fmt = self.opts.get_opt("ArchiveFormat")
        # Create tar
        tar(ftar, *filelist, fmt=fmt, wc=False)

    # Untar a tarfile
    def _untar(self, ftar: str):
        # Get archive format
        fmt = self.opts.get_opt("ArchiveFormat")
        # Unpack
        untar(ftar, fmt=fmt, wc=False)

   # --- Protected files ---
    def save_reportfiles(self, searchopt: dict):
        r"""Save list of files to protect for ``"report"`` option

        The idea is to generate and save a list of files that presently
        appear to be required in order to restart the case without
        unarchiving.

        :Call:
            >>> a.save_reportfiles(searchopt)
        :Inputs:
            *a*: :class:`CaseArchivist`
                Archive controller for one case
            *searchopt*: :class:`dict`
                Key is the regular expression (or glob), value is the
                number of files to protect that match the pattern
        :Versions:
            * 2024-09-13 ``@ddalle``: v1.0
        """
        self.log("Saving list of files needed for reports")
        self._report_files = self.find_keepfiles(searchopt)

    def save_restartfiles(self, searchopt: dict):
        r"""Save list of files to protect for ``"restart"`` option

        The idea is to generate and save a list of files that presently
        appear to be required in order to restart the case without
        unarchiving.

        :Call:
            >>> a.save_restartfiles(searchopt)
        :Inputs:
            *a*: :class:`CaseArchivist`
                Archive controller for one case
            *searchopt*: :class:`dict`
                Key is the regular expression (or glob), value is the
                number of files to protect that match the pattern
        :Versions:
            * 2024-09-13 ``@ddalle``: v1.0
        """
        self.log("Saving list of files needed to restart case")
        self._restart_files = self.find_keepfiles(searchopt)

    @run_rootdir
    def find_keepfiles(self, searchopt: dict) -> list:
        r"""Generate list of files to keep based on a search option

        :Call:
            >>> a.find_keepfiles(searchopt)
        :Inputs:
            *a*: :class:`CaseArchivist`
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

   # --- File search ---
    @run_rootdir
    def search(self, pat: str) -> dict:
        r"""Search case folder for files matching a given pattern

        :Call:
            >>> matchdict = a.search(pat)
        :Inputs:
            *a*: :class:`CaseArchivist`
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
        :Versions:
            * 2024-09-11 ``@ddalle``: v1.0
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

    @run_rootdir
    def _search_targroups(self, searchopt: dict) -> list:
        r"""Search for list of files that match collection of patterns

        :Call:
            >>> filelist = a._search_targroups(searchopt)
        :Inputs:
            *a*: :class:`CaseArchivist`
                Archive controller for one case
            *searchopt*: :class:`dict`
                Patterns of file names to include in archive, key is
                regex/glob and value is *n*, number of files to include
        :Outputs:
            *filelist*: :class:`list`\ [:class:`str`]
                List of files or folders that match *searchopt*
        :Versions:
            * 2024-09-15 ``@ddalle``: v1.0
        """
        # Initialize file list
        filelist = []
        # Loop through patterns
        for pat, n in searchopt.items():
            # Conduct search
            matchdict = self.search(pat)
            # Loop through groups
            for mtchs in matchdict.values():
                # Check which files from list to retain
                if n < 0:
                    # First *n* files
                    mtchsj = mtchs[:-n]
                else:
                    # Last *n* files or all files for n==0
                    mtchsj = mtchs[-n:]
                # Extend list
                filelist.extend(mtchsj)
        # Output
        return filelist

   # --- Archive home ---
    # Add .tar to file name (or appropriate)
    def get_tarfile(self, filename: str) -> str:
        r"""Add ``.tar``, ``.tar.gz``, ``.zip``, etc. as needed to file

        :Call:
            >>> ftar = a.get_tarfile(filename)
        :Inputs:
            *a*: :class:`CaseArchivist`
                Archive controller for one case
            *filename*: :class:`str`
                Name of file or folder
        :Outputs:
            *ftar*: :class:`str`
                Name of file or folder with archive extension added
        :Versions:
            * 2024-09-14 ``@ddalle``: v1.0
        """
        # Get tar extension
        ext = self.opts.get_ArchiveExtension()
        # Check if extension already applied
        if filename.endswith(ext):
            return filename
        # Add extension
        return filename + ext

    # Make folders as needed for case
    def make_case_archivedir(self):
        r"""Create the case archive folder if needed

        :Call:
            >>> a.make_case_archivedir()
        :Inputs:
            *a*: :class:`CaseArchivist`
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
            *a*: :class:`CaseArchivist`
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
            *a*: :class:`CaseArchivist`
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

    # Ensure root of target archive exists
    def assert_archive(self):
        r"""Raise an exception if archive root does not exist

        :Call:
            >>> a.assert_archive()
        :Inputs:
            *a*: :class:`CaseArchivist`
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
            *a*: :class:`CaseArchivist`
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
        valj = expand_fileopt(rawj, vdef=vdef)
        # Save to total dict
        optval.update(valj)
    # Output
    return optval


# Get latest mod time of one or more files or folders
def getmtime(*filenames) -> float:
    r"""Get **latest** modification time of a file or folder

    :Call:
        >>> t = _getmtime(*filenames)
    :Inputs:
        *filenames*: :class:`tuple`\ [:class:`str`]
            Name of one or more files or folders
    :Outputs:
        *total_size*: :class:`int`
            Size of file or folder in bytes (``0`` if no such file)
    :Versions:
        * 2024-09-14 ``@ddalle``: v1.0
    """
    # Initialize
    mtime = 0.0
    # Loop through inputs
    for filename_or_folder in filenames:
        # Cumulative max
        mtime = max(mtime, _getmtime(filename_or_folder))
    # Output
    return mtime


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


# Get latest mod time of a file or folder
def _getmtime(file_or_folder: str) -> float:
    r"""Get **latest** modification time of a file or folder

    :Call:
        >>> t = _getmtime(file_or_folder)
    :Inputs:
        *file_or_folder*: :class:`str`
            Name of file or folder
    :Outputs:
        *total_size*: :class:`int`
            Size of file or folder in bytes (``0`` if no such file)
    :Versions:
        * 2024-09-14 ``@ddalle``: v1.0
    """
    # Skip if no such file/folder or if it's a link
    if not os.path.exists(file_or_folder) or os.path.islink(file_or_folder):
        return 0.0
    # Check if file
    if os.path.isfile(file_or_folder):
        return os.path.getmtime(file_or_folder)
    # Initialize total size with the modtime of folder itself
    mtime = os.path.getmtime(file_or_folder)
    # Loop through contents
    for fname in os.listdir(file_or_folder):
        # Absolutize
        fabs = os.path.join(file_or_folder, fname)
        # Use latest of previous and current (recursive)
        mtime = max(mtime, _getmtime(fabs))
    # Output
    return mtime


# Return a nice-looking size
def _disp_size(size: int) -> str:
    # Get order of magnitude of bytes
    level = int(math.log(size) / math.log(1024))
    # Get prefix
    prefix = " kMGTPE"[level].strip()
    # Amount of B/kB/MB
    y = size / 1024**level
    w = size % 1024**level
    # Check for decimal
    if math.log10(y) < 1 and (w != 0):
        # Use format like "3.2GB"
        z = "%.1f" % y
    else:
        # Convert to integer, like "32GB"
        z = str(int(y))
    # Output
    return f"{z} {prefix}B"


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
