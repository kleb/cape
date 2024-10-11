# -*- coding: utf-8 -*-
r"""
:mod:`cape.pylava.databook`: LAVA data book module
=====================================================

This module provides LAVA-specific interfaces to the various CFD
outputs tracked by the :mod:`cape` package.

"""

# Standard library

# Third-party imports

# Local imports
from .dataiterfile import DataIterFile
from ..cfdx import databook as cdbook
from ..dkit import basedata


# Aerodynamic history class
class DataBook(cdbook.DataBook):
    r"""Primary databook class for LAVA

    :Call:
        >>> db = DataBook(x, opts)
    :Inputs:
        *x*: :class:`RunMatrix`
            Current run matrix
        *opts*: :class:`Options`
            Global CAPE options instance
    :Outputs:
        *db*: :class:`DataBook`
            Databook instance
    :Versions:
        * 2024-09-30 ``@sneuhoff``: v1.0
    """
  # ===========
  # Readers
  # ===========
  # <
    # Initialize a DBComp object
    def ReadDBComp(self, comp, check=False, lock=False):
        r"""Initialize data book for one component

        :Call:
            >>> db.ReadDBComp(comp, check=False, lock=False)
        :Inputs:
            *db*: :class:`DataBook`
                Databook for one run matrix
            *comp*: :class:`str`
                Name of component
            *check*: ``True`` | {``False``}
                Whether or not to check LOCK status
            *lock*: ``True`` | {``False``}
                If ``True``, wait if the LOCK file exists
        :Versions:
            * 2024-09-18 ``@sneuhoff``: v1.0
        """
        # Read the data book
        self[comp] = DBComp(
            comp, self.cntl,
            targ=self.targ, check=check, lock=lock)

    # Local version of data book
    def _DataBook(self, targ):
        self.Targets[targ] = DataBook(
            self.cntl, RootDir=self.RootDir, targ=targ)

    # Local version of target
    def _DBTarget(self, targ):
        self.Targets[targ] = DBTarget(targ, self.x, self.opts, self.RootDir)
  # >

  # ========
  # Case I/O
  # ========
  # <
    # Current iteration status
    def GetCurrentIter(self):
        r"""Determine iteration number of current folder

        :Call:
            >>> n = db.GetCurrentIter()
        :Inputs:
            *db*: :class:`DataBook`
                Databook for one run matrix
        :Outputs:
            *n*: :class:`int` | ``None``
                Iteration number
        :Versions:
            * 2024-09-18 ``@sneuhoff``: v1.0
            * 2024-10-11 ``@ddalle``: v1.1; use ``DataIterFile``
        """
        try:
            db = DataIterFile(meta=True)
            return db.n
        except Exception:
            return None

    # Read case residual
    def ReadCaseResid(self):
        r"""Read a :class:`CaseResid` object

        :Call:
            >>> H = DB.ReadCaseResid()
        :Inputs:
            *db*: :class:`DataBook`
                Databook for one run matrix
        :Outputs:
            *H*: :class:`CaseResid`
                Residual history
        :Versions:
            * 2024-09-30 ``@sneuhoff``: v1.0
        """
        # Read CaseResid object from PWD
        return CaseResid()

    # Read case FM history
    def ReadCaseFM(self, comp: str):
        r"""Read a :class:`CaseFM` object

        :Call:
            >>> fm = db.ReadCaseFM(comp)
        :Inputs:
            *db*: :class:`DataBook`
                Databook for one run matrix
            *comp*: :class:`str`
                Name of component
        :Outputs:
            *fm*: :class:`CaseFM`
                Force and moment history
        :Versions:
            * 2024-09-30 ``@sneuhoff``: v1.0
        """
        # Read CaseResid object from PWD
        return CaseFM(comp)
  # >


# Target databook class
class DBTarget(cdbook.DBTarget):
    pass


# Databook for one component
class DBComp(cdbook.DBComp):
    pass


