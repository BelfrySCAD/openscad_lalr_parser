"""Command-line interface for openscad_lalr_parser."""
import sys
import argparse
from openscad_lalr_parser import getASTfromString, getASTfromFile, ast_to_json
from openscad_lalr_parser.pretty_print import to_openscad


def main():
    ap = argparse.ArgumentParser(
        prog="openscad-lalr",
        description=(
            "Parse an OpenSCAD file and dump its AST as JSON (default), "
            "YAML, or reformatted OpenSCAD source."
        ),
    )
    ap.add_argument(
        "file",
        nargs="?",
        metavar="FILE",
        help="OpenSCAD source file to parse. Omit or use '-' to read from stdin.",
    )
    output = ap.add_mutually_exclusive_group()
    output.add_argument(
        "-j", "--json", action="store_true", default=True,
        help="Output AST as JSON (default).",
    )
    output.add_argument(
        "-y", "--yaml", action="store_true",
        help="Output AST as YAML (requires PyYAML).",
    )
    output.add_argument(
        "-r", "--format", action="store_true",
        help="Output reformatted OpenSCAD source code (comments preserved).",
    )
    comments = ap.add_mutually_exclusive_group()
    comments.add_argument(
        "-c", "--no-comments", action="store_true",
        help="Exclude comments from the output.",
    )
    comments.add_argument(
        "-C", "--with-comments", action="store_true",
        help="Include comments in the output.",
    )
    ap.add_argument(
        "-i", "--no-includes", action="store_true",
        help="Do not expand include <...> statements (keeps IncludeStatement nodes).",
    )
    ap.add_argument(
        "--indent", type=int, default=4, metavar="N",
        help="Indentation width in spaces (default: 4). Applies to --format and --json.",
    )
    args = ap.parse_args()

    if args.yaml or args.format:
        args.json = False

    args.include_comments = False
    if args.format:
        args.include_comments = True
    if args.no_comments:
        args.include_comments = False
    if args.with_comments:
        args.include_comments = True

    try:
        if args.file is None or args.file == "-":
            code = sys.stdin.read()
            ast = getASTfromString(code, include_comments=args.include_comments)
        else:
            ast = getASTfromFile(
                args.file,
                include_comments=args.include_comments,
                process_includes=not args.no_includes,
            )
    except OSError as e:
        print(f"openscad-lalr: {e}", file=sys.stderr)
        sys.exit(1)

    if ast is None:
        sys.exit(1)

    try:
        if args.format:
            print(to_openscad(ast, indent_width=args.indent))
        elif args.yaml:
            try:
                from openscad_lalr_parser import ast_to_yaml
            except ImportError:
                print("openscad-lalr: --yaml requires PyYAML (pip install openscad_lalr_parser[yaml])", file=sys.stderr)
                sys.exit(1)
            print(ast_to_yaml(ast))
        else:
            print(ast_to_json(ast, indent=args.indent))
    except BrokenPipeError:
        sys.exit(0)


if __name__ == "__main__":
    main()
