import threading
import subprocess
import os
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


def start_voice_listener(app):

    thread = threading.Thread(
        target=_voice_loop,
        args=(app,),
        daemon=True,
    )
    thread.start()
    return thread


def _handle_transcript(text, app):
    """
    Check the transcript for the wake word + a known command and
    trigger the corresponding GUI action on the main (Tk) thread.
    Ignores commands while a previous action is still in progress.
    """
    cleaned = text.lower().strip()
    if not cleaned:
        return



    if WAKE_WORD not in cleaned:
        return


    command = cleaned.split(WAKE_WORD, 1)[1].strip()

    if "log scan" in command:
        # Don't open another dialog if one is already active
        if not _action_busy.acquire(blocking=False):
            print("[VOICE] ignored 'log scan'  action already in progress")
            return
        print("[VOICE] → triggering Log Item Use")

        def _do_log_scan():
            try:
                app.log_item_use()
            finally:
                _action_busy.release()

        app.after(0, _do_log_scan)


def _voice_loop(app):

    print("[VOICE] Starting voice recognition")

    try:
        # Start mic capture using arecord (ships with alsa-utils)
        mic = subprocess.Popen(
            [
                "arecord",
                "-f", "S16_LE",      
                "-r", str(SAMPLE_RATE),
                "-c", "1",            # mono
                "-t", "raw",          # raw PCM, no WAV header
                "-q",                 # quiet, no status output
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )

        client = DeepgramClient(api_key=DEEPGRAM_API_KEY)

        with client.listen.v1.connect(
            model="nova-3",
            encoding="linear16",
            sample_rate=str(SAMPLE_RATE),
            keyterm=["helios", "log scan"],
            interim_results="false",
            punctuate="false",
        ) as connection:

            def on_open(_msg):
                print("[VOICE] Deepgram connection opened")
                app.after(0, lambda: app.set_mic_status("listening"))

            def on_message(msg):
                # v1 results: msg.channel.alternatives[0].transcript
                try:
                    transcript = msg.channel.alternatives[0].transcript
                    _handle_transcript(transcript, app)
                except (AttributeError, IndexError):
                    pass

            def on_error(err):
                print(f"[VOICE] Deepgram error: {err}")
                app.after(0, lambda: app.set_mic_status("error"))

            def on_close(_msg):
                print("[VOICE] Deepgram connection closed")
                app.after(0, lambda: app.set_mic_status("off"))
                mic.terminate()

            connection.on(EventType.OPEN, on_open)
            connection.on(EventType.MESSAGE, on_message)
            connection.on(EventType.ERROR, on_error)
            connection.on(EventType.CLOSE, on_close)

            # Feed mic audio to Deepgram in a separate reader thread
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


            connection.start_listening()  # blocks until connection closes

    except Exception as exc:
        print(f"[VOICE] Voice recognition failed: {exc}")
        app.after(0, lambda: app.set_mic_status("error"))