# Iterative F&M history
class CaseFM(cdbook.CaseFM):
    r"""Iterative force & moment history for one component, one case

    :Call:
        >>> fm = CaseFM(comp=None)
    :Inputs:
        *comp*: :class:`str`
            Name of component
    :Outputs:
        *fm*: :class:`CaseFM`
            One-case iterative history
    :Versions:
        * 2024-09-30 ``@sneuhoff``: v1.0;
    """

    # Minimal list of columns (the global ones like flowres + comps)
    # Most of these also have cp/cv, like "cd","cdp","cdv" for
    # pressure and viscous
    _base_cols = (
        "i",
        "solver_iter",
        "CL",
        "CD",
        "CA",
        "CY",
        "CN",
        "CLL",
        "CLM",
        "CLN",
    )
    # Minimal list of "coeffs" (each comp gets one)
    _base_coeffs = (
        "CL",
        "CD",
        "CA",
        "CY",
        "CN",
        "CLL",
        "CLM",
        "CLN",
    )

    # List of files to read
    def get_filelist(self) -> list:
        r"""Get list of files to read

        :Call:
            >>> filelist = fm.get_filelist()
        :Inputs:
            *prop*: :class:`CaseFM`
                Component iterative history instance
        :Outputs:
            *filelist*: :class:`list`\ [:class:`str`]
                List of files to read to construct iterative history
        :Versions:
            * 2024-09-18 ``@sneuhoff``: v1.0
        """
        # Name of (single) file
        return ["data.iter"]

    # Read a raw data file
    def readfile(self, fname: str) -> dict:
        r"""Read the data.iter

        :Call:
            >>> db = fm.readfile(fname)
        :Inputs:
            *fm*: :class:`CaseFM`
                Single-component iterative history instance
            *fname*: :class:`str`
                Name of file to read
        :Outputs:
            *db*: :class:`dict`
                Data read from data.iter
        :Versions:
            * 2024-09-18 ``@sneuhoff``: v1.0
            * 2024-10-11 ``@ddalle``: v1.1; use ``DataIterFile``
        """
        # Read the data.iter
        data = DataIterFile(fname)
        # Unpack component name
        comp = self.comp
        # Initialize data for output
        db = basedata.BaseData()
        db.save_col("i", data["iter"])
        db.save_col("CL", data[f"cl_{comp}"])
        db.save_col("CD", data[f"cd_{comp}"])
        db.save_col("CA", data[f"cfx_{comp}"])
        db.save_col("CY", data[f"cfy_{comp}"])
        db.save_col("CN", data[f"cfz_{comp}"])
        db.save_col("CLL", data[f"cmx_{comp}"])
        db.save_col("CLM", data[f"cmy_{comp}"])
        db.save_col("CLN", data[f"cmz_{comp}"])
        # Output
        return db


# Iterative residual history
class CaseResid(cdbook.CaseResid):
    r"""Iterative residual history for one component, one case

    :Call:
        >>> hist = CaseResid(comp=None)
    :Inputs:
        *comp*: {``None``} | :class:`str`
            Name of component
    :Outputs:
        *hist*: :class:`CaseResid`
            One-case iterative history
    :Versions:
        * 2024-09-30 ``@sneuhoff``: v1.0;
    """

    # Initialization method
    def __init__(self, comp: str = "body1"):
        r"""Initialization method

        :Versions:
            * 2024-09-30 ``@sneuhoff``: v1.0
        """
        # Initialize attributes
        self.comp = comp
        # Call parent method
        cdbook.CaseResid.__init__(self)

    # List of files to read
    def get_filelist(self) -> list:
        r"""Get list of files to read

        :Call:
            >>> filelist = fm.get_filelist()
        :Inputs:
            *prop*: :class:`CaseFM`
                Component iterative history instance
        :Outputs:
            *filelist*: :class:`list`\ [:class:`str`]
                List of files to read to construct iterative history
        :Versions:
            * 2024-09-24 ``@sneuhoff``: v1.0
        """
        return ["data.iter"]

    # Read a raw data file
    def readfile(self, fname: str) -> dict:
        r"""Read the data.iter for residuals

        :Call:
            >>> db = fm.readfile(fname)
        :Inputs:
            *fm*: :class:`CaseFM`
                Single-component iterative history instance
            *fname*: :class:`str`
                Name of file to read
        :Outputs:
            *db*: :class:`BaseData`
                Data read from *fname*
        :Versions:
            * 2024-09-30 ``@sneuhoff``: v1.0
            * 2024-10-11 ``@ddalle``: v1.1; use ``DataiterFile``
        """
        # Read the data.iter
        data = DataIterFile(fname)
        # Initialize data for output
        db = basedata.BaseData()
        db.save_col("i", data["iter"])
        db.save_col("L2Resid", data["flowres"])
        # Output
        return db
