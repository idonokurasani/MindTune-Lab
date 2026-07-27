"""MPE command-line interface."""

from __future__ import annotations

import argparse
import sys
import traceback
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from mpe.aggregates import RuntimeState
from mpe.cli_helpers import (
    DEFAULT_STORE_PATH,
    ENV_STORE_PATH,
    format_json,
    load_protocol_summary,
    load_recognition_summary,
    log_verbose,
    open_store,
    replay_session,
    resolve_store_path,
    run_immediate_recall,
    run_mock_session,
    run_recognition,
)
from mpe.errors import (
    ConcurrencyError,
    EventOrderingError,
    IllegalStateTransitionError,
    MPEError,
    ProviderFailureError,
    ProviderNotFoundError,
    ProviderTimeoutError,
    ProviderVersionMismatchError,
    ReplayError,
    UnknownEventTypeError,
    UnknownSchemaVersionError,
    UnsupportedProviderVersionError,
    ValidationError,
)
from mpe.persistence.interchange import import_stream, write_stream
from mpe.persistence.store import SQLiteEventStore
from mpe.types import SessionID

try:
    from importlib.metadata import version as get_version

    __version__ = get_version("mpe")
except Exception:  # pragma: no cover - fallback during local development
    __version__ = "0.1.0"


EXIT_OK = 0
EXIT_INTERNAL = 1
EXIT_USAGE = 2
EXIT_NOT_FOUND = 3
EXIT_STORE_INVALID = 4
EXIT_CONCURRENCY = 5
EXIT_INVARIANT = 6


def _store_path_from(args: argparse.Namespace) -> Path:
    path = resolve_store_path(args.store_path if args.store_path else None)
    return path


def _ensure_path_is_not_directory(path: Path) -> int | None:
    if path.is_dir():
        print(f"error: store path is a directory: {path}", file=sys.stderr)
        return EXIT_USAGE
    return None


def _open_store_for_command(
    path: Path, *, read_only: bool = False
) -> SQLiteEventStore | int:
    bad = _ensure_path_is_not_directory(path)
    if bad is not None:
        return bad
    if read_only and not path.exists():
        print(f"error: event store not found: {path}", file=sys.stderr)
        return EXIT_NOT_FOUND
    try:
        return open_store(path)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return _exit_code_for(exc)


def _safe_session_id(value: str) -> SessionID | int:
    try:
        return SessionID(value)
    except ValueError as exc:
        print(f"error: invalid session ID: {exc}", file=sys.stderr)
        return EXIT_USAGE


def _output(data: object, args: argparse.Namespace) -> None:
    if args.format == "json":
        print(format_json(data))
    else:
        print(data)


def _output_json(data: object, args: argparse.Namespace) -> None:
    """Emit a JSON document if --format json, otherwise the human string."""
    if args.format == "json":
        print(format_json(data))
    else:
        print(str(data))


def _exit_code_for(exc: BaseException) -> int:
    if isinstance(exc, ConcurrencyError):
        return EXIT_CONCURRENCY
    if isinstance(
        exc,
        (
            ValidationError,
            UnknownSchemaVersionError,
            UnknownEventTypeError,
            EventOrderingError,
            ReplayError,
        ),
    ):
        return EXIT_STORE_INVALID
    if isinstance(
        exc,
        (
            IllegalStateTransitionError,
            ProviderFailureError,
            ProviderNotFoundError,
            ProviderTimeoutError,
            ProviderVersionMismatchError,
            UnsupportedProviderVersionError,
        ),
    ):
        return EXIT_INVARIANT
    if isinstance(exc, MPEError):
        return EXIT_INTERNAL
    return EXIT_INTERNAL


