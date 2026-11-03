import argparse
import sys

import mido
import serial


ROWS = 5
COLUMNS = 8
# Edit this table if the physical keys do not follow row-major order.
KEY_TO_NOTE = {
    (row, column): 48 + (row - 1) * COLUMNS + column - 1
    for row in range(1, ROWS + 1)
    for column in range(1, COLUMNS + 1)
}


def parse_event(line):
    try:
        row, column, state = map(int, line.split(","))
    except ValueError:
        return None
    if (row, column) not in KEY_TO_NOTE or state not in (0, 1):
        return None
    return row, column, state


def handle_event(event, output, active_notes, channel, velocity):
    row, column, state = event
    note = KEY_TO_NOTE[row, column]
    if state and note not in active_notes:
        output.send(mido.Message("note_on", note=note, velocity=velocity, channel=channel))
        active_notes.add(note)
    elif not state and note in active_notes:
        output.send(mido.Message("note_off", note=note, velocity=0, channel=channel))
        active_notes.remove(note)


def bridge(source, output, channel=0, velocity=100):
    active_notes = set()
    pending = b""
    discarding = False
    try:
        while True:
            chunk = source.read_until(b"\n", size=128)
            if not chunk:
                continue
            pending += chunk
            complete = pending.endswith(b"\n")
            if len(pending) > 128:
                discarding = True
            if complete:
                if not discarding:
                    try:
                        event = parse_event(pending.decode("ascii").strip())
                    except UnicodeDecodeError:
                        event = None
                    if event is not None:
                        handle_event(event, output, active_notes, channel, velocity)
                pending = b""
                discarding = False
            elif discarding:
                pending = b""
    finally:
        # Release held keys on Ctrl+C or serial disconnection.
        for note in sorted(active_notes):
            output.send(mido.Message("note_off", note=note, velocity=0, channel=channel))


def bounded_integer(minimum, maximum):
    def parse(value):
        number = int(value)
        if not minimum <= number <= maximum:
            raise argparse.ArgumentTypeError(f"must be between {minimum} and {maximum}")
        return number

    return parse


def main():
    parser = argparse.ArgumentParser(description="Bridge an Arduino key matrix to virtual MIDI.")
    parser.add_argument("--port", default="/dev/ttyACM0", help="serial device")
    parser.add_argument("--baud", type=bounded_integer(1, 4_000_000), default=9600)
    parser.add_argument("--name", default="Arduino MIDI Keyboard", help="virtual MIDI port name")
    parser.add_argument("--channel", type=bounded_integer(1, 16), default=1)
    parser.add_argument("--velocity", type=bounded_integer(1, 127), default=100)
    args = parser.parse_args()

    try:
        mido.set_backend("mido.backends.rtmidi")
        with serial.Serial(args.port, args.baud, timeout=0.1, exclusive=True) as source:
            with mido.open_output(args.name, virtual=True) as output:
                print(
                    f"{args.port} at {args.baud} baud -> {args.name}. "
                    "Select this MIDI input in your DAW; Ctrl+C to stop.",
                    flush=True,
                )
                bridge(source, output, args.channel - 1, args.velocity)
    except KeyboardInterrupt:
        return 0
    except (serial.SerialException, OSError, RuntimeError) as error:
        print(f"Could not run MIDI bridge: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
