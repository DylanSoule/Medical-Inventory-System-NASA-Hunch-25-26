import threading
import subprocess
import os
from kivy.clock import Clock
from deepgram import DeepgramClient
from deepgram.core.events import EventType

DEEPGRAM_API_KEY = os.environ.get(
    "DEEPGRAM_API_KEY",
    "18e10017609ade313ab766c4bf33ba2ce2ba5e7a",
)
SAMPLE_RATE = 16000
CHUNK_BYTES = 8000  # 0.25 s of 16-bit mono @ 16 kHz
WAKE_WORD = "helios"

# Lock to prevent triggering a command while one is already running
_action_busy = threading.Lock()


def start_voice_listener(screen):
    """Start a background thread that streams mic audio to Deepgram
    and triggers actions on the given Kivy MainScreen.

    Parameters
    ----------
    screen : MainScreen
        The Kivy screen instance whose methods will be called
        (log_item_use, personal_run, set_mic_status, etc.).
    """
    thread = threading.Thread(
        target=_voice_loop,
        args=(screen,),
        daemon=True,
    )
    thread.start()
    return thread


def _handle_transcript(text, screen):
    """Parse transcript for wake-word + command, dispatch to screen."""
    cleaned = text.lower().strip()
    if not cleaned:
        return

    print(f"[VOICE] heard: {cleaned}")

    if WAKE_WORD not in cleaned:
        return

    command = cleaned.split(WAKE_WORD, 1)[1].strip()

    if "log scan" in command:
        if not _action_busy.acquire(blocking=False):
            print("[VOICE] ignored 'log scan' — action already in progress")
            return
        print("[VOICE] → triggering Log Item Use")

        def _do(dt):
            try:
                screen.log_item_use()
            finally:
                _action_busy.release()

        Clock.schedule_once(_do, 0)

    elif "personal database" in command:
        if not _action_busy.acquire(blocking=False):
            print("[VOICE] ignored 'personal database' — action already in progress")
            return
        print("[VOICE] → triggering Personal Database")

        def _do(dt):
            try:
                screen.personal_run()
            finally:
                _action_busy.release()

        Clock.schedule_once(_do, 0)


def _voice_loop(screen):
    """Blocking loop (runs in daemon thread).
    Captures mic via arecord, streams to Deepgram v1, dispatches commands.
    """
    print("[VOICE] Starting voice recognition...")

    try:
        mic = subprocess.Popen(
            [
                "arecord",
                "-f", "S16_LE",
                "-r", str(SAMPLE_RATE),
                "-c", "1",
                "-t", "raw",
                "-q",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )

        client = DeepgramClient(api_key=DEEPGRAM_API_KEY)

        with client.listen.v1.connect(
            model="nova-3",
            encoding="linear16",
            sample_rate=str(SAMPLE_RATE),
            keyterm=["helios", "log scan", "personal database"],
            interim_results="false",
            punctuate="false",
        ) as connection:

            def on_open(_msg):
                print("[VOICE] Deepgram connection opened")
                Clock.schedule_once(
                    lambda dt: screen.set_mic_status("listening"), 0
                )

            def on_message(msg):
                try:
                    transcript = msg.channel.alternatives[0].transcript
                    _handle_transcript(transcript, screen)
                except (AttributeError, IndexError):
                    pass

            def on_error(err):
                print(f"[VOICE] Deepgram error: {err}")
                Clock.schedule_once(
                    lambda dt: screen.set_mic_status("error"), 0
                )

            def on_close(_msg):
                print("[VOICE] Deepgram connection closed")
                Clock.schedule_once(
                    lambda dt: screen.set_mic_status("off"), 0
                )
                mic.terminate()

            connection.on(EventType.OPEN, on_open)
            connection.on(EventType.MESSAGE, on_message)
            connection.on(EventType.ERROR, on_error)
            connection.on(EventType.CLOSE, on_close)

            def _feed_audio():
                try:
                    while True:
                        chunk = mic.stdout.read(CHUNK_BYTES)
                        if not chunk:
                            break
                        connection.send_media(chunk)
                except Exception:
                    pass

            feeder = threading.Thread(target=_feed_audio, daemon=True)
            feeder.start()

            print("[VOICE] Microphone active — say 'helios log scan'")
            connection.start_listening()

    except Exception as exc:
        print(f"[VOICE] Voice recognition failed: {exc}")
        Clock.schedule_once(
            lambda dt: screen.set_mic_status("error"), 0
        )
