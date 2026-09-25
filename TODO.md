# TODO

## Backports from openscad_cpp_parser

Triaged 2026-09-24 against cpp 33a78ca..9524bdc. `#N` are cpp PRs. Library search, backslash-newline
in strings, argument-list line comments, `render()` expressions and the range step flag are done.

- Strict-commas mode (#9), optional: reject the trailing commas 2021.01 rejected (call arguments
  and let/for/intersection_for assignments), keep them in list literals, list comprehensions and
  parameter declarations. Part of the parse cache key
- Libraries shipped beside the binary (#10's third search dir, OpenSCAD's
  `resourcePath("libraries")`) are not searched; a pip-installed package has no such directory,
  so this only matters if something ever bundles this parser with libraries next to it

## Comment round-trip

Reformatting with `include_comments=True` now always gives code that parses and is the same
program: on BOSL2, 91 of 92 files (the other is itself invalid), where 36 used to reformat into
code that didn't parse and 5 more into a different program. What's left is cosmetic -- the
program never changes, but on 58 files a second reformat differs from the first (measured
2026-09-24):

- Standalone comments are only injected at top level: one on its own line inside a block,
  argument list or list comprehension (`foo(\n    // lead\n    a, b);`) moves out to after the
  statement on the next reformat. Statement-trailing and `{`-line comments are placed in nested
  blocks now (`_place_statement_comment`); the same placement could take own-line comments
- Blank lines grow by two per reformat after a function/module declaration followed by a
  comment: `to_openscad` adds two, and the re-parse keeps them as `BlankLine`s
