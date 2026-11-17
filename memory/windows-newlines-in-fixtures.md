---
name: windows-newlines-in-fixtures
description: On Windows, Path.write_text turns \n into \r\n; write byte-exact fixtures with write_bytes
type: correction
---

`test_report_download` failed on Windows only: `write_text("daily report\n")` wrote `\r\n`,
and the endpoint returned the bytes as they were. CI on Linux would have hidden it.

**Correction:** test fixtures whose bytes are asserted use `write_bytes`. Generated files that
are committed are written with `newline="\n"` (see `scripts/build_register.py`), and
`.gitattributes` forces LF in the repository.
