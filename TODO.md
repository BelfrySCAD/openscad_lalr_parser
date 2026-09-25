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

## Comment round-trip (found while backporting, present on master)

With `include_comments=True`, 60 of BOSL2's 92 files don't reformat to a stable result
(`to_openscad` of the re-parse differs), measured 2026-09-24.

- A `//` comment at the end of a statement is attached to the statement's LAST EXPRESSION, and
  printed before the terminator, commenting it out: `x = 1; // c` prints `x = 1 // c;`,
  `x = f(1); // c` prints `x = f(1) // c;`. With a child module it lands on the child's NAME:
  `translate(v) cube(1); // c` prints `cube // c(1);`, and so do `if (a) cube(1); // c`,
  `for (...) cube(i); // c` and `module m() { cube(1); } // c`. The C++ port fixed the
  terminator cases in its initial port (`appendTerminatorSafely`, text-based, so a `"//"` in a
  string misfires) and has tests for them. A root fix attaches end-of-statement comments to the
  statement rather than an expression
- Standalone comments are only injected at top level: one inside a block or argument list
  (`foo(\n    // lead\n    a, b);`) is moved out to after the statement
- `rprism11.scad` crashes attachment: `_inject_comments` meets a top-level node that is a list
  (`AttributeError: 'list' object has no attribute 'position'`)
