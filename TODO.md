# TODO

## Comment round-trip

Reformatting with `include_comments=True` gives code that parses, is the same program, keeps
every comment where it was, and reformats to identical text a second time: on BOSL2, 91 of 92
files (the other is itself invalid) and all 45,635 of their comments, measured 2026-09-24.

- Comments appear inside nested statement lists (`children`, `body`, `true_branch`, ...) when
  parsing with `include_comments=True`, not only at top level; a consumer counting a block's
  statements (as `$children` does) must skip them
