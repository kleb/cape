r"""
:mod:`cape.cfdx.archive.Archive`: Case archiving options
=========================================================

This module provides a class to access options relating to archiving
folders that were used to run CFD simulations.

The class provided in this module, :class:`ArchiveOpts`, is
loaded into the ``"RunControl"`` section of the main options interface.
"""

# Standard library
import os

# Local imports
from .util import OptionsDict


# Turn dictionary into Archive options
def auto_Archive(opts):
    r"""Automatically convert :class:`dict` to :class:`ArchiveOpts`
    
    :Call:
        >>> opts = auto_Archive(opts)
    :Inputs:
        *opts*: :class:`dict`
            Dict of either global, "RunControl" or "Archive" options
    :Outputs:
        *opts*: :class:`ArchiveOpts`
            Instance of archiving options
    :Versions:
        * 2016-02-29 ``@ddalle``: Version 1.0
    """
    # Check type
    if not isinstance(opts, dict):
        # Invalid type
        raise TypeError(
            "Expected input type 'dict'; got '%s'" % type(opts).__name__)
    # Downselect if appropriate
    opts = opts.get("RunControl", opts)
    opts = opts.get("Archive", opts)
    # Check if already initialized
    if isinstance(opts, ArchiveOpts):
        # Good; quit
        return opts
    else:
        # Convert to class
        return ArchiveOpts(**opts)


