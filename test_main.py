import unittest

import serial

from main import bridge, handle_event, parse_event


class Output:
    def __init__(self):
        self.messages = []

    def send(self, message):
        self.messages.append(message)


class Source:
    def __init__(self, chunks):
        self.chunks = iter(chunks)

    def read_until(self, expected, size):
        try:
            return next(self.chunks)
        except StopIteration:
            raise serial.SerialException("disconnected")


class BridgeTests(unittest.TestCase):
    def test_parsing(self):
        self.assertEqual(parse_event(" 5, 8, 1 "), (5, 8, 1))
        for line in ("0,1,1", "6,1,1", "1,9,1", "1,1,2", "a,1,1", "1,1", "1,1,1,1"):
            with self.subTest(line=line):
                self.assertIsNone(parse_event(line))

    def test_polyphony_duplicate_states_and_mapping(self):
        output = Output()
        active = set()
        for event in ((1, 1, 0), (1, 1, 1), (1, 1, 1), (5, 8, 1), (1, 1, 0), (1, 1, 0)):
            handle_event(event, output, active, channel=2, velocity=90)
        self.assertEqual(
            [(m.type, m.note, m.velocity, m.channel) for m in output.messages],
            [("note_on", 48, 90, 2), ("note_on", 87, 90, 2), ("note_off", 48, 0, 2)],
        )
        self.assertEqual(active, {87})

    def test_partial_lines_invalid_input_and_disconnect_cleanup(self):
        source = Source([
            b"1,", b"", b"1,1\r\n", b"\xff\n", b"invalid\n",
            b"x" * 128, b"x" * 128, b"5,8,1\n", b"5,8,1\n",
            b"1,1,0\n",
        ])
        output = Output()
        with self.assertRaises(serial.SerialException):
            bridge(source, output)
        self.assertEqual(
            [(m.type, m.note) for m in output.messages],
            [("note_on", 48), ("note_on", 87), ("note_off", 48), ("note_off", 87)],
        )

    def test_interrupt_releases_held_notes(self):
        class InterruptedSource:
            calls = 0

            def read_until(self, expected, size):
                self.calls += 1
                if self.calls == 1:
                    return b"1,1,1\n"
                raise KeyboardInterrupt

        output = Output()
        with self.assertRaises(KeyboardInterrupt):
            bridge(InterruptedSource(), output)
        self.assertEqual([m.type for m in output.messages], ["note_on", "note_off"])


if __name__ == "__main__":
    unittest.main()
