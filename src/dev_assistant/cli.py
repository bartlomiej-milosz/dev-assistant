"""CLI for indexing one repository and answering questions about its snapshot."""

import subprocess
import sys
from argparse import ArgumentParser
from contextlib import closing
from importlib.metadata import version
from pathlib import Path
from time import monotonic

import httpx
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError

from dev_assistant.corpus import Source
from dev_assistant.model import Ollama
from dev_assistant.service import retrieve, update
from dev_assistant.storage import database


def main() -> None:
    parser = ArgumentParser(prog="dev-assistant", description=__doc__)
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {version('dev-assistant')}"
    )
    commands = parser.add_subparsers(dest="command")
    index = commands.add_parser("update", help="Replace the index with one repository snapshot")
    index.add_argument("--config", type=Path, default=Path("sources.toml"))
    index.add_argument("--commit", help="Index an exact Git SHA for reproducible experiments")
    ask = commands.add_parser("ask", help="Answer one English question with cited evidence")
    ask.add_argument("question")
    ask.add_argument("--method", choices=["text", "vector"], default="text")
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return
    load_dotenv(Path(".env"))
    try:
        engine = database()
        with closing(Ollama()) as model:
            if args.command == "update":
                started = monotonic()
                state, count = update(engine, model, Source.read(args.config), args.commit)
                print(
                    f"Indexed {count} passages at {state.revision} in {monotonic() - started:.1f}s"
                )
            else:
                state, passages = retrieve(engine, model, args.question, args.method)
                answer = model.answer(args.question, passages)
                print(answer.text)
                if answer.source:
                    print(f"\n{answer.quote}\n\n{answer.source.link(state.url, state.revision)}")
    except subprocess.CalledProcessError as exc:
        parser.exit(1, f"Git operation failed: {exc.stderr.decode(errors='replace').strip()}\n")
    except SQLAlchemyError as exc:
        parser.exit(
            1, f"Database operation failed ({type(exc).__name__}). Check make db and .env.\n"
        )
    except (ValueError, OSError, subprocess.TimeoutExpired, httpx.HTTPError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