def _format_state_summary(state: RuntimeState) -> str:
    event_count = len(state.events)
    trial_count = len(state.trials)
    block_count = len(state.blocks)
    status = state.session_status.value if state.session_status else "unknown"
    return (
        f"Session: {state.session_id}\n"
        f"Status: {status}\n"
        f"Terminal: {state.terminal}\n"
        f"Trials: {trial_count}\n"
        f"Blocks: {block_count}\n"
        f"Events: {event_count}"
    )


def cmd_run_mock_session(args: argparse.Namespace) -> int:
    path = _store_path_from(args)
    bad = _ensure_path_is_not_directory(path)
    if bad is not None:
        return bad

    session_id: SessionID | None = None
    if args.session_id:
        parsed = _safe_session_id(args.session_id)
        if isinstance(parsed, int):
            return parsed
        session_id = parsed

    if args.verbose:
        log_verbose(f"Resolved store path: {path}")

    was_new = not path.exists()
    try:
        with open_store(path) as store:
            if was_new:
                log_verbose(f"Created new event store at {path}")
            elif args.verbose:
                log_verbose(f"Opened existing event store at {path}")

            state = run_mock_session(
                store,
                session_id=session_id,
                learner_id=args.learner_id,
                random_seed=args.random_seed,
            )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc(file=sys.stderr)
        return _exit_code_for(exc)

    event_count = len(state.events)
    status = state.session_status.value if state.session_status else "unknown"
    assert state.session_id is not None
    result = {
        "session_id": str(state.session_id),
        "event_count": event_count,
        "status": status,
        "terminal": state.terminal,
    }

    if args.format == "json":
        print(format_json(result))
    else:
        print(f"Session: {result['session_id']}")
        print(f"Events: {event_count}")
        print(f"Status: {status}")
        print(f"Terminal: {state.terminal}")

    return EXIT_OK


def cmd_replay(args: argparse.Namespace) -> int:
    path = _store_path_from(args)
    parsed = _safe_session_id(args.session_id)
    if isinstance(parsed, int):
        return parsed
    session_id = parsed

    if args.verbose:
        log_verbose(f"Resolved store path: {path}")

    opened = _open_store_for_command(path, read_only=True)
    if isinstance(opened, int):
        return opened

    try:
        with opened as store:
            if args.verbose:
                log_verbose(f"Opened event store at {path}")
            if store.get_last_sequence(session_id) == 0:
                print(f"error: no events found for session {session_id}", file=sys.stderr)
                return EXIT_NOT_FOUND
            state = replay_session(store, session_id)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc(file=sys.stderr)
        return _exit_code_for(exc)

    if args.format == "json":
        print(format_json(state.as_dict()))
    else:
        print(_format_state_summary(state))

    return EXIT_OK


def cmd_list_sessions(args: argparse.Namespace) -> int:
    path = _store_path_from(args)
    if args.verbose:
        log_verbose(f"Resolved store path: {path}")

    opened = _open_store_for_command(path, read_only=True)
    if isinstance(opened, int):
        return opened

    try:
        with opened as store:
            if args.verbose:
                log_verbose(f"Opened event store at {path}")
            sessions = store.list_sessions()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc(file=sys.stderr)
        return _exit_code_for(exc)

    data = [
        {
            "session_id": str(summary.session_id),
            "event_count": summary.event_count,
            "last_sequence": summary.last_sequence,
        }
        for summary in sessions
    ]

    if args.format == "json":
        print(format_json(data))
    else:
        for summary in sessions:
            print(f"{summary.session_id}  {summary.event_count}  {summary.last_sequence}")

    return EXIT_OK


