"""
Cart3D and pyCart settings module: :mod:`pyCart.options`
========================================================

This module provides tools to read, access, modify, and write settings for
:mod:`pyCart`.  The class is based off of the built-int :class:`dict` class, so
its default behavior, such as ``opts['InputCntl']`` or 
``opts.get('InputCntl')`` are also present.  In addition, many convenience
methods, such as ``opts.set_it_fc(n)``, which sets the number of
:file:`flowCart` iterations,  are provided.

In addition, this module controls default values of each pyCart
parameter in a two-step process.  The precedence used to determine what the
value of a given parameter should be is below.

    *. Values directly specified in the input file, :file:`pyCart.json`
    
    *. Values specified in the default control file,
       :file:`$PYCART/settings/pyCart.default.json`
    
    *. Hard-coded defaults from this module
"""

# Import options-specific utilities
from util import *

# Import modules for controlling specific parts of Cart3D
from .flowCart    import flowCart
from .adjointCart import adjointCart
from .Adaptation  import Adaptation
from .Mesh        import Mesh
from .pbs         import PBS
from .Config      import Config


# Class definition
class Options(odict):
    """
    Options structure, subclass of :class:`dict`
    
    :Call:
        >>> opts = Options(fname=None, **kw)
    :Inputs:
        *fname*: :class:`str`
            File to be read as a JSON file with comments
        *kw*: :class:`dict`
            Dictionary to be transformed into :class:`pyCart.options.Options`
    :Versions:
        * 2014.07.28 ``@ddalle``: First version
    """
    
    # Initialization method
    def __init__(self, fname=None, **kw):
        """Initialization method with optional JSON input"""
        # Check for an input file.
        if fname:
            # Read the input file.
            lines = open(fname).readlines()
            # Strip comments and join list into a single string.
            lines = stripComments(lines, '#')
            lines = stripComments(lines, '//')
            # Get the equivalent dictionary.
            d = json.loads(lines)
            # Loop through the keys.
            for k in d:
                kw[k] = d[k]
        # Read the defaults.
        defs = getPyCartDefaults()
        # Apply the defaults.
        kw = applyDefaults(kw, defs)
        # Store the data in *this* instance
        for k in kw:
            self[k] = kw[k]
        # Upgrade important groups to their own classes.
        self._flowCart()
        self._adjointCart()
        self._Adaptation()
        self._Mesh()
        self._PBS()
        self._Config()
    
    
    # Initialization and confirmation for flowCart options
    def _flowCart(self):
        """Initialize `flowCart` options if necessary"""
        # Check for missing entirely.
        if 'flowCart' not in self:
            # Empty/default
            self['flowCart'] = flowCart()
        elif type(self['flowCart']).__name__ == 'dict':
            # Convert to special class.
            self['flowCart'] = flowCart(**self['flowCart'])
            
    # Initialization and confirmation for adjointCart options
    def _adjointCart(self):
        """Initialize `adjointCart` options if necessary"""
        # Check for missing entirely.
        if 'adjointCart' not in self:
            # Empty/default
            self['adjointCart'] = adjointCart()
        elif type(self['adjointCart']).__name__ == 'dict':
            # Convert to special class.
            self['adjointCart'] = adjointCart(**self['adjointCart'])
    
    # Initialization and confirmation for Adaptation options
    def _Adaptation(self):
        """Initialize adaptation options if necessary"""
        # Check status
        if 'Adaptation' not in self:
            # Missing entirely
            self['Adaptation'] = Adaptation()
        elif type(self['Adaptation']).__name__ == 'dict':
            # Convert to special class.
            self['Adaptation'] = Adaptation(**self['Adaptation'])
    
    # Initialization and confirmation for Adaptation options
    def _Mesh(self):
        """Initialize mesh options if necessary"""
        # Check status
        if 'Mesh' not in self:
            # Missing entirely
            self['Mesh'] = Mesh()
        elif type(self['Mesh']).__name__ == 'dict':
            # Convert to special class.
            self['Mesh'] = Mesh(**self['Mesh'])
            
    # Initialization and confirmation for PBS options
    def _PBS(self):
        """Initialize PBS options if necessary"""
        # Check status.
        if 'PBS' not in self:
            # Missing entirely
            self['PBS'] = PBS()
        elif type(self['PBS']).__name__ == 'dict':
            # Add prefix to all the keys.
            tmp = {}
            for k in self['PBS']:
                tmp["PBS_"+k] = self['PBS'][k]
            # Convert to special class.
            self['PBS'] = PBS(**tmp)
            
    # Initialization and confirmation for PBS options
    def _Config(self):
        """Initialize configuration options if necessary"""
        # Check status.
        if 'Config' not in self:
            # Missing entirely
            self['Config'] = Config()
        elif type(self['Config']).__name__ == 'dict':
            # Add prefix to all the keys.
            tmp = {}
            for k in self['Config']:
                # Check for "File"
                if k == 'File':
                    # Add prefix.
                    tmp["Config"+k] = self['Config'][k]
                else:
                    # Use the key as is.
                    tmp[k] = self['Config'][k]
            # Convert to special class.
            self['Config'] = Config(**tmp)
    
    # ==============
    # Global Options
    # ==============
    
    # Method to get the input file
    def get_InputCntl(self):
        """Return the name of the master :file:`input.cntl` file
        
        :Call:
            >>> fname = opts.get_InputCntl()
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
        :Outputs:
            *fname*: :class:`str`
                Name of Cart3D input control template file
        :Versions:
            * 2014.09.30 ``@ddalle``: First version
        """
        return self.get('InputCntl', rc0('InputCntl'))
        
    # Method to set the input file
    def set_InputCntl(self, fname):
        """Set the name of the master :file:`input.cntl` file
        
        :Call:
            >>> opts.set_InputCntl(fname)
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
            *fname*: :class:`str`
                Name of Cart3D input control template file
        :Versions:
            * 2014.09.30 ``@ddalle``: First version
        """
        self['InputCntl'] = fname
    
    # Method to get the aero shell file
    def get_AeroCsh(self):
        """Return the name of the master :file:`aero.csh` file
        
        :Call:
            >>> fname = opts.get_AeroCsh()
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
        :Outputs:
            *fname*: :class:`str`
                Name of Cart3D aero shell template file
        :Versions:
            * 2014.09.30 ``@ddalle``: First version
        """
        return self.get('AeroCsh', rc0('AeroCsh'))
        
    # Method to set the input file
    def set_AeroCsh(self, fname):
        """Set the name of the master :file:`aero.csh` file
        
        :Call:
            >>> opts.set_AeroCsh(fname)
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
            *fname*: :class:`str`
                Name of Cart3D asero shell template file
        :Versions:
            * 2014.09.30 ``@ddalle``: First version
        """
        self['AeroCsh'] = fname
    
    # Method to determine if groups have common meshes.
    def get_GroupMesh(self):
        """Determine whether or not groups have common meshes
        
        :Call:
            >>> qGM = opts.get_GroupMesh()
        :Inputs:
            *opts* :class:`pyCart.options.Options`
                Options interface
        :Outputs:
            *qGM*: :class:`bool`
                True all cases in a group use the same (starting) mesh
        :Versions:
            * 2014.10.06 ``@ddalle``: First version
        """
        return self.get('GroupMesh', rc0('GroupMesh'))
        
    # Method to specify that meshes do or do not use the same mesh
    def set_GroupMesh(self, qGM=rc0('GroupMesh')):
        """Specify that groups do or do not use common meshes
        
        :Call:
            >>> opts.get_GroupMesh(qGM)
        :Inputs:
            *opts* :class:`pyCart.options.Options`
                Options interface
            *qGM*: :class:`bool`
                True all cases in a group use the same (starting) mesh
        :Versions:
            * 2014.10.06 ``@ddalle``: First version
        """
        self['GroupMesh'] = qGM
        
    
    # ==============
    # Shell Commands
    # ==============
    
    # Function to get the shell commands
    def get_ShellCmds(self):
        """Get shell commands, if any
        
        :Call:
            >>> cmds = opts.get_ShellCmds()
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
        :Outputs:
            *cmds*: :class:`list`
        """
        # Get the commands.
        cmds = self.get('ShellCmds', [])
        # Turn to a list if not.
        if type(cmds).__name__ != 'list':
            cmds = [cmds]
        # Output
        return cmds
    
    # ===================
    # flowCart parameters
    # ===================
    
    # Get number of inputs
    def get_nSeq(self):
        self._flowCart()
        return self['flowCart'].get_nSeq()
    # Copy documentation
    get_nSeq.__doc__ = flowCart.get_nSeq.__doc__
    
    # Get input sequence
    def get_InputSeq(self, i=None):
        self._flowCart()
        return self['flowCart'].get_InputSeq(i)
        
    # Set input sequence
    def set_InputSeq(self, InputSeq=rc0('InputSeq'), i=None):
        self._flowCart()
        self['flowCart'].set_InputSeq(InputSeq, i)
        
    # Get iteration break points
    def get_IterSeq(self, i=None):
        self._flowCart()
        return self['flowCart'].get_IterSeq(i)
        
    # Set Iteration break points
    def set_IterSeq(self, IterSeq=rc0('IterSeq'), i=None):
        self._flowCart()
        return self['flowCart'].set_IterSeq(IterSeq, i)
    
    # Get flowCart order
    def get_first_order(self, i=None):
        self._flowCart()
        return self['flowCart'].get_first_order(i)
        
    # Set flowCart order
    def set_first_order(self, fo=rc0('first_order'), i=None):
        self._flowCart()
        self['flowCart'].set_first_order(fo, i)
    
    # Number of iterations
    def get_it_fc(self, i=None):
        self._flowCart()
        return self['flowCart'].get_it_fc(i)
        
    # Set flowCart iteration count
    def set_it_fc(self, it_fc=rc0('it_fc'), i=None):
        self._flowCart()
        self['flowCart'].set_it_fc(it_fc, i)
        
    # Get flowCart iteration count
    def get_mg_fc(self, i=None):
        self._flowCart()
        return self['flowCart'].get_mg_fc(i)
        
    # Set flowCart iteration count
    def set_mg_fc(self, mg_fc=rc0('mg_fc'), i=None):
        self._flowCart()
        self['flowCart'].set_mg_fc(mg_fc, i)
        
    # Get MPI status
    def get_mpi_fc(self, i=None):
        self._flowCart()
        return self['flowCart'].get_mpi_fc(i)
        
    # Set MPI status
    def set_mpi_fc(self, mpi_fc=rc0('mpi_fc'), i=None):
        self._flowCart()
        self['flowCart'].set_mpi_fc(mpi_fc, i)
        
    # Get aero.csh status
    def get_use_aero_csh(self, i=None):
        self._flowCart()
        return self['flowCart'].get_use_aero_csh(i)
        
    # Set aero.csh status
    def set_use_aero_csh(self, ac=rc0('use_aero_csh'), i=None):
        self._flowCart()
        self['flowCart'].set_use_aero_csh(ac, i)
        
    # Get cut-cell gradient flag
    def get_tm(self, i=None):
        self._flowCart()
        return self['flowCart'].get_tm(i)
        
    # Set cut-cell gradient flag
    def set_tm(self, tm=rc0('tm'), i=None):
        self._flowCart()
        self['flowCart'].set_tm(tm, i)
        
    # Get the nominal CFL number
    def get_cfl(self, i=None):
        self._flowCart()
        return self['flowCart'].get_cfl(i)
        
    # Set the nominal CFL number
    def set_cfl(self, cfl=rc0('cfl'), i=None):
        self._flowCart()
        self['flowCart'].set_cfl(cfl, i)
        
    # Get the minimum CFL number
    def get_cflmin(self, i=None):
        self._flowCart()
        return self['flowCart'].get_cflmin(i)
    
    # Set the minimum CFL number
    def set_cflmin(self, cflmin=rc0('cflmin'), i=None):
        self._flowCart()
        self['flowCart'].set_cflmin(cflmin, i)
        
    # Get the limiter
    def get_limiter(self, i=None):
        self._flowCart()
        return self['flowCart'].get_limiter(i)
    
    # Set the limiter
    def set_limiter(self, limiter=rc0('limiter'), i=None):
        self._flowCart()
        self['flowCart'].set_limiter(limiter, i)
        
    # Get the y_is_spanwise status
    def get_y_is_spanwise(self, i=None):
        self._flowCart()
        return self['flowCart'].get_y_is_spanwise(i)
        
    # Set the y_is_spanwise status
    def set_y_is_spanwise(self, y_is_spanwise=rc0('y_is_spanwise'), i=None):
        self._flowCart()
        self['flowCart'].set_y_is_spanwise(y_is_spanwise, i)
        
    # Get the binary I/O status
    def get_binaryIO(self, i=None):
        self._flowCart()
        return self['flowCart'].get_binaryIO(i)
        
    # Set the binary I/O status
    def set_binaryIO(self, binaryIO=rc0('binaryIO'), i=None):
        self._flowCart()
        self['flowCart'].set_binaryIO(binaryIO, i)
        
    # Get the Tecplot output status
    def get_tecO(self, i=None):
        self._flowCart()
        return self['flowCart'].get_tecO(i)
        
    # Set the Tecplot output status
    def set_tecO(self, tecO=rc0('tecO'), i=None):
        self._flowCart()
        self['flowCart'].set_tecO(tecO, i)
        
    # Get the number of threads for flowCart
    def get_nProc(self, i=None):
        self._flowCart()
        return self['flowCart'].get_nProc(i)
        
    # Set the number of threads for flowCart
    def set_nProc(self, nProc=rc0('nProc'), i=None):
        self._flowCart()
        self['flowCart'].set_nProc(nProc, i)
        
    # Get the MPI system command
    def get_mpicmd(self, i=None):
        self._flowCart()
        return self['flowCart'].get_mpicmd(i)
        
    # Set the MPI system command
    def set_mpicmd(self, mpicmd=rc0('mpicmd'), i=None):
        self._flowCart()
        self['flowCart'].set_mpicmd(mpicmd, i)
        
    # Get the submittable/nonsubmittalbe status
    def get_qsub(self, i=None):
        self._flowCart()
        return self['flowCart'].get_qsub(i)
        
    # Set the submittable/nonsubmittalbe status
    def set_qsub(self, qsub=rc0('qsub'), i=None):
        self._flowCart()
        self['flowCart'].set_qsub(qsub, i)
        
    # Get the resubmittable/nonresubmittalbe status
    def get_resub(self, i=None):
        self._flowCart()
        return self['flowCart'].get_resub(i)
        
    # Set the resubmittable/nonresubmittalbe status
    def set_resub(self, resub=rc0('resub'), i=None):
        self._flowCart()
        self['flowCart'].set_resub(resub, i)
        
    # Copy over the documentation.
    for k in ['InputSeq', 'IterSeq', 'first_order', 'mpi_fc', 'use_aero_csh',
            'it_fc', 'mg_fc', 'cfl', 'cflmin', 'limiter', 'tecO',
            'y_is_spanwise', 'binaryIO', 'nProc', 'mpicmd', 'qsub', 'resub']:
        # Get the documentation for the "get" and "set" functions
        eval('get_'+k).__doc__ = getattr(flowCart,'get_'+k).__doc__
        eval('set_'+k).__doc__ = getattr(flowCart,'set_'+k).__doc__
        
    
    
    # ====================
    # adjointCart settings
    # ====================
    
    # Number of iterations
    def get_it_ad(self, i=None):
        self._adjointCart()
        return self['adjointCart'].get_it_ad(i)
        
    # Set flowCart iteration count
    def set_it_ad(self, it_ad=rc0('it_ad'), i=None):
        self._adjointCart()
        self['adjointCart'].set_it_ad(it_ad, i)
    
    # Get flowCart iteration count
    def get_mg_ad(self, i=None):
        self._adjointCart()
        return self['adjointCart'].get_mg_ad(i)
        
    # Set flowCart iteration count
    def set_mg_ad(self, mg_ad=rc0('mg_ad'), i=None):
        self._adjointCart()
        self['adjointCart'].set_mg_ad(mg_ad, i)
        
    # Copy over the documentation.
    for k in ['it_ad', 'mg_ad']:
        # Get the documentation for the "get" and "set" functions
        eval('get_'+k).__doc__ = getattr(adjointCart,'get_'+k).__doc__
        eval('set_'+k).__doc__ = getattr(adjointCart,'set_'+k).__doc__
    
    # ================
    # multigrid levels
    # ================
        
    # Method to get the number of multigrid levels
    def get_mg(self, i=None):
        """Return the number of multigrid levels
        
        :Call:
            >>> mg = opts.get_mg(i=None) 
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
            *i*: :class:`int`
                Run index
        :Outputs:
            *mg*: :class:`int`
                Maximum of *mg_fc* and *mg_ad*
        :Versions:
            * 2014.08.01 ``@ddalle``: First version
        """
        # Get the two values.
        mg_fc = self.get_mg_fc(i)
        mg_ad = self.get_mg_ad(i)
        # Check for valid settings.
        if mg_fc and mg_ad:
            # Handle lists...
            if type(mg_fc).__name__ == "list":
                mg_fc = mg_fc[0]
            if type(mg_ad).__name__ == "list":
                mg_ad = mg_ad[0]
            # Both are defined, use maximum.
            return max(mg_fc, mg_ad)
        elif mg_fc:
            # Only one valid nonzero setting; use it.
            return mg_fc
        elif mg_ad:
            # Only one valid nonzero setting; use it.
            return mg_ad
        else:
            # Both either invalid or zero.  Return 0.
            return 0
    
    # Method to set both multigrid levels
    def set_mg(self, mg=rc0('mg_fc'), i=None):
        """Set number of multigrid levels for `flowCart` and `adjointCart`
        
        :Call:
            >>> opts.set_mg(mg, i=None) 
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
            *mg*: :class:`int`
                Multigrid levels for both adjointCart and flowCart
            *i*: :class:`int`
                Run index
        :Versions:
            * 2014.08.01 ``@ddalle``: First version
        """
        self.set_mg_fc(mg, i)
        self.set_mg_ad(mg, i)
        
        
    # ===================
    # Adaptation settings
    # ===================
    
    # Get number of adapt cycles
    def get_n_adapt_cycles(self, i=None):
        self._Adaptation()
        return self['Adaptation'].get_n_adapt_cycles(i)
        
    # Set number of adapt cycles
    def set_n_adapt_cycles(self, nAdapt=rc0('n_adapt_cycles'), i=None):
        self._Adaptation()
        self['Adaptation'].set_n_adapt_cycles(nAdapt, i)
    
    # Get error tolerance
    def get_etol(self, i=None):
        self._Adaptation()
        return self['Adaptation'].get_etol(i)
        
    # Set error tolerance
    def set_etol(self, etol=rc0('etol'), i=None):
        self._Adaptation()
        self['Adaptation'].set_etol(etol, i)
    
    # Get maximum cell count
    def get_max_nCells(self, i=None):
        self._Adaptation()
        return self['Adaptation'].get_max_nCells(i)
        
    # Set maximum cell count
    def set_max_nCells(self, etol=rc0('max_nCells'), i=None):
        self._Adaptation()
        self['Adaptation'].set_max_nCells(etol, i)
    
    # Get flowCart iterations on refined meshes
    def get_ws_it(self, i=None):
        self._Adaptation()
        return self['Adaptation'].get_ws_it(i)
        
    # Set flowCart iterations on refined meshes
    def set_ws_it(self, ws_it=rc0('ws_it'), i=None):
        self._Adaptation()
        self['Adaptation'].set_ws_it(ws_it, i)
        
    # Get mesh growth ratio
    def get_mesh_growth(self, i=None):
        self._Adaptation()
        return self['Adaptation'].get_mesh_growth(i)
        
    # Set mesh growth ratio
    def set_mesh_growth(self, mesh_growth=rc0('mesh_growth'), i=None):
        self._Adaptation()
        self['Adaptation'].set_mesh_growth(mesh_growth, i)
        
    # Get mesh refinement cycle type
    def get_apc(self, i=None):
        self._Adaptation()
        return self['Adaptation'].get_apc(i)
        
    # Set mesh refinement cycle type
    def set_apc(self, apc=rc0('apc'), i=None):
        self._Adaptation()
        self['Adaptation'].set_apc(apc, i)
        
    # Copy over the documentation.
    for k in ['n_adapt_cycles', 'etol', 'max_nCells', 'ws_it',
            'mesh_growth', 'apc']:
        # Get the documentation for the "get" and "set" functions
        eval('get_'+k).__doc__ = getattr(Adaptation,'get_'+k).__doc__
        eval('set_'+k).__doc__ = getattr(Adaptation,'set_'+k).__doc__
            
    
    # ========================
    # mesh creation parameters
    # ========================
    
    # Get triangulation file(s)
    def get_TriFile(self, i=None):
        self._Mesh()
        return self['Mesh'].get_TriFile(i)
        
    # Set triangulation file(s)
    def set_TriFile(self, TriFile=rc0('TriFile'), i=None):
        self._Mesh()
        self['Mesh'].set_TriFile(TriFile, i)
    
    # Get mesh2d status
    def get_mesh2d(self, i=None):
        self._Mesh()
        return self['Mesh'].get_mesh2d(i)
        
    # Set error tolerance
    def set_mesh2d(self, mesh2d=rc0('mesh2d'), i=None):
        self._Mesh()
        self['Mesh'].set_mesh2d(mesh2d, i)
        
    # Get the nominal mesh radius
    def get_r(self, i=None):
        self._Mesh()
        return self['Mesh'].get_r(i)
        
    # Set the nominal mesh radius
    def set_r(self, r=rc0('r'), i=None):
        self._Mesh()
        self['Mesh'].set_r(r, i)
    
    # Get the number of refinements
    def get_maxR(self, i=None):
        self._Mesh()
        return self['Mesh'].get_maxR(i)
        
    # Set the number of refinements
    def set_maxR(self, maxR=rc0('maxR'), i=None):
        self._Mesh()
        self['Mesh'].set_maxR(maxR, i)
        
    # Get the prespecification file
    def get_pre(self, i=None):
        self._Mesh()
        return self['Mesh'].get_pre(i)
        
    # Set the prespecification file
    def set_pre(self, pre=rc0('pre'), i=None):
        self._Mesh()
        self['Mesh'].set_pre(pre, i)
        
    # Get the 'cubes_a' parameter
    def get_cubes_a(self, i=None):
        self._Mesh()
        return self['Mesh'].get_cubes_a(i)
        
    # Set the 'cubes_a' parameter
    def set_cubes_a(self, cubes_a=rc0('cubes_a'), i=None):
        self._Mesh()
        self['Mesh'].set_cubes_a(cubes_a, i)
        
    # Get the 'cubes_b' parameter
    def get_cubes_b(self, i=None):
        self._Mesh()
        return self['Mesh'].get_cubes_b(i)
        
    # Set the 'cubes_b' parameter
    def set_cubes_b(self, cubes_b=rc0('cubes_b'), i=None):
        self._Mesh()
        self['Mesh'].set_cubes_b(cubes_b, i)
        
    # Get the mesh reordering status
    def get_reorder(self, i=None):
        self._Mesh()
        return self['Mesh'].get_reorder(i)
        
    # Set the mesh reordering status
    def set_reorder(self, reorder=rc0('reorder'), i=None):
        self._Mesh()
        self['Mesh'].set_reorder(reorder, i)
        
        
    # Copy over the documentation.
    for k in ['TriFile', 'mesh2d', 'r', 'maxR', 'pre',
            'cubes_a', 'cubes_b', 'reorder']:
        # Get the documentation for the "get" and "set" functions
        eval('get_'+k).__doc__ = getattr(Mesh,'get_'+k).__doc__
        eval('set_'+k).__doc__ = getattr(Mesh,'set_'+k).__doc__
        
        
    # ============
    # PBS settings
    # ============
    
    # Get PBS *join* setting
    def get_PBS_j(self):
        self._PBS()
        return self['PBS'].get_PBS_j()
        
    # Set PBS *join* setting
    def set_PBS_j(self, j=rc0('PBS_j')):
        self._PBS()
        self['PBS'].set_PBS_j(j)
    
    # Get PBS *rerun* setting
    def get_PBS_r(self):
        self._PBS()
        return self['PBS'].get_PBS_r()
        
    # Set PBS *rerun* setting
    def set_PBS_r(self, r=rc0('PBS_r')):
        self._PBS()
        self['PBS'].set_PBS_r(r)
    
    # Get PBS shell setting
    def get_PBS_S(self):
        self._PBS()
        return self['PBS'].get_PBS_S()
        
    # Set PBS shell setting
    def set_PBS_S(self, S=rc0('PBS_S')):
        self._PBS()
        self['PBS'].set_PBS_S(S)
    
    # Get PBS nNodes setting
    def get_PBS_select(self):
        self._PBS()
        return self['PBS'].get_PBS_select()
        
    # Set PBS nNodes setting
    def set_PBS_select(self, n=rc0('PBS_select')):
        self._PBS()
        self['PBS'].set_PBS_select(n)
    
    # Get PBS CPUS/node setting
    def get_PBS_ncpus(self):
        self._PBS()
        return self['PBS'].get_PBS_ncpus()
        
    # Set PBS CPUs/node setting
    def set_PBS_ncpus(self, n=rc0('PBS_ncpus')):
        self._PBS()
        self['PBS'].set_PBS_ncpus(n)
    
    # Get PBS MPI procs/node setting
    def get_PBS_mpiprocs(self):
        self._PBS()
        return self['PBS'].get_PBS_mpiprocs()
        
    # Set PBS *rerun* setting
    def set_PBS_mpiprocs(self, n=rc0('PBS_mpiprocs')):
        self._PBS()
        self['PBS'].set_PBS_mpiprocs(n)
    
    # Get PBS model or arch setting
    def get_PBS_model(self):
        self._PBS()
        return self['PBS'].get_PBS_model()
        
    # Set PBS model or arch setting
    def set_PBS_model(self, s=rc0('PBS_model')):
        self._PBS()
        self['PBS'].set_PBS_model(s)
    
    # Get PBS group setting
    def get_PBS_W(self):
        self._PBS()
        return self['PBS'].get_PBS_W()
        
    # Set PBS group setting
    def set_PBS_W(self, W=rc0('PBS_W')):
        self._PBS()
        self['PBS'].set_PBS_W(W)
    
    # Get PBS queue setting
    def get_PBS_q(self):
        self._PBS()
        return self['PBS'].get_PBS_q()
        
    # Set PBS queue setting
    def set_PBS_q(self, q=rc0('PBS_q')):
        self._PBS()
        self['PBS'].set_PBS_q(q)
    
    # Get PBS walltime setting
    def get_PBS_walltime(self):
        self._PBS()
        return self['PBS'].get_PBS_walltime()
        
    # Set PBS walltime setting
    def set_PBS_walltime(self, t=rc0('PBS_walltime')):
        self._PBS()
        self['PBS'].set_PBS_walltime(t)
        
    # Copy over the documentation.
    for k in ['PBS_j', 'PBS_r', 'PBS_S', 'PBS_select', 'PBS_mpiprocs',
            'PBS_ncpus', 'PBS_model', 'PBS_W', 'PBS_q', 'PBS_walltime']:
        # Get the documentation for the "get" and "set" functions
        eval('get_'+k).__doc__ = getattr(PBS,'get_'+k).__doc__
        eval('set_'+k).__doc__ = getattr(PBS,'set_'+k).__doc__
    
    
    # =============
    # Configuration
    # =============
    
    # Get config file name
    def get_ConfigFile(self):
        self._Config()
        return self['Config'].get_ConfigFile()
        
    # Set config file name
    def set_ConfigFile(self, fname=rc0('ConfigFile')):
        self._Config()
        self['Config'].set_ConfigFile(fname)
    
    # Get reference area
    def get_RefArea(self, comp=None):
        self._Config()
        return self['Config'].get_RefArea(comp)
        
    # Set config file name
    def set_RefArea(self, A=rc0('RefArea'), comp=None):
        self._Config()
        self['Config'].set_RefArea(A, comp)
    
    # Get reference length
    def get_RefLength(self, comp=None):
        self._Config()
        return self['Config'].get_RefLength(comp)
        
    # Set config file name
    def set_RefLength(self, L=rc0('RefLength'), comp=None):
        self._Config()
        self['Config'].set_RefLength(L, comp)
    
    # Get moment reference point
    def get_RefPoint(self, comp=None):
        self._Config()
        return self['Config'].get_RefPoint(comp)
        
    # Set moment reference point
    def set_RefPoint(self, x=rc0('RefPoint'), comp=None):
        self._Config()
        self['Config'].set_RefPoint(x, comp)
        
    # Copy over the documentation.
    for k in ['ConfigFile', 'RefArea', 'RefLength', 'RefPoint']:
        # Get the documentation for the "get" and "set" functions
        eval('get_'+k).__doc__ = getattr(Config,'get_'+k).__doc__
        eval('set_'+k).__doc__ = getattr(Config,'set_'+k).__doc__


