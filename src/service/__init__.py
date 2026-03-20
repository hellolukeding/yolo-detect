__all__ = ["PushStreamer", "FFmpegPushStreamer", "RemoteStreamAnalyzer"]


def __getattr__(name):
    if name == "PushStreamer":
        from .push_streamer import PushStreamer

        return PushStreamer
    if name == "FFmpegPushStreamer":
        from .push_streamer_ffmpeg import FFmpegPushStreamer

        return FFmpegPushStreamer
    if name == "RemoteStreamAnalyzer":
        from .remote_stream_analyzer import RemoteStreamAnalyzer

        return RemoteStreamAnalyzer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