def cmd_validate_store(args: argparse.Namespace) -> int:
    path = _store_path_from(args)
    if args.verbose:
        log_verbose(f"Resolved store path: {path}")

    opened = _open_store_for_command(path, read_only=True)
    if isinstance(opened, int):
        return opened

    event_count = 0
    session_count = 0
    sessions_data: list[dict[str, object]] = []
    error_message: str | None = None

    try:
        with opened as store:
            if args.verbose:
                log_verbose(f"Opened event store at {path}")
            sessions = store.list_sessions()
            for summary in sessions:
                state = replay_session(store, summary.session_id)
                event_count += summary.event_count
                session_count += 1
                sessions_data.append(
                    {
                        "session_id": str(summary.session_id),
                        "event_count": summary.event_count,
                        "last_sequence": summary.last_sequence,
                        "status": (
                            state.session_status.value
                            if state.session_status
                            else None
                        ),
                        "terminal": state.terminal,
                    }
                )
    except Exception as exc:
        error_message = str(exc)
        if args.verbose:
            traceback.print_exc(file=sys.stderr)

    valid = error_message is None
    result = {
        "valid": valid,
        "event_count": event_count,
        "session_count": session_count,
        "sessions": sessions_data,
        "error": error_message,
    }

    if args.format == "json":
        print(format_json(result))
    else:
        if valid:
            print(f"store valid: {event_count} events, {session_count} sessions")
        else:
            print(f"store invalid: {error_message}")

    return EXIT_OK if valid else EXIT_STORE_INVALID




def _format_protocol_summary(summary: Any) -> str:
    """Human-readable rendering of an Immediate Recall protocol summary."""
    lines = [
        f"Session: {summary.session_id}",
        f"Protocol: {summary.protocol_id}",
        f"Fixture: {summary.fixture_id}",
        f"Status: {summary.status}",
        f"Items: {summary.item_count} ({summary.completed_item_count} completed, {summary.unresolved_count} unresolved)",
        f"Total repeats: {summary.total_repeats}",
        f"Events: {summary.event_count}",
    ]
    for item in summary.items:
        lines.append(
            f"  {item.content_item_id}: {item.outcome} "
            f"(self_confirmation={item.self_confirmation}, repeats={item.repeats_used}, "
            f"latency={item.latency})"
        )
    return "\n".join(lines)


def _format_recognition_summary(summary: Any) -> str:
    """Human-readable rendering of a Recognition protocol summary."""
    lines = [
        f"Session: {summary.session_id}",
        f"Protocol: {summary.protocol_id}",
        f"Fixture: {summary.fixture_id}",
        f"Status: {summary.status}",
        f"Items: {summary.item_count} ({summary.completed_item_count} completed, {summary.correct_count} correct)",
        f"Total repeats: {summary.total_repeats}",
        f"Events: {summary.event_count}",
    ]
    for item in summary.items:
        correct_marker = "correct" if item.correct else item.outcome
        lines.append(
            f"  {item.content_item_id}: {correct_marker} "
            f"(selected={item.selected_choice_index}, correct={item.correct_choice_index}, "
            f"repeats={item.repeats_used}, latency={item.latency})"
        )
    return "\n".join(lines)


def _run_protocol_session(
    args: argparse.Namespace,
    runner: Callable[..., tuple[Any, Any]],
    formatter: Callable[[Any], str],
) -> int:
    """Shared mechanics for the explicit protocol run commands."""
    path = _store_path_from(args)
    bad = _ensure_path_is_not_directory(path)
    if bad is not None:
        return bad

    session_id: SessionID | None = None
    if args.session_id:
        parsed = _safe_session_id(args.session_id)
        if isinstance(parsed, int):
            return parsed
        session_id = parsed

    if args.verbose:
        log_verbose(f"Resolved store path: {path}")

    was_new = not path.exists()
    try:
        with open_store(path) as store:
            if was_new:
                log_verbose(f"Created new event store at {path}")
            elif args.verbose:
                log_verbose(f"Opened existing event store at {path}")

            _state, summary = runner(
                store,
                session_id=session_id,
                learner_id=args.learner_id,
                random_seed=args.random_seed,
            )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc(file=sys.stderr)
        return _exit_code_for(exc)

    if args.format == "json":
        print(format_json(summary.as_dict()))
    else:
        print(formatter(summary))

    return EXIT_OK


