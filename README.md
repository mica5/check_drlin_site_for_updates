# check_drlin_site_for_updates
Check Dr. Lin's site for file updates.  
This is for Dr. Lin's CS157A. It's difficult to keep track of all the changing files/assignments/requirements of this class, and this script is intended to make it easier to keep up with changes.

# Usage

## From a Jupyter Notebook

    # make sure that no code appears after this at the end of
    # its cell, so that the DataFrame is displayed below
    from check_drlin_site_for_updates.check_drlin_site_for_updates import show_html_updates_table
    show_html_updates_table()

## From the command line

    # prints a formatted DataFrame table to stdout
    ./check_drlin_site_for_updates.py
