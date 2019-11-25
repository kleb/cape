#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import CSV module
import cape.attdb.ftypes.csv as csv

# Read CSV file
db = csv.CSVFile("runmatrix.csv",
    Definitions={
        "config": {"Type": "str"},
        "Label": {"Type": "str"},
        "user": {"Type": "str"}
    })

# Case number
i = 6

# Get attributes
for col in db.cols:
    print("%8s: %s" % (col, db[col][i]))

