DocPrefix (Windows GUI)
=======================

What this tool does
-------------------
DocPrefix is a local file renaming tool for documents. It adds a prefix to each
filename in a selected folder using this format:

  YYYYMM - Lastname, Firstname - <existing filename>

Example:
  report.pdf
becomes:
  202602 - Doe, Jane - report.pdf

This tool runs locally on your computer and does not use the network.


How to run
----------
1. Open the DocPrefix folder.
2. Double-click `DocPrefix.exe`.

Important:
- If you received a portable folder build (ONEDIR), keep all files in that
  folder together. Do not move only the `.exe` out of the folder.


How to use
----------
1. Click "Browse..." and select the folder containing files to rename.
2. Enter First name and Last name.
3. Choose options (Recursive, Force, Conflict policy, Date mode) as needed.
4. Click "Preview" to review the planned changes.
5. Click "Apply" only after reviewing the preview.
6. Confirm the dialog to perform the rename operations.


Safety behavior
---------------
- Preview-first by default (no changes are made until you click Apply).
- Apply always asks for confirmation before renaming files.
- The tool only renames files in the folder you select.


Troubleshooting
---------------
Windows SmartScreen warning:
- Click "More info" and then "Run anyway" if you trust the source.

Antivirus / corporate security tools:
- Some antivirus tools may flag packaged applications (especially single-file
  builds) as suspicious. This can be a false positive.
- If available, use the portable folder build (ONEDIR), which is often flagged
  less often than ONEFILE builds.

Permissions / protected folders:
- If the tool cannot rename files, try a folder where you have write access.
- Avoid system folders or locations managed by IT policies.

Files in use:
- Close any program that currently has the file open (PDF viewer, Word, etc.)
  and try again.


Notes
-----
- The tool does not upload files.
- Renaming is not automatically undoable. Always review the Preview first.
