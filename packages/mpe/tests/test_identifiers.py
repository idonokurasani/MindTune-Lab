"""Canonical identifier type tests."""

from __future__ import annotations

import unittest

from mpe.types import (
    EventID,
    ProgramID,
    SessionID,
    make_id,
)


class IdentifierTests(unittest.TestCase):
    def test_valid_identifier(self) -> None:
        sid = SessionID("session-abc")
        self.assertEqual(str(sid), "session-abc")
        self.assertEqual(sid.value, "session-abc")

    def test_empty_identifier_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ProgramID("")
        with self.assertRaises(ValueError):
            EventID("")

    def test_identifier_type_safety(self) -> None:
        sid = SessionID("same-value")
        pid = ProgramID("same-value")
        # Same string value but different types.
        self.assertEqual(str(sid), str(pid))
        self.assertNotIsInstance(sid, ProgramID)
        self.assertNotIsInstance(pid, SessionID)

    def test_make_id_creates_typed_uuids(self) -> None:
        sid = make_id(SessionID)
        self.assertIsInstance(sid, SessionID)
        self.assertEqual(len(sid.value), 36)

    def test_identifiers_are_hashable(self) -> None:
        s1 = SessionID("s1")
        s2 = SessionID("s1")
        self.assertEqual(hash(s1), hash(s2))
        self.assertEqual(s1, s2)
