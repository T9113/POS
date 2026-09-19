import sys
import threading

def play_beep(sound_type: str = "beep"):
    """
    Plays non-blocking sound effect on Windows.
    sound_type: 'beep' (scanner), 'success' (sale complete), 'error' (warning)
    """
    if sys.platform != "win32":
        return

    def _play():
        try:
            import winsound
            if sound_type == "beep":
                winsound.Beep(1800, 100)
            elif sound_type == "success":
                winsound.Beep(1200, 120)
                winsound.Beep(1800, 150)
            elif sound_type == "error":
                winsound.Beep(400, 250)
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()
