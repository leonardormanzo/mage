import unittest
from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from calendar_app.ai_parser import AppointmentParser, AppointmentResult


class FakeResponses:
    def __init__(self, result):
        self.result = result

    def parse(self, **_kwargs):
        return SimpleNamespace(output_parsed=self.result)


class FakeClient:
    def __init__(self, result):
        self.responses = FakeResponses(result)


class AppointmentParserTests(unittest.TestCase):
    def test_parses_structured_appointment(self):
        result = AppointmentResult(
            understood=True,
            title="Reunião com o cliente",
            start="2026-07-25T14:00:00-03:00",
            end="2026-07-25T15:00:00-03:00",
        )
        parser = AppointmentParser(FakeClient(result))
        parsed = parser.parse(
            "reunião com o cliente amanhã às 14h",
            datetime(2026, 7, 24, 10, tzinfo=ZoneInfo("America/Sao_Paulo")),
        )
        self.assertEqual(parsed.title, "Reunião com o cliente")
        self.assertEqual(parsed.start.hour, 14)

    def test_rejects_ambiguous_text(self):
        parser = AppointmentParser(FakeClient(AppointmentResult(
            understood=False, title=None, start=None, end=None,
        )))
        with self.assertRaisesRegex(ValueError, "Não entendi"):
            parser.parse("marcar uma coisa")


if __name__ == "__main__":
    unittest.main()
