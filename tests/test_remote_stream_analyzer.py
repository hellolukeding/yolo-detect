import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "service" / "remote_stream_analyzer.py"
SPEC = importlib.util.spec_from_file_location("remote_stream_analyzer", MODULE_PATH)
remote_stream_analyzer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(remote_stream_analyzer)


class RemoteStreamAnalyzerHelpersTest(unittest.TestCase):
    def test_frame_size_uses_bgr24(self):
        self.assertEqual(remote_stream_analyzer.calculate_frame_size(640, 480), 640 * 480 * 3)

    def test_sdp_content_uses_listen_port(self):
        sdp = remote_stream_analyzer.build_rtp_sdp(5004, "0.0.0.0")
        self.assertIn("m=video 5004 RTP/AVP 96", sdp)
        self.assertIn("c=IN IP4 0.0.0.0", sdp)
        self.assertIn("a=rtpmap:96 H264/90000", sdp)


if __name__ == "__main__":
    unittest.main()
