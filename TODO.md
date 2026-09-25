# TODO

## Backports from openscad_cpp_parser

Triaged 2026-09-24 against cpp 33a78ca..9524bdc. `#N` are cpp PRs.

- Library search (#10), `findLibraryFile` in `__init__.py`: `OPENSCADPATH` replaces the default
  libraries folder instead of being searched before it; Windows hard-codes
  `~\Documents` (wrong under OneDrive Known Folder Move, use `SHGetFolderPathW(CSIDL_PERSONAL)`);
  libraries beside the binary are never searched. The not-found error should list every
  directory tried
- Backslash-newline inside a string (#4): `x = "a\` + newline + `b";` is a syntax error here.
  OpenSCAD accepts it (warns "Undefined escape sequence", echoes `"ab"`). Keep both characters
  verbatim in the literal; escapes are resolved by the evaluator
- Comment round-trip in multi-line args (89114d9): `foo(a // one\n, b // two\n, c);` pretty-prints
  as `foo(a, // one b, // two c);`, which comments out the rest and no longer parses. Move a
  leading `//` onto the previous argument's line
- `render()` in expression position (#5): `render` becomes a reserved keyword and
  `obj = render() { ... };` gets its own node; the statement form stays a ModularCall
- RangeLiteral records whether the step was written (#6): `[5:0]` and `[5:1:0]` give identical
  ASTs and `str()` prints the synthesized step. The evaluator needs the flag for its
  backwards-range warning, and printing must reproduce the written form
- Strict-commas mode (#9), optional: reject the trailing commas 2021.01 rejected (call arguments
  and let/for/intersection_for assignments), keep them in list literals, list comprehensions and
  parameter declarations. Part of the parse cache key

Not needed: string spans (#3) are already right here; declaration signature comments already
ported (e6d72a6); #7/#8 shared parse cache and scope table are C++-structural.