# Class for folder management and archiving
class ArchiveOpts(OptionsDict):
    r"""Archive mamangement options interface
    
    :Call:
        >>> opts = ArchiveOpts(**kw)
    :Inputs:
        *kw*: :class:`dict`
            Dictionary of archive options
    :Outputs:
        *opts*: :class:`ArchiveOpts`
            Archive options interface
    :Versions:
        * 2016-30-02 ``@ddalle``: Version 1.0 (:class:`Archive`)
        * 2022-10-14 ``@ddalle``: Version 2.0; :class:`OptionsDict`
    """
    # List of recognized options
    _optlist = {
        "ArchiveAction",
        "ArchiveExtension",
        "ArchiveFiles",
        "ArchiveFolder",
        "ArchiveFormat",
        "ArchiveTemplate",
        "ArchiveType",
        "PostDeleteDirs",
        "PostDeleteFiles",
        "PostTarDirs",
        "PostTarGroups",
        "PreDeleteDirs",
        "PreDeleteFiles",
        "PreTarDirs",
        "PreTarGroups",
        "PreUpdateFiles",
        "ProgressArchiveFiles",
        "ProgressDeleteDirs",
        "ProgressDeleteFiles",
        "ProgressUpdateFiles",
        "ProgressTarDirs",
        "ProgressTarGroups",
        "RemoteCopy",
        "SkeletonDirs",
        "SkeletonFiles",
        "SkeletonTailFiles",
        "SkeletonTarDirs",
    }

    # Types
    _opttypes = {
        "_default_": str,
    }

    # Limited allowed values
    _optvals = {
        "ArchiveAction": ("", "archive", "rm", "skeleton"),
        "ArchiveExtension": ("tar", "tgz", "bz2", "zip"),
        "ArchiveFormat": ("", "tar", "gzip", "bz2", "zip"),
        "ArchiveType": ("full", "sub"),
    }

    # Parameters to avoid phasing
    _optlistdepth = {
        "_default_": 1,
    }

    # Default values
    _rc = {
        "ArchiveAction": "archive",
        "ArchiveExtension": "tar",
        "ArchiveFolder": "",
        "ArchiveFormat": "tar",
        "ArchiveProgress": True,
        "ArchiveType": "full",
        "ArchiveTemplate": "full",
        "ArchiveFiles": [],
        "ArchiveGroups": [],
        "PostDeleteDirs": [],
        "PostDeleteFiles": [],
        "PostTarDirs": [],
        "PostTarGroups": [],
        "ProgressDeleteFiles": [],
        "ProgressDeleteDirs": [],
        "ProgressTarGroups": [],
        "ProgressTarDirs": [],
        "ProgressUpdateFiles": [],
        "ProgressArchiveFiles": [],
        "PreDeleteFiles": [],
        "PreDeleteDirs": [],
        "PreTarDirs": [],
        "PreTarGroups": [],
        "PreUpdateFiles": [],
        "PostUpdateFiles": [],
        "SkeletonFiles": ["case.json"],
        "SkeletonTailFiles": [],
        "SkeletonTarDirs": [],
        "RemoteCopy": "scp",
    }

    # Descriptions
    _rst_descriptions = {
        "ArchiveAction": "action to take after finishing a case",
        "ArchiveExtension": "archive file extension",
        "ArchiveFiles": "files to copy to archive",
        "ArchiveFolder": "path to the archive root",
        "ArchiveFormat": "format for case archives",
        "ArchiveTemplate": "template for default archive settings",
        "ArchiveType":  "flag for single (full) or multi (sub) archive files",
        "RemoteCopy": "command for archive remote copies",
        "PostDeleteDirs": "list of folders to delete after archiving",
        "PostDeleteFiles": "list of files to delete after archiving",
        "PostTarDirs": "folders to tar after archiving",
        "PostTarGroups": "groups of files to tar after archiving",
        "PostUpdateFiles": "globs: keep *n* and rm older, after archiving",
        "PreDeleteDirs": "folders to delete **before** archiving",
        "PreDeleteFiles": "files to delete **before** archiving",
        "PreTarGroups": "file groups to tar before archiving",
        "PreTarDirs": "folders to tar before archiving",
        "PreUpdateFiles": "files to keep *n* and delete older, b4 archiving",
        "ProgressArchiveFiles": "files to archive at any time",
        "ProgressDeleteDirs": "folders to delete while still running",
        "ProgressDeleteFiles": "files to delete while still running",
        "ProgressUpdateFiles": "files to delete old versions while running",
        "ProgressTarDirs": "folders to tar while running",
        "ProgressTarGroups": "list of file groups to tar while running",
        "SkeletonDirs": "folders to **keep** during skeleton action",
        "SkeletonFiles": "files to **keep** during skeleton action",
        "SkeletonTailFiles": "files to tail before deletion during skeleton",
        "SkeletonTarDirs": "folders to tar before deletion during skeleton",
    }

    # Get the umask
    def get_umask(self):
        r"""Get the current file permissions mask
        
        The default value is the read from the system
        
        :Call:
            >>> umask = opts.get_umask(umask=None)
        :Inputs:
            *opts* :class:`cape.cfdx.options.Options`
                Options interface
        :Outputs:
            *umask*: :class:`oct`
                File permissions mask
        :Versions:
            * 2015-09-27 ``@ddalle``: Version 1.0
        """
        # Read the option.
        umask = self.get('umask')
        # Check if we need to use the default.
        if umask is None:
            # Get the value.
            umask = os.popen('umask', 'r').read()
            # Convert to value.
            umask = eval('0o' + umask.strip())
        elif type(umask).__name__ in ['str', 'unicode']:
            # Convert to octal
            umask = eval('0o' + str(umask).strip().lstrip('0o'))
        # Output
        return umask
        
    # Set the umask
    def set_umask(self, umask):
        r"""Set the current file permissions mask
        
        :Call:
            >>> umask = opts.get_umask(umask=None)
        :Inputs:
            *opts* :class:`cape.cfdx.options.Options`
                Options interface
        :Outputs:
            *umask*: :class:`oct`
                File permissions mask
        :Versions:
            * 2015-09-27 ``@ddalle``: Version 1.0
        """
        # Default
        if umask is None:
            # Get the value.
            umask = os.popen('umask', 'r', 1).read()
            # Convert to value.
            self['umask'] = '0o' + umask.strip()
        elif type(umask).__name__ in ['str', 'unicode']:
            # Set the value as an octal number
            self['umask'] = '0o' + str(umask)
        else:
            # Convert to octal
            self['umask'] = '0o' + oct(umask)
        
    # Get the directory permissions to use
    def get_dmask(self):
        r"""Get the permissions to assign to new folders
        
        :Call:
            >>> dmask = opts.get_dmask()
        :Inputs:
            *opts* :class:`cape.cfdx.options.Options`
                Options interface
        :Outputs:
            *umask*: :class:`int`
                File permissions mask
        :Versions:
            * 2015-09-27 ``@ddalle``: Version 1.0
        """
        # Get the umask
        umask = self.get_umask()
        # Subtract UMASK from full open permissions
        return 0o0777 - umask
        
    # Apply the umask
    def apply_umask(self):
        r"""Apply the permissions filter
        
        :Call:
            >>> opts.apply_umask()
        :Inputs:
            *opts* :class:`cape.cfdx.options.Options`
                Options interface
        :Versions:
            * 2015-09-27 ``@ddalle``: Version 1.0
        """
        os.umask(self.get_umask())
            
    # Make a directory
    def mkdir(self, fdir):
        r"""Make a directory with the correct permissions
        
        :Call:
            >>> opts.mkdir(fdir)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *fdir*: :class:`str`
                Directory to create
        :Versions:
            * 2015-09-27 ``@ddalle``: Version 1.0
        """
        # Get umask
        umask = self.get_umask()
        # Apply umask
        dmask = 0o777 - umask
        # Make the directory.
        os.mkdir(fdir, dmask)
   # >
   
   # -----
   # Tools
   # -----
   # <
    # Archive command
    def get_ArchiveCmd(self):
        r"""Get archiving command
        
        :Call:
            >>> cmd = opts.get_ArchiveCmd()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *cmd*: :class:`list`\ [:class:`str`]
                Tar command and appropriate flags
        :Versions:
            * 2016-03-01 ``@ddalle``: Version 1.0
        """
        # Get the format
        fmt = self.get_opt("ArchiveFormat")
        # Process
        if fmt in ['gzip', 'tgz']:
            # Gzip
            return ['tar', '-czf']
        elif fmt in ['zip']:
            # Zip
            return ['zip', '-r']
        elif fmt in ['bzip', 'bz', 'bzip2', 'bz2', 'tbz', 'tbz2']:
            # Bzip2
            return ['tar', '-cjf']
        else:
            # Default: tar
            return ['tar', '-cf']
            
    # Unarchive command
    def get_UnarchiveCmd(self):
        r"""Get command to unarchive
        
        :Call:
            >>> cmd = opts.get_UnarchiveCmd()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *cmd*: :class:`list`\ [:class:`str`]
                Untar command and appropriate flags
        :Versions:
            * 2016-03-01 ``@ddalle``: Version 1.0
        """
        # Get the format
        fmt = self.get_opt("ArchiveFormat")
        # Process
        if fmt in ['gzip', 'tgz']:
            # Gzip
            return ['tar', '-xzf']
        elif fmt in ['zip']:
            # Zip
            return ['unzip']
        elif fmt in ['bzip', 'bz', 'bzip2', 'bz2', 'tbz', 'tbz2']:
            # Bzip2
            return ['tar', '-xjf']
        else:
            # Default: tar
            return ['tar', '-xf']
   # >


# Normal get/set options
_ARCHIVE_PROPS = (
    "ArchiveAction",
    "ArchiveExtension",
    "ArchiveFolder",
    "ArchiveFormat",
    "ArchiveTemplate",
    "ArchiveType",
    "RemoteCopy",
)
# Getters and extenders only
_GETTER_OPTS = (
    "ArchiveFiles",
    "PostDeleteDirs",
    "PostDeleteFiles",
    "PostTarDirs",
    "PostTarGroups",
    "PostUpdateFiles",
    "PreDeleteDirs",
    "PreDeleteFiles",
    "PreTarGroups",
    "PreTarDirs",
    "ProgressArchiveFiles",
    "ProgressDeleteDirs",
    "ProgressDeleteFiles",
    "ProgressUpdateFiles",
    "ProgressTarDirs",
    "ProgressTarGroups",
    "SkeletonFiles",
    "SkeletonDirs",
    "SkeletonTailFiles",
    "SkeletonTarDirs",
)

# Add full options
ArchiveOpts.add_properties(_ARCHIVE_PROPS)
# Add getters only
ArchiveOpts.add_getters(_GETTER_OPTS, prefix="Archive")
ArchiveOpts.add_extenders(_GETTER_OPTS, prefix="Archive")
