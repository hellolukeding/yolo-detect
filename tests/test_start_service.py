import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "deploy" / "scripts" / "start_service.py"
SPEC = importlib.util.spec_from_file_location("start_service", MODULE_PATH)
start_service = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(start_service)


class ResolveCameraDeviceTest(unittest.TestCase):
    def test_usb_numeric_index_keeps_index(self):
        self.assertEqual(start_service.resolve_camera_device("usb", "4"), 4)

    def test_usb_device_path_keeps_path(self):
        self.assertEqual(
            start_service.resolve_camera_device("usb", "/dev/video4"),
            "/dev/video4",
        )

    def test_rtsp_keeps_url(self):
        self.assertEqual(
            start_service.resolve_camera_device("rtsp", "rtsp://example.com/live"),
            "rtsp://example.com/live",
        )

    def test_unknown_usb_string_is_not_forced_to_zero(self):
        self.assertEqual(
            start_service.resolve_camera_device("usb", "/dev/v4l/by-id/camera0"),
            "/dev/v4l/by-id/camera0",
        )


class ServiceRoleTest(unittest.TestCase):
    def test_default_role_is_integrated(self):
        settings = start_service.build_runtime_settings({})
        self.assertEqual(settings["service_role"], "integrated")

    def test_edge_role_uses_push_target(self):
        settings = start_service.build_runtime_settings(
            {
                "SERVICE_ROLE": "edge",
                "CAMERA_TYPE": "usb",
                "CAMERA_DEVICE": "/dev/video4",
                "PUSH_HOST": "10.0.0.2",
                "PUSH_PORT": "6000",
            }
        )

        self.assertEqual(settings["service_role"], "edge")
        self.assertEqual(settings["camera_device"], "/dev/video4")
        self.assertEqual(settings["push_host"], "10.0.0.2")
        self.assertEqual(settings["push_port"], 6000)

    def test_server_role_uses_listen_target(self):
        settings = start_service.build_runtime_settings(
            {
                "SERVICE_ROLE": "server",
                "LISTEN_HOST": "0.0.0.0",
                "LISTEN_PORT": "7000",
                "MODEL_PATH": "models/person_detector.pt",
                "VIDEO_WIDTH": "640",
                "VIDEO_HEIGHT": "480",
            }
        )

        self.assertEqual(settings["service_role"], "server")
        self.assertEqual(settings["listen_host"], "0.0.0.0")
        self.assertEqual(settings["listen_port"], 7000)

    def test_invalid_role_raises(self):
        with self.assertRaises(ValueError):
            start_service.build_runtime_settings({"SERVICE_ROLE": "invalid"})


if __name__ == "__main__":
    unittest.main()
