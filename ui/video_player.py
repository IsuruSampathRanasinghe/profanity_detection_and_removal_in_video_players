"""Compatibility layer that re-exports the modularized UI controller."""

from ui.main_window import VideoPlayer, launch_video_player


__all__ = ["VideoPlayer", "launch_video_player"]


if __name__ == "__main__":
    launch_video_player()
