import webbrowser

music = {
    "music": "https://youtu.be/NYmkY7d6PE8?si=Q60sIagCVKgI0dSp",
    "music2": "https://youtu.be/TFTnJzWRTJ8?si=tbXPPfedWGekq00F",
}


def list_tracks():
    """Return the available track names."""
    return list(music.keys())


def play_track(name: str) -> bool:
    """Open the track in the default web browser."""
    url = music.get(name)
    if url:
        webbrowser.open(url)
        return True
    return False
