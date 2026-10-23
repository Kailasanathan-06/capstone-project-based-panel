TEST PURPOSE: failed_01_corrupt_archive.zip
===========================================
This file is intentionally truncated to test ZIP integrity and defensive archive parsing.
EXPECTED RESULT:
The upload validation service detects the corrupted headers via zipfile.testzip() or invalid header check,
rejects the archive gracefully, logs an audit event, and avoids server crashing.
