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

Reformatting with `include_comments=True` gives code that parses, is the same program, keeps
every comment where it was, and reformats to identical text a second time: on BOSL2, 91 of 92
files (the other is itself invalid) and all 45,635 of their comments, measured 2026-09-24.

- Comments appear inside nested statement lists (`children`, `body`, `true_branch`, ...) when
  parsing with `include_comments=True`, not only at top level; a consumer counting a block's
  statements (as `$children` does) must skip them
