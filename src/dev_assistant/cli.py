"""Console entry point for Dev Assistant."""

from argparse import ArgumentParser
from importlib.metadata import version


def main() -> None:
    parser = ArgumentParser(
        prog="dev-assistant",
        description="Dev Assistant for local repository Q&A. Project scaffold.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {version('dev-assistant')}"
    )
    parser.parse_args()
    parser.print_help()
