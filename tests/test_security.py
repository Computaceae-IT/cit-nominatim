import contextlib
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("smoke_api", ROOT / "scripts/smoke_api.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@contextlib.contextmanager
def api_fixture(overrides=None):
    place = {"lat": "46.2", "lon": "6.1", "osm_type": "node", "osm_id": 1, "display_name": "Geneve"}
    responses = {"/status.php": {"status": 0}, "/search.php": [place],
                 "/reverse.php": place, "/lookup.php": [place], "/details.php": {"place_id": 42}}
    responses.update(overrides or {})

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(responses[self.path.split("?")[0]]).encode())

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


class SmokeTests(unittest.TestCase):
    def test_healthy_contract(self):
        with api_fixture() as url:
            self.assertEqual(module.smoke(url)["status"], "OK")

    def test_http_200_with_database_error_is_rejected(self):
        with api_fixture({"/status.php": {"status": 700, "message": "DB unavailable"}}) as url:
            with self.assertRaisesRegex(ValueError, "not healthy"):
                module.smoke(url)

    def test_empty_search_is_rejected(self):
        with api_fixture({"/search.php": []}) as url:
            with self.assertRaisesRegex(ValueError, "non-empty"):
                module.smoke(url)

    def test_reverse_application_error_is_rejected(self):
        with api_fixture({"/reverse.php": {"error": "Unable to geocode"}}) as url:
            with self.assertRaisesRegex(ValueError, "Unable to geocode"):
                module.smoke(url)


class SourceTests(unittest.TestCase):
    def test_db_archive_integrity_and_version(self):
        archive = ROOT / "DB/db-src.tar.gz"
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(),
                         "b5fe1446d6ce5a64f8112eff8b6e773a4b8a09b242a902e76f86a5d523a32bc6")
        with tarfile.open(archive) as source:
            cmake = source.extractfile("src/CMakeLists.txt").read().decode()
        for name, value in (("MAJOR", 3), ("MINOR", 6), ("PATCH", 0)):
            self.assertIn(f"set(NOMINATIM_VERSION_{name} {value})", cmake)

    def test_package_checks_are_identical(self):
        self.assertEqual((ROOT / "API/verify-php.sh").read_bytes(), (ROOT / "DB/verify-php.sh").read_bytes())


@unittest.skipUnless(shutil.which("dpkg") and shutil.which("sh"), "Requires Linux dpkg/sh; CI runs these checks")
class PackageGateTests(unittest.TestCase):
    def check_packages(self, version, missing=False, extension_error=False, old_apache=False):
        with tempfile.TemporaryDirectory() as directory:
            mock = Path(directory)
            query = mock / "dpkg-query"
            query.write_text("#!/bin/sh\ncase \"$2\" in\n *Status*) " +
                             ("echo 'unknown ok not-installed'" if missing else "echo 'install ok installed'") +
                             " ;;\n *) echo 'php7.4 php7.4-cli " + version + " installed'; " + ("echo 'php7.4 libapache2-mod-php7.4 7.4.3-4ubuntu2.29 installed'; " if old_apache else "") + ";;\nesac\n")
            php = mock / "php"
            php.write_text("#!/bin/sh\nexit " + ("1" if extension_error else "0") + "\n")
            query.chmod(0o755)
            php.chmod(0o755)
            return subprocess.run(["sh", str(ROOT / "API/verify-php.sh")],
                                  env={**os.environ, "PATH": directory + os.pathsep + os.environ["PATH"]},
                                  capture_output=True, text=True)

    def test_observed_unpatched_revision_is_rejected(self):
        self.assertNotEqual(self.check_packages("7.4.3-4ubuntu2.29").returncode, 0)

    def test_fixed_and_newer_ubuntu_revisions_are_accepted(self):
        for revision in ("7.4.3-4ubuntu2.29+esm5", "7.4.3-4ubuntu2.29+esm6"):
            with self.subTest(revision=revision):
                result = self.check_packages(revision)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_old_apache_module_with_fixed_cli_is_rejected(self):
        self.assertNotEqual(self.check_packages("7.4.3-4ubuntu2.29+esm5", old_apache=True).returncode, 0)

    def test_missing_sapi_package_is_rejected(self):
        self.assertNotEqual(self.check_packages("7.4.3-4ubuntu2.29+esm5", missing=True).returncode, 0)

    def test_missing_runtime_extension_is_rejected(self):
        self.assertNotEqual(self.check_packages("7.4.3-4ubuntu2.29+esm5", extension_error=True).returncode, 0)


class DBStartupTests(unittest.TestCase):
    def test_missing_mount_refuses_start_without_invoking_service(self):
        shell = shutil.which("sh")
        if not shell and os.name == "nt":
            candidate = Path("C:/Program Files/Git/bin/bash.exe")
            shell = str(candidate) if candidate.exists() else None
        if not shell:
            self.skipTest("A POSIX shell is required")
        with tempfile.TemporaryDirectory() as directory:
            mock = Path(directory)
            (mock / "mountpoint").write_text("#!/bin/sh\nexit 1\n")
            (mock / "service").write_text("#!/bin/sh\necho SERVICE_MUST_NOT_START >&2\nexit 99\n")
            for script in mock.iterdir():
                script.chmod(0o755)
            result = subprocess.run([shell, "-c", 'PATH="$1:$PATH"; export PATH; sh "$2"', "test",
                                     mock.as_posix(), (ROOT / "DB/startpostgres.sh").as_posix()],
                                    capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Refusing to start", result.stderr)
        self.assertNotIn("SERVICE_MUST_NOT_START", result.stderr)


if __name__ == "__main__":
    unittest.main()
