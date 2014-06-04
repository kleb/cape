"""
File Control Base Module
========================

This provides common methods to control objects for various specific files.
"""

# Advanced text processing
import re


# File control class
class FileCntl:
    """
    Base file control class.  This includes various methods for reading files,
    splitting it into sections, and replacing lines based on patterns or regular
    expressions.
    """
    
    # Initialization method; not useful for derived classes
    def __init__(self, fname):
        """
        Base file control class
        
        :Call:
            >>> FC = pyCart.FileCntl.FileCntl(fname)
            
        :Inputs:
            *fname*: :class:`str`
                Name of file to read from and manipulate
        """
        # Read the file.
        self.Read(fname)
        # Save the file name.
        self.fname = fname
    
    # Display method
    def __repr__(self):
        """
        Display method for file control class
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Initialize the string.
        s = '<FileCntl("%s", %i lines' % (self.fname, len(self.lines))
        # Check for number of sections.
        if hasattr(self, 'SectionNames'):
            # Write the number of sections.
            s = s + ", %i sections)>" % len(self.SectionNames)
        else:
            # Just close the string.
            s = s + ")>"
        return s
    
    
    # Read the file.
    def Read(self, fname):
        """
        Read text from file
        
        :Call:
            >>> FC.Read(fname)
        
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance
            *fname*: :class:`str`
                Name of file to read from
                
        :Outputs:
            ``None``
            
        :Effects:
            *FC.lines*: :class:`list`
                List of lines in file is created
            *FC._updated_sections*: :class:`bool`
                Whether or not the lines in the sections has been updated
            *FC._updated_lines*: :class:`bool`
                Whether or not the lines in the global text has been updated
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Open the file and read the lines.
        self.lines = open(fname).readlines()
        # Initialize update statuses.
        self._updated_sections = False
        self._updated_lines = False
        return None
    
    
    # Function to split into sections
    def SplitToSections(self, reg="\$__([\w_]+)", ngr=1):
        """
        Split lines into sections based on starting regular expression
        
        :Call:
            >>> FC.SplitToSections()
            >>> FC.SplitToSections(reg="\$__([\w_]+)", ngr=1)
            
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance
            *reg*: :class:`str`
                Regular expression for recognizing the start of a new section.
                By default this looks for sections that start with "$__" as in
                the 'input.cntl' files.  The regular expression must also
                include a group (meaning content between parentheses) to capture
                the *name* of the section.  Thus the default value of
                ``"\$__([\w_]+)"`` finds any name that consists of word
                characters and/or underscores.
            *ngr*: :class:`int`
                Group number from which to take name of section.  This is always
                ``1`` unless the section-starting regular expression has more
                than one group.
                
        :Outputs:
            ``None``
            
        :Effects:
            *FC.SectionNames*: :class:`list`
                List of section names is created (includes "_header")
            *FC.Section*: :class:`dict`
                Dictionary of section line lists is created
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Initial section name
        sec = "_header"
        # Initialize the sections.
        self.SectionNames = [sec]
        self.Section = {sec: []}
        # Loop through the lines.
        for line in self.lines:
            # Search for the new-section regular expression.
            m = re.search(reg, line)
            # Check if there was a match.
            if m:
                # Get the new section name.
                sec = m.group(ngr)
                # Start the new section.
                self.SectionNames.append(sec)
                self.Section[sec] = [line]
            else:
                # Append the line to the current section.
                self.Section[sec].append(line)
        # Done.
        return None
        
    # Function to update the text based on the section content.
    def UpdateLines(self):
        """
        Update the global file control text list from current section content
        
        :Call:
            >>> FC.UpdateLines()
            
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance
        
        :Effects:
            *FC.lines*: :class:`list`
                Lines are rewritten to match the sequence of lines from the
                sections
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Check for lines
        if not self._updated_sections:
            # No updates.
            return None
        # Reinitialize the lines.
        self.lines = []
        # Loop through the sections.
        for sec in self.SectionNames:
            # Join the lines in that section.
            self.lines.extend(self.Section[sec])
        # The lines are now up-to-date.
        self._updated_sections = False
        # Done.
        return None
        
    # Function to update the text based on the section content.
    def UpdateSections(self):
        """
        Remake the section split if necessary.
        
        :Call:
            >>> FC.UpdateLines()
            
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance
        
        :Effects:
            :func:`SplitToSections()` is run if *FC._updated_lines* is ``True``
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Check for lines
        if not self._updated_lines:
            # No updates.
            return None
        # Redo the split.
        self.SplitToSections()
        self._updated_lines = False
        # Done.
        return None
        
    # Method to ensure that an instance has a certain section
    def AssertSection(self, sec):
        """
        Assert that a certain section is present
        
        :Call:
            >>> FC.AssertSection(sec)
            
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance, defaults to *FC.fname*
            *sec*: :class:`str`
                Name of section to check for
        
        :Effects:
            Raises an exception if *FC* does not have the section
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Update sections.
        self.UpdateSections()
        # Check for the section.
        if sec not in self.SectionNames:
            raise KeyError(
                "File control instance does not have section '%s'" % sec)
        # Done
        return None
        
    # Method to write the file.
    def Write(self, fname=None):
        """
        Write to text file
        
        :Call:
            >>> FC.Write()
            >>> FC.Write(fname)
        
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance, defaults to *FC.fname*
            *fname*: :class:`str`
                Name of file to write to
                
        :Outputs:
            ``None``
            
        :Effects:
            Runs :func:`UpdateLines` if appropriate and writes *FC.lines* to
            text file
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Update the lines if appropriate.
        self.UpdateLines()
        # Default file name.
        if fname is None: fname = self.fname
        # Open the new file.
        f = open(fname, 'w')
        # Write the joined text.
        f.write("".join(self.lines))
        # Close the file and exit.
        f.close()
        return None
        
        
    # Method to replace a line that starts with a given string
    def ReplaceLineStartsWith(self, start, line):
        """
        Find all lines that begin with a certain string and replace them with
        another string.  Note that the entire line is replaced, not just the
        initial string.
        
        Leading spaces are ignored during the match tests.
        
        :Call:
            >>> n = FC.ReplaceLineStartsWith(start, line)
            >>> n = FC.ReplaceLineStartsWith(start, lines)
        
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance
            *start*: :class:`str`
                String to test as literal match for beginning of each line
            *line*: :class:`str`
                String to replace every match with
            *lines*: :class:`list`
                List of strings to match first ``len(lines)`` matches with
        
        :Outputs:
            *n*: :class:`int`
                Number of matches found
                
        :Effects:
            *FC.lines*: Some of the lines may be affected
            *FC._updated_lines*: Set to ``True``
        
        :Examples:
            Suppose that *FC* has the following two lines.
            
            ``Mach      8.00   # some comment\n``
            ``Mach      Mach_TMP\n``
            
            Then this example will replace *both* lines with ``Mach 4.0``
            
                >>> FC.ReplaceLineStartsWith('Mach', 'Mach 4.0')
                
            This example replaces each line with a different value for the Mach
            number.
            
                >>> FC.ReplaceLineStartsWidth('Mach', ['Mach 2.0', 'Mach 4.0']
                
            Finally, this example is different from the first example in that it
            will replace the first line and then quit before it can find the
            second match.
            
                >>> FC.ReplaceLineStartsWidth('Mach', ['Mach 4.0'])
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Set the update status.
        self.UpdateLines()
        self._updated_lines = True
        # Number of matches.
        n = 0
        # Loop through the lines.
        for i in range(len(self.lines)):
            # Get the line.
            L = self.lines[i]
            # Check for a match.
            if L.startswith(start):
                # Check for the replacement type.
                if type(line) is str:
                    # Replace the line.
                    self.lines[i] = line
                    n += 1
                else:
                    # Replace the line based on the list.
                    self.lines[i] = line[n]
                    # Increase the match count.
                    n += 1
                    # Check for end of matches.
                    if n >= len(line): return len(line)
        # Done
        return n
        
    # Method to replace a line only in a certain section
    def ReplaceLineInSectionStartsWith(self, sec, start, line):
        """
        Find all lines in a certain section that start with a specified literal
        string and replace the entire line with the specified text.
        
        :Call:
            >>> n = FC.ReplaceLineInSectionStartsWith(sec, start, line)
            >>> n = FC.ReplaceLineInSectionStartsWith(sec, start, lines)
            
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance
            *sec*: :class:`str`
                Name of section to search in
            *start*: :class:`str`
                String to test as literal match for beginning of each line
            *line*: :class:`str`
                String to replace every match with
            *lines*: :class:`list`
                List of strings to match first ``len(lines)`` matches with
        
        :Outputs:
            *n*: :class:`int`
                Number of matches found
                
        :Effects:
            Some lines in *FC.Section[sec]* may be replaced. 
            
        :See also:
            This function is similar to
            :func:`pyCart.FileCntl.FileCntl.ReplaceLineStartsWith` except that
            the search is restricted to a specified section.
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Number of matches.
        n = 0
        # Update the sections.
        self.UpdateSections()
        # Check if the section exists.
        if sec not in self.SectionNames: return n
        # Set the update status.
        self._updated_sections = True
        # Loop through the lines.
        for i in range(len(self.Section[sec])):
            # Get the line.
            L = self.Section[sec][i]
            # Check for a match.
            if L.startswith(start):
                # Check for the replacement type.
                if type(line) is str:
                    # Replace the line.
                    self.Section[sec][i] = line
                    n += 1
                else:
                    # Replace the line based on the match count.
                    self.Section[sec][i] = line[n]
                    # Increase the match count.
                    n += 1
                    # Check for end of matches.
                    if n >= len(line): return len(line)
        # Done.
        return n
        
        
    # Method to insert a line somewhere
    def InsertLine(self, i, line):
        """
        Insert a line of text somewhere into the text
        
        :Call:
            >>> FC.InsertLine(i, line)
            
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance
            *i*: :class:`int`
                Index to which to insert the line
            *line*: :class:`str`
                String to add
        
        :Effects:
            A line is inserted to *FC.lines*
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Set the update flags.
        self.UpdateLines()
        self._updated_lines = True
        # Insert the line.
        self.lines.insert(i, line)
        
    # Method to append a line
    def AppendLine(self, line):
        """
        Append a line of text
        
        :Call:
            >>> FC.AppendLine(line)
            
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance
            *line*: :class:`str`
                String to add
        
        :Effects:
            A line is appended to *FC.lines*
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Set the update flag.
        self.UpdateLines()
        self._updated_lines = True
        # Insert the line.
        self.lines.append(line)
        
    # Method to append a line
    def PrependLine(self, line):
        """
        Prepend a line of text
        
        :Call:
            >>> FC.PrependLine(line)
            
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance
            *line*: :class:`str`
                String to add
        
        :Effects:
            A line is prepended to *FC.lines*
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Set the update flag.
        self.UpdateLines()
        self._updated_lines = True
        # Insert the line.
        self.lines.prepend(line)
    
    
    # Method to insert a line somewhere
    def InsertLineToSection(self, sec, i, line):
        """
        Insert a line of text somewhere into the text of a section
        
        :Call:
            >>> FC.InsertLineToSection(sec, i, line)
            
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance
            *sec*: :class:`str`
                Name of section to update
            *i*: :class:`int`
                Index to which to insert the line
            *line*: :class:`str`
                String to add
        
        :Effects:
            A line is inserted to *FC.Section[sec]*
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Set the update flags.
        self.UpdateSections()
        self._updated_sections = True
        # Check for the section
        self.AssertSection(sec)
        # Insert the line.
        self.Section[sec].insert(i, line)
        
    # Method to append a line somewhere
    def AppendLineToSection(self, sec, i, line):
        """
        Append a line of text to a section
        
        :Call:
            >>> FC.AppendLineToSection(sec, i, line)
            
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance
            *sec*: :class:`str`
                Name of section to update
            *line*: :class:`str`
                String to add
        
        :Effects:
            A line is appended to *FC.Section[sec]*
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Set the update flags.
        self.UpdateSections()
        self._updated_sections = True
        # Check for the section
        self.AssertSection(sec)
        # Insert the line.
        self.Section[sec].append(line)
        
    # Method to prepend a line somewhere
    def PrependLineToSection(self, sec, i, line):
        """
        Prepend a line of text to a section
        
        :Call:
            >>> FC.PrependLineToSection(sec, i, line)
            
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance
            *sec*: :class:`str`
                Name of section to update
            *line*: :class:`str`
                String to add
        
        :Effects:
            A line is prepended to *FC.Section[sec]*
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Set the update flags.
        self.UpdateSections()
        self._updated_sections = True
        # Check for the section
        self.AssertSection(sec)
        # Insert the line.
        self.Section[sec].prepend(line)
        
        
    # Method to delete a line that starts with a certain literal
    def DeleteLineStartsWith(self, start, count=1):
        """
        Delete lines that start with given literal up to *count* times
        
        :Call:
            >>> n = FC.DeleteLineStartsWith(start)
            >>> n = FC.DeleteLineStartsWith(start, count)
        
        :Inputs:
            *start*: :class:`str`
                Line-starting string to search for
            *count*: :class:`int`
                Maximum number of lines to delete (default is ``1``
        
        :Outputs:
            *n*: :class:`int`
                Number of deletions made
                
        :Effects:
            Lines in *FC.lines* may be removed if they start with *start*.
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Initialize the deletion count.
        n = 0
        # Update the text.
        self.UpdateLines()
        # Line number
        i = 0
        # Loop backward through the lines.
        while i < len(self.lines):
            # Get the line.
            L = self.lines[i]
            # Check it.
            if L.startswith(start):
                # Increase the count.
                n += 1
                self._updated_lines = True
                # Delete the line.
                self.lines.__delitem__(i)
                # Check for limit.
                if n >= count:
                    return n
            else:
                # Increase line number.
                i += 1
        # Done.
        return n
        
    # Method to delete a line from a section that starts with a certain literal
    def DeleteLineInSectionStartsWith(self, sec, start, count=1):
        """
        Delete lines that start with given literal up to *count* times
        
        :Call:
            >>> n = FC.DeleteLineInSectionStartsWith(sec, start)
            >>> n = FC.DeleteLineInSectionStartsWith(sec, start, count)
        
        :Inputs:
            *sec*: :class:`str`
                Name of section to search
            *start*: :class:`str`
                Line-starting string to search for
            *count*: :class:`int`
                Maximum number of lines to delete (default is ``1``
        
        :Outputs:
            *n*: :class:`int`
                Number of deletions made
                
        :Effects:
            Lines in *FC.Section[sec]* may be removed if they start with
            *start*.
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Initialize the deletion count.
        n = 0
        # Update the sections.
        self.UpdateSections()
        # Check for the section.
        if sec not in self.SectionNames: return n
        # Line number
        i = 0
        # Loop backward through the lines.
        while i < len(self.Section[sec]):
            # Get the line.
            L = self.lines[i]
            # Check it.
            if L.startswith(start):
                # Increase the count.
                n += 1
                self._updated_sections = True
                # Delete the line.
                self.Section[sec].__delitem__(i)
                # Check for limit.
                if n >= count:
                    return n
            else:
                # Increase the line number.
                i += 1
        # Done.
        return n
        
                
    # Replace a line or add it if not found
    def ReplaceOrAddLineStartsWith(self, start, line, i=None):
        """
        Replace a line that starts with a given literal string or add the line
        if no matches are found.
        
        :Call:
            >>> FC.ReplaceOrAddLineStartsWith(start, line)
            >>> FC.ReplaceOrAddLineStartsWith(start, line, i)
            
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance
            *start*: :class:`str`
                String to test as literal match for beginning of each line
            *line*: :class:`str`
                String to replace every match with
            *i*: :class:`int`
                Location to add line (by default it is appended)
                
        :Outputs:
            ``None``
            
        :Effects:
            Replaces line in section *FC.lines* or adds it if not found
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Call the replace method (only perform once).
        n = self.ReplaceLineStartsWith(start, [line])
        # Check for a match.
        if not n:
            # Check where to add the line.
            if i is None:
                # Append.
                self.lines.append(line)
            else:
                # Insert at specified location.
                self.lines.insert(i, line)
        # Done
        return None
        
    # Replace a line or add (from one section) if not found
    def ReplaceOrAddLineToSectionStartsWith(self, sec, start, line, i=None):
        """
        Replace a line in a specified section that starts with a given literal 
        string or add the line to the section if no matches are found.
        
        :Call:
            >>> FC.ReplaceOrAddLineToSectionStartsWith(sec, start, line)
            >>> FC.ReplaceOrAddLineToSectionStartsWith(sec, start, line, i)
            
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance
            *sec*: :class:`str`
                Name of section to search in
            *start*: :class:`str`
                String to test as literal match for beginning of each line
            *line*: :class:`str`
                String to replace every match with
            *i*: :class:`int`
                Location to add line (by default it is appended)
                
        :Outputs:
            ``None``
            
        :Effects:
            Replaces line in section *FC.Section[sec]* or adds it if not found
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Call the replace method (only perform once).
        n = self.ReplaceLineInSectionStartsWith(sec, start, [line])
        # Must have the section.
        self.AssertSection(sec)
        # Check for a match.
        if not n:
            # Check where to add the line.
            if i is None:
                # Append.
                self.Section[sec].append(line)
            else:
                # Insert at specified location.
                self.Section[sec].insert(i, line)
        # Done
        return None
        
        
    # Method to replace a line that starts with a regular expression
    def ReplaceLineSearch(self, reg, line):
        """
        Find all lines that begin with a certain regular expression and replace
        them with another string.  Note that the entire line is replaced, not
        just the regular expression.
        
        Leading spaces are ignored during the match tests.
        
        :Call:
            >>> n = FC.ReplaceLineSearch(reg, line)
            >>> n = FC.ReplaceLineSearch(reg, lines)
        
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance
            *reg*: :class:`str`
                A regular expression to search for at the beginning of lines
            *line*: :class:`str`
                String to replace every match with
            *lines*: :class:`list`
                List of strings to match first ``len(lines)`` matches with
        
        :Outputs:
            *n*: :class:`int`
                Number of matches found
                
        :Effects:
            *FC.lines*: Some of the lines may be affected
            *FC._updated_lines*: Set to ``True``
        
        :Examples:
            Suppose that *FC* has the following two lines.
            
            ``Mach      8.00   # some comment\n``
            ``Mach    4\n``
            
            Then this example will replace *both* lines with ``Mach 2.0``
            
                >>> FC.ReplaceLineSearch('Mach\s+[0-9.]+', 'Mach 2.0')
                
            This example replaces each line with a different value for the Mach
            number.
            
                >>> FC.ReplaceLineSearch('Mach\s+[0-9.]+', ['Mach 2.0', 'Mach 2.5'])
                
            Finally, this example is different from the first example in that it
            will replace the first line and then quit before it can find the
            second match.
            
                >>> FC.ReplaceLineSearch('Mach\s+[0-9.]+', ['Mach 2.0'])
        """
        # Versions:
        #  2014.06.04 @ddalle  : First version
        
        # Set the update status.
        self.UpdateLines()
        self._updated_lines = True
        # Number of matches.
        n = 0
        # Loop through the lines.
        for i in range(len(self.lines)):
            # Get the line.
            L = self.lines[i]
            # Check for a match.
            if re.search(reg, L):
                # Check for the replacement type.
                if type(line) is str:
                    # Replace the line.
                    self.lines[i] = line
                    n += 1
                else:
                    # Replace the line based on the list.
                    self.lines[i] = line[n]
                    # Increase the match count.
                    n += 1
                    # Check for end of matches.
                    if n >= len(line): return len(line)
        # Done
        return n
        
    # Method to replace a line only in a certain section
    def ReplaceLineInSectionSearch(self, sec, reg, line):
        """
        Find all lines in a certain section that start with a specified regular
        expression and replace the entire lines with the specified text.
        
        :Call:
            >>> n = FC.ReplaceLineInSectionSearch(sec, reg, line)
            >>> n = FC.ReplaceLineInSectionSearch(sec, reg, lines)
            
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance
            *sec*: :class:`str`
                Name of section to search in
            *reg*: :class:`str`
                Regular expression to search for match at beginning of each line
            *line*: :class:`str`
                String to replace every match with
            *lines*: :class:`list`
                List of strings to match first ``len(lines)`` matches with
        
        :Outputs:
            *n*: :class:`int`
                Number of matches found
                
        :Effects:
            Some lines in *FC.Section[sec]* may be replaced. 
            
        :See also:
            This function is similar to
            :func:`pyCart.FileCntl.FileCntl.ReplaceLineSearch` except that
            the search is restricted to a specified section.
        """
        # Versions:
        #  2014.06.04 @ddalle  : First version
        
        # Number of matches.
        n = 0
        # Update the sections.
        self.UpdateSections()
        # Check if the section exists.
        if sec not in self.SectionNames: return n
        # Set the update status.
        self._updated_sections = True
        # Loop through the lines.
        for i in range(len(self.Section[sec])):
            # Get the line.
            L = self.Section[sec][i]
            # Check for a match.
            if re.search(reg, L):
                # Check for the replacement type.
                if type(line) is str:
                    # Replace the line.
                    self.Section[sec][i] = line
                    n += 1
                else:
                    # Replace the line based on the match count.
                    self.Section[sec][i] = line[n]
                    # Increase the match count.
                    n += 1
                    # Check for end of matches.
                    if n >= len(line): return len(line)
        # Done.
        return n
        
        
        # Replace a line or add it if not found
    def ReplaceOrAddLineSearch(self, reg, line, i=None):
        """
        Replace a line that starts with a given literal string or add the line
        if no matches are found.
        
        :Call:
            >>> FC.ReplaceOrAddLineSearch(reg, line)
            >>> FC.ReplaceOrAddLineSearch(reg, line, i)
            
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance
            *reg*: :class:`str`
                Regular expression to match beginning of line
            *line*: :class:`str`
                String to replace first match with
            *i*: :class:`int`
                Location to add line (by default it is appended)
                
        :Outputs:
            ``None``
            
        :Effects:
            Replaces line in section *FC.lines* or adds it if not found
        """
        # Versions:
        #  2014.06.04 @ddalle  : First version
        
        # Call the replace method (only perform once).
        n = self.ReplaceLineSearch(reg, [line])
        # Check for a match.
        if not n:
            # Check where to add the line.
            if i is None:
                # Append.
                self.lines.append(line)
            else:
                # Insert at specified location.
                self.lines.insert(i, line)
        # Done
        return None
        
    # Replace a line or add (from one section) if not found
    def ReplaceOrAddLineToSectionSearch(self, sec, reg, line, i=None):
        """
        Replace a line in a specified section that starts with a given literal 
        string or add the line to the section if no matches are found.
        
        :Call:
            >>> FC.ReplaceOrAddLineToSectionStartsWith(sec, reg, line)
            >>> FC.ReplaceOrAddLineToSectionStartsWith(sec, reg, line, i)
            
        :Inputs:
            *FC*: :class:`pyCart.FileCntl.FileCntl` or derivative
                File control instance
            *sec*: :class:`str`
                Name of section to search in
            *start*: :class:`str`
                String to test as literal match for beginning of each line
            *line*: :class:`str`
                String to replace every match with
            *i*: :class:`int`
                Location to add line (by default it is appended)
                
        :Outputs:
            ``None``
            
        :Effects:
            Replaces line in section *FC.Section[sec]* or adds it if not found
        """
        # Versions:
        #  2014.06.03 @ddalle  : First version
        
        # Call the replace method (only perform once).
        n = self.ReplaceLineInSectionSearch(sec, reg, [line])
        # Must have the section.
        self.AssertSection(sec)
        # Check for a match.
        if not n:
            # Check where to add the line.
            if i is None:
                # Append.
                self.Section[sec].append(line)
            else:
                # Insert at specified location.
                self.Section[sec].insert(i, line)
        # Done
        return None
        
        
        