def _show_protocol_session_summary(
    args: argparse.Namespace,
    loader: Callable[[Any, SessionID], Any],
    formatter: Callable[[Any], str],
) -> int:
    """Shared mechanics for the explicit summary commands."""
    path = _store_path_from(args)
    parsed = _safe_session_id(args.session_id)
    if isinstance(parsed, int):
        return parsed
    session_id = parsed

    if args.verbose:
        log_verbose(f"Resolved store path: {path}")

    opened = _open_store_for_command(path, read_only=True)
    if isinstance(opened, int):
        return opened

    try:
        with opened as store:
            if args.verbose:
                log_verbose(f"Opened event store at {path}")
            if store.get_last_sequence(session_id) == 0:
                print(f"error: no events found for session {session_id}", file=sys.stderr)
                return EXIT_NOT_FOUND
            summary = loader(store, session_id)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc(file=sys.stderr)
        return _exit_code_for(exc)

    if args.format == "json":
        print(format_json(summary.as_dict()))
    else:
        print(formatter(summary))

    return EXIT_OK


def cmd_run_immediate_recall(args: argparse.Namespace) -> int:
    return _run_protocol_session(args, run_immediate_recall, _format_protocol_summary)


def cmd_show_protocol_summary(args: argparse.Namespace) -> int:
    return _show_protocol_session_summary(
        args, load_protocol_summary, _format_protocol_summary
    )


def cmd_run_recognition(args: argparse.Namespace) -> int:
    return _run_protocol_session(args, run_recognition, _format_recognition_summary)


def cmd_show_recognition_summary(args: argparse.Namespace) -> int:
    return _show_protocol_session_summary(
        args, load_recognition_summary, _format_recognition_summary
    )


def cmd_export_session(args: argparse.Namespace) -> int:
    path = _store_path_from(args)
    if args.verbose:
        log_verbose(f"Resolved store path: {path}")

    session_id = _safe_session_id(args.session_id)
    if isinstance(session_id, int):
        return session_id

    opened = _open_store_for_command(path, read_only=True)
    if isinstance(opened, int):
        return opened

    out_path = Path(args.out)
    try:
        with opened as store:
            if store.get_last_sequence(session_id) == 0:
                print(f"error: session not found: {session_id}", file=sys.stderr)
                return EXIT_NOT_FOUND
            with out_path.open("wb") as handle:
                count = write_stream(store, session_id, handle)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc(file=sys.stderr)
        return _exit_code_for(exc)

    _output_json(
        {"session_id": str(session_id), "event_count": count, "out": str(out_path)},
        args,
    )
    return EXIT_OK


