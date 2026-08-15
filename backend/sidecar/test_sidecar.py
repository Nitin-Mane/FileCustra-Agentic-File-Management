#!/usr/bin/env python3
"""
Test suite for FileCustra Python Sidecar lifecycle, JSON-RPC framing, and IPC.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from main import SidecarLifecycleManager, JSONRPCFraming, process_request


class TestSidecarLifecycle(unittest.TestCase):
    """Test sidecar lifecycle management."""
    
    def test_lifecycle_start_stop(self):
        lifecycle = SidecarLifecycleManager()
        lifecycle.start()
        self.assertTrue(lifecycle._running)
        lifecycle.stop()
        self.assertFalse(lifecycle._running)
    
    def test_lifecycle_status(self):
        lifecycle = SidecarLifecycleManager()
        lifecycle.start()
        status = lifecycle.get_status()
        self.assertIn("running", status)
        self.assertIn("uptime_seconds", status)
        self.assertIn("request_count", status)
        self.assertIn("error_count", status)
        self.assertTrue(status["running"])
        lifecycle.stop()
    
    def test_lifecycle_request_counting(self):
        lifecycle = SidecarLifecycleManager()
        lifecycle.start()
        lifecycle.record_request()
        lifecycle.record_request()
        lifecycle.record_request()
        status = lifecycle.get_status()
        self.assertEqual(status["request_count"], 3)
        lifecycle.stop()
    
    def test_lifecycle_error_counting(self):
        lifecycle = SidecarLifecycleManager()
        lifecycle.start()
        lifecycle.record_error()
        status = lifecycle.get_status()
        self.assertEqual(status["error_count"], 1)
        lifecycle.stop()


class TestJSONRPCFraming(unittest.TestCase):
    """Test JSON-RPC 2.0 message framing."""
    
    def test_create_response(self):
        framing = JSONRPCFraming()
        resp = framing.create_response({"status": "ok"}, "123")
        data = json.loads(resp)
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertEqual(data["result"]["status"], "ok")
        self.assertEqual(data["id"], "123")
    
    def test_create_response_no_id(self):
        framing = JSONRPCFraming()
        resp = framing.create_response({"status": "ok"})
        data = json.loads(resp)
        self.assertIsNone(data["id"])
    
    def test_create_error(self):
        framing = JSONRPCFraming()
        resp = framing.create_error(-32601, "Method not found", "456")
        data = json.loads(resp)
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertEqual(data["error"]["code"], -32601)
        self.assertEqual(data["error"]["message"], "Method not found")
        self.assertEqual(data["id"], "456")
    
    def test_create_error_with_data(self):
        framing = JSONRPCFraming()
        resp = framing.create_error(-32603, "Internal error", "789", {"detail": "traceback"})
        data = json.loads(resp)
        self.assertIn("data", data["error"])
        self.assertEqual(data["error"]["data"]["detail"], "traceback")
    
    def test_create_notification(self):
        framing = JSONRPCFraming()
        resp = framing.create_notification("progress", {"percent": 50})
        data = json.loads(resp)
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertEqual(data["method"], "progress")
        self.assertEqual(data["params"]["percent"], 50)
        self.assertNotIn("id", data)
    
    def test_parse_request_valid(self):
        framing = JSONRPCFraming()
        req = {"jsonrpc": "2.0", "method": "test", "id": "1", "params": {}}
        result = framing.parse_request(json.dumps(req))
        self.assertIsNotNone(result)
        self.assertEqual(result["method"], "test")
    
    def test_parse_request_invalid_json(self):
        framing = JSONRPCFraming()
        result = framing.parse_request("not valid json")
        self.assertIsNone(result)
    
    def test_parse_request_wrong_version(self):
        framing = JSONRPCFraming()
        req = {"jsonrpc": "1.0", "method": "test"}
        result = framing.parse_request(json.dumps(req))
        self.assertIsNone(result)
    
    def test_parse_request_no_method(self):
        framing = JSONRPCFraming()
        req = {"jsonrpc": "2.0"}
        result = framing.parse_request(json.dumps(req))
        self.assertIsNone(result)
    
    def test_parse_request_not_dict(self):
        framing = JSONRPCFraming()
        result = framing.parse_request(json.dumps([1, 2, 3]))
        self.assertIsNone(result)


class TestProcessRequest(unittest.TestCase):
    """Test request processing."""
    
    def setUp(self):
        self.lifecycle = SidecarLifecycleManager()
        self.lifecycle.start()
        self.framing = JSONRPCFraming()
    
    def tearDown(self):
        self.lifecycle.stop()
    
    def test_ping(self):
        req = {"jsonrpc": "2.0", "method": "sidecar.ping", "id": "1"}
        resp = process_request(req, self.lifecycle, self.framing)
        data = json.loads(resp)
        self.assertEqual(data["result"]["status"], "PONG")
        self.assertIn("sidecar_version", data["result"])
    
    def test_heartbeat(self):
        req = {"jsonrpc": "2.0", "method": "sidecar.heartbeat", "id": "2"}
        resp = process_request(req, self.lifecycle, self.framing)
        data = json.loads(resp)
        self.assertEqual(data["result"]["status"], "ALIVE")
        self.assertIn("uptime_seconds", data["result"])
    
    def test_status(self):
        req = {"jsonrpc": "2.0", "method": "sidecar.status", "id": "3"}
        resp = process_request(req, self.lifecycle, self.framing)
        data = json.loads(resp)
        self.assertIn("running", data["result"])
        self.assertIn("request_count", data["result"])
    
    def test_system_snapshot(self):
        req = {"jsonrpc": "2.0", "method": "system.snapshot", "id": "4", "params": {}}
        resp = process_request(req, self.lifecycle, self.framing)
        data = json.loads(resp)
        self.assertIn("runtime", data["result"])
        self.assertIn("drives", data["result"])
        self.assertIn("hardware", data["result"])
    
    def test_phase_status(self):
        req = {"jsonrpc": "2.0", "method": "workspace.phase_status", "id": "5"}
        resp = process_request(req, self.lifecycle, self.framing)
        data = json.loads(resp)
        self.assertIn("phases", data["result"])
        self.assertEqual(len(data["result"]["phases"]), 20)
    
    def test_method_not_found(self):
        req = {"jsonrpc": "2.0", "method": "nonexistent.method", "id": "6"}
        resp = process_request(req, self.lifecycle, self.framing)
        data = json.loads(resp)
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], -32601)
    
    def test_request_count_increments(self):
        req = {"jsonrpc": "2.0", "method": "sidecar.ping", "id": "7"}
        process_request(req, self.lifecycle, self.framing)
        process_request(req, self.lifecycle, self.framing)
        self.assertEqual(self.lifecycle.get_status()["request_count"], 2)


if __name__ == "__main__":
    unittest.main()
