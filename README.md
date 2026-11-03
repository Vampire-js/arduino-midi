# Arduino MIDI keyboard

Reads newline-terminated `row,column,state` events from `/dev/ttyACM0` and
creates an ALSA virtual MIDI output named **Arduino MIDI Keyboard**, which DAWs
can select as a MIDI input while the script is running. This is a software MIDI
port, not a USB MIDI device or an audio source.

## Run on Linux

```sh
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python main.py
```

Alternatively, with uv installed: `uv run main.py`.

Enable **Arduino MIDI Keyboard** as an input in your DAW and arm a track with a
software instrument. ALSA MIDI must be available (`/dev/snd/seq`). If the DAW
only exposes JACK/PipeWire MIDI, enable its ALSA MIDI bridge. Sandboxed DAWs
also need access to host MIDI devices.

The firmware in `main.c` transmits at **9600 baud**; the upload baud rate in
`run.sh` is unrelated. To use different settings:

```sh
.venv/bin/python main.py --port /dev/ttyACM0 --baud 9600 --channel 1 --velocity 100
```

Close serial monitors before starting. If access is denied, grant your user
access to the serial device (usually membership in `dialout`, followed by a
new login); do not run the DAW or bridge as root.

## Key mapping

Rows and columns are **1-based**. The default mapping assigns ascending
chromatic notes row-by-row:

| Row | Columns 1-8: MIDI note numbers |
|-----|-------------------------------|
| 1 | 48-55 |
| 2 | 56-63 |
| 3 | 64-71 |
| 4 | 72-79 |
| 5 | 80-87 |

Note 48 is C3 when middle C (60) is called C4; octave labels vary by DAW.
Edit `KEY_TO_NOTE` in `main.py` to match your physical wiring, using unique
MIDI note numbers from 0 to 127 for all 40 coordinates.

For example, `1,1,1` sends note-on for note 48 and `1,1,0` sends note-off.
Malformed events and duplicate states are ignored. Held notes are released
on Ctrl+C or serial disconnection. The current firmware only reports `(1,1)`;
it must scan the full matrix to use all 40 keys.