def cmd_import_session(args: argparse.Namespace) -> int:
    path = _store_path_from(args)
    if args.verbose:
        log_verbose(f"Resolved store path: {path}")

    in_path = Path(getattr(args, "in"))
    if not in_path.exists():
        print(f"error: interchange file not found: {in_path}", file=sys.stderr)
        return EXIT_NOT_FOUND

    opened = _open_store_for_command(path)
    if isinstance(opened, int):
        return opened

    try:
        with opened as store, in_path.open("rb") as handle:
            count = import_stream(store, handle)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc(file=sys.stderr)
        return _exit_code_for(exc)

    _output_json({"event_count": count, "store": str(path)}, args)
    return EXIT_OK


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mpe",
        description="MindTune Protocol Engine (MPE) v1.1 CLI",
    )
    parser.add_argument("--version", action="version", version=f"mpe {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Emit diagnostic output to stderr")
    parser.add_argument(
        "--store-path",
        default=None,
        help=f"SQLite event-store path (env: {ENV_STORE_PATH}, default: {DEFAULT_STORE_PATH})",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run-mock-session", help="Execute and persist the mock session")
    run_parser.add_argument("--session-id", default=None, help="Fixed session identifier")
    run_parser.add_argument("--learner-id", default="learner_001", help="Learner identifier")
    run_parser.add_argument("--random-seed", default="seed_0", help="Random seed")
    run_parser.add_argument("--format", choices=["human", "json"], default="human", help="Output format")

    replay_parser = subparsers.add_parser("replay", help="Replay a persisted session")
    replay_parser.add_argument("session_id", help="Session identifier")
    replay_parser.add_argument("--format", choices=["human", "json"], default="human", help="Output format")

    list_parser = subparsers.add_parser("list-sessions", help="List sessions in the store")
    list_parser.add_argument("--format", choices=["human", "json"], default="human", help="Output format")

    validate_parser = subparsers.add_parser("validate-store", help="Validate the event store")
    validate_parser.add_argument("--format", choices=["human", "json"], default="human", help="Output format")

    immediate_recall_parser = subparsers.add_parser(
        "run-immediate-recall", help="Execute and persist an Immediate Recall session"
    )
    immediate_recall_parser.add_argument("--session-id", default=None, help="Fixed session identifier")
    immediate_recall_parser.add_argument("--learner-id", default="learner_001", help="Learner identifier")
    immediate_recall_parser.add_argument("--random-seed", default="seed_0", help="Random seed")
    immediate_recall_parser.add_argument(
        "--format", choices=["human", "json"], default="human", help="Output format"
    )

    show_summary_parser = subparsers.add_parser(
        "show-protocol-summary", help="Show the Immediate Recall protocol summary for a session"
    )
    show_summary_parser.add_argument("session_id", help="Session identifier")
    show_summary_parser.add_argument(
        "--format", choices=["human", "json"], default="human", help="Output format"
    )

    recognition_parser = subparsers.add_parser(
        "run-recognition", help="Execute and persist a Recognition session"
    )
    recognition_parser.add_argument("--session-id", default=None, help="Fixed session identifier")
    recognition_parser.add_argument("--learner-id", default="learner_001", help="Learner identifier")
    recognition_parser.add_argument("--random-seed", default="seed_0", help="Random seed")
    recognition_parser.add_argument(
        "--format", choices=["human", "json"], default="human", help="Output format"
    )

    export_parser = subparsers.add_parser(
        "export-session", help="Export one session as canonical JSONL records"
    )
    export_parser.add_argument("--session-id", required=True, help="Session identifier")
    export_parser.add_argument("--out", required=True, help="Destination .jsonl file")
    export_parser.add_argument(
        "--format", choices=["human", "json"], default="human", help="Output format"
    )

    import_parser = subparsers.add_parser(
        "import-session", help="Import a session from canonical JSONL records"
    )
    import_parser.add_argument("--in", required=True, help="Source .jsonl file")
    import_parser.add_argument(
        "--format", choices=["human", "json"], default="human", help="Output format"
    )

    show_recognition_parser = subparsers.add_parser(
        "show-recognition-summary", help="Show the Recognition protocol summary for a session"
    )
    show_recognition_parser.add_argument("session_id", help="Session identifier")
    show_recognition_parser.add_argument(
        "--format", choices=["human", "json"], default="human", help="Output format"
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    command_map = {
        "run-mock-session": cmd_run_mock_session,
        "run-immediate-recall": cmd_run_immediate_recall,
        "show-protocol-summary": cmd_show_protocol_summary,
        "run-recognition": cmd_run_recognition,
        "show-recognition-summary": cmd_show_recognition_summary,
        "replay": cmd_replay,
        "list-sessions": cmd_list_sessions,
        "validate-store": cmd_validate_store,
        "export-session": cmd_export_session,
        "import-session": cmd_import_session,
    }

    command = command_map.get(args.command)
    if command is None:
        # argparse with required subparsers should prevent this, but keep defensive.
        print(f"error: unknown command: {args.command}", file=sys.stderr)
        return EXIT_USAGE

    return command(args)


if __name__ == "__main__":
    sys.exit(main())
