"""
:mod:`cape.pyover.options.util`: Utilities for pyOver options module
=====================================================================

This module provides tools to read, access, modify, and write settings for
:mod:`cape.pyover`. It is based off of the :mod:`cape.cfdx.options.util` module and
provides a special class :class:`cape.cfdx.options.odict` that is subclassed from
the Python built-in :class:`dict`. Behavior, such as ``opts['OverNamelist']``
or ``opts.get('OverNamelist')`` are also present. In addition, many convenience
methods such as ``opts.get_OverNamelist()`` are provided.

In addition, this module controls default values of each pyOver parameter in a
three-step process.  The precedence used to determine what the value of a given
parameter should be is below.

    #. Values directly specified in the input file, :file:`pyOver.json`
    
    #. Values specified in the default control file,
       :file:`$PYOVER/settings/pyOver.default.json`
    
    #. Hard-coded defaults from this module
    
:See Also:
    * :mod:`cape.cfdx.options.util`
    * :mod:`cape.pyover.options`
"""

# Import CAPE options utilities
from cape.cfdx.options.util import *

# Get the root directory of the module.
_fname = os.path.abspath(__file__)

# Saved folder names
PyOverFolder = os.path.split(os.path.split(_fname)[0])[0]

# Backup default settings
rc["OverNamelist"]         = "overflow.inp"
rc["project_rootname"]     = "run"
rc["overrun_cmd"]          = "overrunmpi"
rc["overrun_aux"]          = "\"-v pcachem -- dplace -s1\""
rc["overrun_args"]         = ""
rc["MPI"]                  = True

# Mesh files
rc["MeshType"]  = "dcf"
rc["ConfigDir"] = "common"
# DCF defaults
rc["LinkFilesDCF"] = [[
    "grid.in",
    "xrays.in",
    "fomo/grid.ibi",
    "fomo/grid.nsf",
    "fomo/grid.ptv",
    "fomo/mixsur.fmp"
]]
rc["CopyFilesDCF"] = [[]]
# Pegasus 5 defaults
rc["LinkFilesPeg5"] = [[
    "grid.in",
    "x.save",
    "XINTOUT",
    "fomo/grid.ibi",
    "fomo/grid.nsf",
    "fomo/grid.ptv",
    "fomo/mixsur.fmp"
]]
rc["CopyFilesPeg5"] = [[]]
    

# Function to ensure scalar from above
def rc0(p):
    """
    Return default setting from ``pyCart.options.rc``, but ensure a scalar
    
    :Call:
        >>> v = rc0(s)
    :Inputs:
        *s*: :class:`str`
            Name of parameter to extract
    :Outputs:
        *v*: any
            Either ``rc[s]`` or ``rc[s][0]``, whichever is appropriate
    :Versions:
        * 2014-08-01 ``@ddalle``: First version
    """
    # Use the `getel` function to do this.
    return getel(rc[p], 0)


# Function to get the defautl settings.
def getPyOverDefaults():
    """
    Read :file:`pyOver.default.json` default settings configuration file
    
    :Call:
        >>> defs = getPyOverDefaults()
    :Outputs:
        *defs*: :class:`dict`
            Dictionary of settings read from JSON file
    :Versions:
        * 2014-06-03 ``@ddalle``: First version
        * 2014-07-28 ``@ddalle``: Moved to new options module
        * 2015-12-29 ``@ddalle``: OVERFLOW version
    """
    # Fixed default file
    fname = os.path.join(PyOverFolder, 
        "..", "..", "settings", "pyOver.default.json")
    # Process the default input file
    return loadJSONFile(fname)
    
