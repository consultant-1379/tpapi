'''User Acceptance test for UseCase 6
A tool shall be developed that will allow a TP tester verify the data coverage of a TP. This tool will not cover all coverage cases and is not intended to be a definitive data coverage test tool for TPs; rather it will cover a specific set of coverage cases and also serve as a template for how to use TP API .

The tool will analyse all tables in a selected TP (installed on an ENIQ server) and highlight the following:

    number of rows loaded in each table
    any empty/null columns (and associated table)
    rows marked suspect/duplicate
    % counter coverage

The tool should do the following:

    Read the TP installed on the ENIQ Server
    Execute a set of queries to test the coverage cases listed above
    Output the results to screen and file

This tool should be delivered to the community forum that will be established for the TP API; it should not be delivered with the product.

Acceptance criteria:

    Output will accurately reflect the data coverage of the TP
    Javadoc of the API methods developed
    Methods include exception handling and log issues/errors to a common log file
    Short "man page" for the tool
    Tool will write issues/errors to it's own log

Created on 24 Aug 2012
'''

# Use case is documentry only
print "Not done."