"""
Module to interface with "input.cntl" files: :mod:`pyCart.inputCntl`
====================================================================

This is a module built off of the :mod:`pyCart.fileCntl` module customized for
manipulating :file:`input.cntl` files.  Such files are split into section by lines of
the format

    ``$__Post_Processing``
    
and this module is designed to recognize such sections.  The main feature of
this module is methods to set specific properties of the :file:`input.cntl` 
file, for example the Mach number or CFL number.
"""

# Import the base file control class.
from cape.fileCntl import FileCntl, _num, _float

# Base this class off of the main file control class.
class Namelist(FileCntl):
    """
    File control class for :file:`fun3d.nml`
    ========================================
            
    This class is derived from the :class:`pyCart.fileCntl.FileCntl` class, so
    all methods applicable to that class can also be used for instances of this
    class.
    
    :Call:
        >>> nml = pyFun.Namelist()
        >>> nml = pyfun.Namelist(fname)
    :Inputs:
        *fname*: :class:`str`
            Name of namelist file to read, defaults to ``'fun3d.nml'``
    :Version:
        * 2015-10-15 ``@ddalle``: Started
    """
    
    # Initialization method (not based off of FileCntl)
    def __init__(self, fname="fun3d.nml"):
        """Initialization method"""
        # Read the file.
        self.Read(fname)
        # Save the file name.
        self.fname = fname
        # Split into sections.
        self.SplitToSections(reg="\&([\w_]+)")
        
    # Copy the file
    def Copy(self, fname):
        """Copy a file interface
        
        :Call:
            >>> nml2 = nml.Copy()
        :Inputs:
            *nml*: :class:`pyFun.namelist.Namelist`
                File control instance for :file:`fun3d.nml`
        :Outputs:
            *nml2*: :class:`pyFun.namelist.Namelist`
                Duplicate file control instance for :file:`fun3d.nml`
        :Versions:
            * 2015-06-12 ``@ddalle``: First version
        """
        # Create empty instance.
        nml = Namelist(fname=None)
        # Copy the file name.
        nml.fname = self.fname
        nml.lines = self.lines
        # Copy the sections
        nml.Section = self.Section
        nml.SectionNames = self.SectionNames
        # Update flags.
        nml._updated_sections = self._updated_sections
        nml._updated_lines = self._updated_lines
        # Output
        return nml
        
    # Function to set generic values, since they have the same format.
    def SetVar(self, sec, name, val, s=False, f=False):
        """Set generic :file:`fun3d.nml` variable value
        
        :Call:
            >>> nml.SetVar(sec, name, val, f=False)
        :Inputs:
            *nml*: :class:`pyFun.namelist.Namelist`
                File control instance for :file:`fun3d.nml`
            *sec*: :class:`str`
                Name of section in which to set variable
            *name*: :class:`str`
                Name of variable as identified in 'aero.csh'
            *val*: any, converted using :func:`str`
                Value to which variable is set in final script
            *f*: :class:`bool`
                If ``True``, force value to be written as a float
        :Versions:
            * 2014-06-10 ``@ddalle``: First version
        """
        # Check sections
        if sec not in self.SectionNames:
            raise KeyError("Section '%s' not found." % sec)
        # Line regular expression: "XXXX=" but with white spaces
        reg = '^\s*' + str(name) + '\s*[=\n]'
        # Convert *val* to string.
        val = str(val)
        # Form the output line.
        if f:
            # Force character to be written as a float!
            line = '    %s = %.20f\n' % (name, float(val))
        elif s:
            # Force quotes
            line = '    %s = "%s"\n' % (name, val)
        elif type(val).__name__ in ['str', 'unicode']:
            # Force quotes
            line = '    %s = "%s"\n' % (name, val)
        else:
            # Set a value.
            line = '    %s = %s\n' % (name, val)
        # Replace the line; prepend it if missing
        self.ReplaceOrAddLineToSectionSearch(sec, reg, line)
        
    # Function to get the value of a variable
    def GetVar(self, sec, name):
        """Get value of a variable
        
        :Call:
            >>> val = nml.GetVar(sec, name)
        :Inputs:
            *nml*: :class:`pyFun.namelist.Namelist`
                File control instance for :file:`fun3d.nml`
            *sec*: :class:`str`
                Name of section in which to set variable
            *name*: :class:`str`
                Name of variable as identified in 'aero.csh'
        :Outputs:
            *val*: :class:`str` or :class:`unicode`
                Value to which variable is set in final script
        :Versions:
            * 2015-10-15 ``@ddalle``: First version
        """
        # Check sections
        if sec not in self.SectionNames:
            raise KeyError("Section '%s' not found." % sec)
        # Line regular expression: "XXXX=" but with white spaces
        reg = '^\s*' + str(name) + '\s*[=\n]'
        # Find the line.
        lines = self.GetLineInSectionStartsWith(sec, name, 1)
        # Exit if no match
        if len(lines) == 0: return ''
        # Split on the equal sign
        vals = lines[0].split('=')
        # Check for a match
        if len(vals) < 1: return ''
        # Return the value
        return vals[1]
        
    # Function set the Mach number.
    def SetMach(self, mach):
        """Set the freestream Mach number
        
        :Call:
            >>> nml.SetMach(mach)
        :Inputs:
            *nml*: :class:`pyFun.namelist.Namelist`
                File control instance for :file:`fun3d.nml`
            *mach*: :class:`float`
                Mach number
        :Versions:
            * 2015-10-15 ``@ddalle``: First version
        """
        # Replace the line or add it if necessary.
        self.SetVar('reference_physical_properties', 'mach_number', mach)
        
    # Function to get the current Mach number.
    def GetMach(self):
        """
        Find the current Mach number
        
        :Call:
            >>> mach = nml.GetMach()
        :Inputs:
            *nml*: :class:`pyFun.namelist.Namelist`
                File control instance for :file:`fun3d.nml`
        :Outputs:
            *M*: :class:`float` (or :class:`str`)
                Mach number specified in :file:`input.cntl`
        :Versions:
            * 2014-06-10 ``@ddalle``: First version
        """
        # Get the value.
        return _float(
            self.GetVar('reference_physical_properties', 'mach_number'))
        
    # Function to set the angle of attack
    def SetAlpha(self, alpha):
        """Set the angle of attack
        
        :Call:
            >>> nml.SetAlpha(alpha)
        :Inputs:
            *nml*: :class:`pyFun.namelist.Namelist`
                File control instance for :file:`fun3d.nml`
            *alpha*: :class:`float`
                Angle of attack
        :Versions:
            * 2015-10-15 ``@ddalle``: First version
        """
        # Replace the line or add it if necessary.
        self.SetVar('reference_physical_properties', 
            'angle_of_attack', alpha)
        
    # Function to set the sideslip angle
    def SetBeta(self, beta):
        """Set the sideslip angle
        
        :Call:
            >>> nml.SetBeta(beta)
        :Inputs:
            *nml*: :class:`pyFun.namelist.Namelist`
                File control instance for :file:`fun3d.nml`
            *beta*: :class:`float`
                Sideslip angle
        :Versions:
            * 2014-06-04 ``@ddalle``: First version
        """
        # Replace the line or add it if necessary.
        self.SetVar('reference_physical_properties',
            'angle_of_yaw', beta)
        
    # Set temperature unites
    def SetTemperatureUnits(self, units=None):
        """Set the temperature units
        
        :Call:
            >>> nml.SetTemperatureUnits(units)
        :Inputs:
            *nml*: :class:`pyFun.namelist.Namelist`
                File control instance for :file:`fun3d.nml`
            *units*: :class:`str`
                Units, defaults to ``"Rankine"``
        :Versions:
            * 2015-10-15 ``@ddalle``: First version
        """
        # Check for defaults.
        if units is None: units = "Rankine"
        # Replace the line or add it if necessary.
        self.SetVar('reference_physical_properties',
            'temperature_units', units)
        
    # Set the temperature
    def SetTemperature(self, T):
        """Set the freestream temperature
        
        :Call:
            >>> nml.SetTemperature(T)
        :Inputs:
            *nml*: :class:`pyFun.namelist.Namelist`
                File control instance for :file:`fun3d.nml`
            *T*: :class:`float`
                Freestream temperature
        :Versions:
            * 2015-10-15 ``@ddalle``: First version
        """
        self.SetVar('reference_physical_properties', 'temperature', T)
        
    # Set the Reynolds number
    def SetReynoldsNumber(self, Re):
        """Set the Reynolds number per unit length
        
        :Call:
            >>> nml.SetReynoldsNumber(Re)
        :Inputs:
            *nml*: :class:`pyFun.namelist.Namelist`
                File control instance for :file:`fun3d.nml`
            *Re*: :class:`float`
                Reynolds number per unit length
        :Versions:
            * 2015-10-15 ``@ddalle``: First version
        """
        self.SetVar('reference_physical_properties', 'reynolds_number', Re)
        
# class Namelist

        
