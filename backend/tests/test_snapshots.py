import json
import uuid
from unittest import TestCase
from unittest.mock import patch, MagicMock
import base64

from api.main import app, cfg

class TestGetEvent(TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.valid_token = "valid_jwt_token"
        
        self.event_id = str(uuid.uuid4())
        self.snapshot_id = str(uuid.uuid4())
        self.resource_id = str(uuid.uuid4())
        self.event_timestamp = "2023-06-15T14:30:45.123456Z"
        
        self.event = {
            "id": self.event_id,
            "snapshot_id": self.snapshot_id,
            "resource_id": self.resource_id,
            "timestamp": self.event_timestamp,
            "type": "fire_detection",
            "status": "active"
        }

        self.last_snapshot_id = str(uuid.uuid4())

        self.resource = {
            "id": self.resource_id,
            "name": "Test Resource",
            "url": "https://example.com",
        }

        self.snapshot_times = [
            ("2023-01-01T10:00:00Z", 1),
            ("2023-01-02T11:30:00Z", 2),
            ("2023-01-03T12:45:00Z", 3)
        ]
        
        self.test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82'
        
        self.test_image_base64 = base64.b64encode(self.test_image_data).decode("utf-8")

        self.test_html = b'<html><body><h1>Test Heading</h1><p>This is a test paragraph.</p></body></html>'
        
        self.extracted_text = "Test Heading\nThis is a test paragraph."

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_monitoring_event_by_id')
    def test_get_event_success(self, mock_get_event, mock_validate_uuid, 
                            mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_event.return_value = self.event
        
        response = self.app.get(
            f'/events/{self.event_id}',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        self.assertIn('event', response_data)
        event = response_data['event']
        
        self.assertEqual(event['id'], self.event_id)
        self.assertEqual(event['snapshot_id'], self.snapshot_id)
        self.assertEqual(event['resource_id'], self.resource_id)
        self.assertEqual(event['timestamp'], self.event_timestamp)
        self.assertEqual(event['type'], "fire_detection")
        self.assertEqual(event['status'], "active")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    def test_get_event_invalid_uuid(self, mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = False
        
        response = self.app.get(
            '/events/invalid-uuid',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], "event_id is invalid")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_monitoring_event_by_id')
    def test_get_event_not_found(self, mock_get_event, mock_validate_uuid, 
                               mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_event.return_value = None
        
        response = self.app.get(
            f'/events/{self.event_id}',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], f"event {self.event_id} not found")

    def test_get_event_unauthorized(self):
        response = self.app.get(f'/events/{self.event_id}')
        
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_monitoring_event_by_id')
    def test_get_event_with_invalid_token(self, mock_get_event, mock_validate_uuid, 
                                       mock_get_user, mock_jwt_decode):
        mock_jwt_decode.side_effect = Exception("Invalid token")
        
        response = self.app.get(
            f'/events/{self.event_id}',
            headers={'Authorization': f'bearer: invalid_token'}
        )
        
        self.assertEqual(response.status_code, 401)
        
        mock_get_user.assert_not_called()
        mock_validate_uuid.assert_not_called()
        mock_get_event.assert_not_called()

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_get_event_deleted_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = 228228227
        mock_get_user.return_value = mock_user
        
        response = self.app.get(
            f'/events/{self.event_id}',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 403)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_get_event_nonexistent_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "nonexistent@example.com"}
        mock_get_user.return_value = None
        
        response = self.app.get(
            f'/events/{self.event_id}',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_monitoring_event_by_id')
    def test_get_event_different_event_types(self, mock_get_event, mock_validate_uuid, 
                                          mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        
        event_types = ["fire_detection", "water_level_alert", "temperature_threshold", "weather_alert"]
        
        for event_type in event_types:
            current_event = self.event.copy()
            current_event["type"] = event_type
            
            mock_get_event.return_value = current_event
            
            response = self.app.get(
                f'/events/{self.event_id}',
                headers={'Authorization': f'bearer: {self.valid_token}'}
            )
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.data.decode())
            self.assertEqual(response_data["event"]["type"], event_type)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_monitoring_event_by_id')
    def test_get_event_with_different_statuses(self, mock_get_event, mock_validate_uuid, 
                                            mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        
        event_statuses = ["active", "resolved", "false_alarm", "pending", "escalated"]
        
        for status in event_statuses:
            current_event = self.event.copy()
            current_event["status"] = status
            
            mock_get_event.return_value = current_event
            
            response = self.app.get(
                f'/events/{self.event_id}',
                headers={'Authorization': f'bearer: {self.valid_token}'}
            )
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.data.decode())
            self.assertEqual(response_data["event"]["status"], status)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_monitoring_event_by_id')
    def test_get_event_null_snapshot_id(self, mock_get_event, mock_validate_uuid, 
                                     mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        
        event_with_null = self.event.copy()
        event_with_null["snapshot_id"] = None
        
        mock_get_event.return_value = event_with_null
        
        response = self.app.get(
            f'/events/{self.event_id}',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        self.assertIsNone(response_data["event"]["snapshot_id"])
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_monitoring_event_by_id')
    @patch('api.main.validate_monitoring_event_status')
    @patch('api.main.update_monitoring_event_status')
    def test_update_event_status_to_acknowledged(self, mock_update_status, mock_validate_status, 
                                             mock_get_event, mock_validate_uuid, 
                                             mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_event.return_value = self.event
        mock_validate_status.return_value = True
        
        payload = {
            "status": "ACKNOWLEDGED"
        }
        
        response = self.app.patch(
            f'/events/{self.event_id}',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        
        mock_update_status.assert_called_once_with(cfg.postgres, self.event_id, "ACKNOWLEDGED")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_monitoring_event_by_id')
    @patch('api.main.validate_monitoring_event_status')
    @patch('api.main.update_monitoring_event_status')
    def test_update_event_status_to_resolved(self, mock_update_status, mock_validate_status, 
                                         mock_get_event, mock_validate_uuid, 
                                         mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_event.return_value = self.event
        mock_validate_status.return_value = True
        
        payload = {
            "status": "REACTED"
        }
        
        response = self.app.patch(
            f'/events/{self.event_id}',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        
        mock_update_status.assert_called_once_with(cfg.postgres, self.event_id, "REACTED")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_monitoring_event_by_id')
    @patch('api.main.validate_monitoring_event_status')
    @patch('api.main.update_monitoring_event_status')
    def test_update_event_status_to_closed(self, mock_update_status, mock_validate_status, 
                                       mock_get_event, mock_validate_uuid, 
                                       mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_event.return_value = self.event
        mock_validate_status.return_value = True
        
        payload = {
            "status": "CLOSED"
        }
        
        response = self.app.patch(
            f'/events/{self.event_id}',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        
        mock_update_status.assert_called_once_with(cfg.postgres, self.event_id, "CLOSED")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    def test_update_event_invalid_uuid(self, mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = False
        
        payload = {
            "status": "ACKNOWLEDGED"
        }
        
        response = self.app.patch(
            '/events/invalid-uuid',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], "event_id is invalid")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_monitoring_event_by_id')
    def test_update_event_not_found(self, mock_get_event, mock_validate_uuid, 
                                 mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_event.return_value = None
        
        payload = {
            "status": "ACKNOWLEDGED"
        }
        
        response = self.app.patch(
            f'/events/{self.event_id}',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], f"event {self.event_id} not found")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_monitoring_event_by_id')
    @patch('api.main.validate_monitoring_event_status')
    def test_update_event_invalid_status(self, mock_validate_status, mock_get_event, 
                                      mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_event.return_value = self.event
        mock_validate_status.return_value = False
        
        payload = {
            "status": "INVALID_STATUS"
        }
        
        response = self.app.patch(
            f'/events/{self.event_id}',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], "status is invalid")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_monitoring_event_by_id')
    def test_update_event_watched_status(self, mock_get_event, mock_validate_uuid, 
                                      mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_event.return_value = self.event
        
        payload = {
            "status": "WATCHED"
        }
        
        response = self.app.patch(
            f'/events/{self.event_id}',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_monitoring_event_by_id')
    def test_update_event_reacted_status(self, mock_get_event, mock_validate_uuid, 
                                       mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        
        payload = {
            "status": "REACTED"
        }
        
        response = self.app.patch(
            f'/events/{self.event_id}',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)

    def test_update_event_unauthorized(self):
        payload = {
            "status": "ACKNOWLEDGED"
        }
        
        response = self.app.patch(
            f'/events/{self.event_id}',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_object')
    def test_get_event_snapshot_success(self, mock_get_object, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_get_object.return_value = self.test_image_data
        
        response = self.app.get(
            f'/events/{self.snapshot_id}/screenshot',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        mock_get_object.assert_called_once_with(cfg.s3, "images", f"{self.snapshot_id}.png")
        
        self.assertIn('image', response_data)
        
        self.assertEqual(response_data['image'], self.test_image_base64)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_object')
    def test_get_event_snapshot_not_found(self, mock_get_object, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_get_object.return_value = None
        
        response = self.app.get(
            f'/events/{self.snapshot_id}/screenshot',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data['error'], f"screenshot {self.snapshot_id} not found")

    def test_get_event_snapshot_unauthorized(self):
        response = self.app.get(f'/events/{self.snapshot_id}/screenshot')
        
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_get_event_snapshot_deleted_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = "2023-01-01 12:00:00"
        mock_get_user.return_value = mock_user
        
        response = self.app.get(
            f'/events/{self.snapshot_id}/screenshot',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 403)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_get_event_snapshot_nonexistent_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "nonexistent@example.com"}
        mock_get_user.return_value = None
        
        response = self.app.get(
            f'/events/{self.snapshot_id}/screenshot',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_object')
    def test_get_event_snapshot_with_invalid_token(self, mock_get_object, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.side_effect = Exception("Invalid token")
        
        response = self.app.get(
            f'/events/{self.snapshot_id}/screenshot',
            headers={'Authorization': f'bearer: invalid_token'}
        )
        
        self.assertEqual(response.status_code, 401)
        
        mock_get_user.assert_not_called()
        mock_get_object.assert_not_called()

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_object')
    def test_get_event_snapshot_wrong_http_method(self, mock_get_object, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        response_post = self.app.post(
            f'/events/{self.snapshot_id}/screenshot',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        response_put = self.app.put(
            f'/events/{self.snapshot_id}/screenshot',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        response_delete = self.app.delete(
            f'/events/{self.snapshot_id}/screenshot',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response_post.status_code, 405)
        self.assertEqual(response_put.status_code, 405)
        self.assertEqual(response_delete.status_code, 405)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_object')
    def test_get_event_snapshot_large_image(self, mock_get_object, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        large_image_data = b'\x00' * (5 * 1024 * 1024)
        large_image_base64 = base64.b64encode(large_image_data).decode("utf-8")
        
        mock_get_object.return_value = large_image_data
        
        response = self.app.get(
            f'/events/{self.snapshot_id}/screenshot',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data['image'], large_image_base64)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_object')
    def test_get_event_snapshot_different_snapshot_ids(self, mock_get_object, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_get_object.return_value = self.test_image_data
        
        snapshot_ids = [
            "abcd1234-5678-90ef-ghij-klmnopqrstuv",
            "12345",
            "snapshot_2023_06_15",
            "very-long-snapshot-id-with-many-characters-that-exceeds-normal-length"
        ]
        
        for snapshot_id in snapshot_ids:
            mock_get_object.reset_mock()
            
            response = self.app.get(
                f'/events/{snapshot_id}/screenshot',
                headers={'Authorization': f'bearer: {self.valid_token}'}
            )
            
            self.assertEqual(response.status_code, 200)
            
            mock_get_object.assert_called_once_with(cfg.s3, "images", f"{snapshot_id}.png")
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_object')
    @patch('api.main.extract_text_from_html')
    def test_get_event_text_success(self, mock_extract_text, mock_get_object, 
                                 mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_get_object.return_value = self.test_html
        mock_extract_text.return_value = self.extracted_text
        
        response = self.app.get(
            f'/events/{self.snapshot_id}/text',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        mock_get_object.assert_called_once_with(cfg.s3, "htmls", f"{self.snapshot_id}.html")
        
        mock_extract_text.assert_called_once_with(self.test_html)
        
        self.assertIn('text', response_data)
        
        self.assertEqual(response_data['text'], self.extracted_text)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_object')
    def test_get_event_text_snapshot_not_found(self, mock_get_object, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_get_object.return_value = None
        
        response = self.app.get(
            f'/events/{self.snapshot_id}/text',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data['error'], f"snapshot {self.snapshot_id} not found")

    def test_get_event_text_unauthorized(self):
        response = self.app.get(f'/events/{self.snapshot_id}/text')
        
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_get_event_text_deleted_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = "2023-01-01 12:00:00"
        mock_get_user.return_value = mock_user
        
        response = self.app.get(
            f'/events/{self.snapshot_id}/text',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 403)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_get_event_text_nonexistent_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "nonexistent@example.com"}
        mock_get_user.return_value = None
        
        response = self.app.get(
            f'/events/{self.snapshot_id}/text',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_object')
    def test_get_event_text_with_invalid_token(self, mock_get_object, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.side_effect = Exception("Invalid token")
        
        response = self.app.get(
            f'/events/{self.snapshot_id}/text',
            headers={'Authorization': f'bearer: invalid_token'}
        )
        
        self.assertEqual(response.status_code, 401)
        
        mock_get_user.assert_not_called()
        mock_get_object.assert_not_called()

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_object')
    @patch('api.main.extract_text_from_html')
    def test_get_event_text_different_html_types(self, mock_extract_text, mock_get_object, 
                                            mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        html_samples = [
            (b'<html><body><h1>Simple HTML</h1></body></html>', "Simple HTML"),
            (b'<html><body><div>Nested <span>elements</span></div></body></html>', "Nested elements"),
            (b'<html><body><script>var x = 1;</script><p>Text with script</p></body></html>', "Text with script"),
            (b'<html><body><!-- Comment --><p>Text with comment</p></body></html>', "Text with comment"),
            (b'<html><body><p>Text with special chars: &lt;&gt;&amp;</p></body></html>', "Text with special chars: <>")
        ]
        
        for html, expected_text in html_samples:
            mock_get_object.reset_mock()
            mock_extract_text.reset_mock()
            
            mock_get_object.return_value = html
            mock_extract_text.return_value = expected_text
            
            response = self.app.get(
                f'/events/{self.snapshot_id}/text',
                headers={'Authorization': f'bearer: {self.valid_token}'}
            )
            
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.data.decode())
            self.assertEqual(response_data['text'], expected_text)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_object')
    @patch('api.main.extract_text_from_html')
    def test_get_event_text_empty_html(self, mock_extract_text, mock_get_object, 
                                    mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        mock_get_object.return_value = b''
        mock_extract_text.return_value = ""
        
        response = self.app.get(
            f'/events/{self.snapshot_id}/text',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data['text'], "")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_object')
    @patch('api.main.extract_text_from_html')
    def test_get_event_text_large_html(self, mock_extract_text, mock_get_object, 
                                    mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        large_html = b'<html><body><p>' + b'A' * (1024 * 1024) + b'</p></body></html>'
        large_text = "A" * (1024 * 1024)
        
        mock_get_object.return_value = large_html
        mock_extract_text.return_value = large_text
        
        response = self.app.get(
            f'/events/{self.snapshot_id}/text',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data['text'], large_text)
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_last_snapshot_id')
    def test_get_event_last_snapshot_id_success(self, mock_get_last_snapshot, mock_get_resource, 
                                             mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        mock_get_last_snapshot.return_value = self.last_snapshot_id
        
        response = self.app.get(
            f'/resources/{self.resource_id}/last_snapshot_id',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        mock_validate_uuid.assert_called_once_with(self.resource_id)
        mock_get_resource.assert_called_once_with(cfg.postgres, self.resource_id)
        mock_get_last_snapshot.assert_called_once_with(cfg.s3, self.resource_id)
        
        self.assertIn('snapshot_id', response_data)
        
        self.assertEqual(response_data['snapshot_id'], self.last_snapshot_id)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    def test_get_event_last_snapshot_id_invalid_uuid(self, mock_validate_uuid, mock_get_user, mock_jwt_decode):
        # Настройка моков
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = False
        
        response = self.app.get(
            '/resources/invalid-uuid/last_snapshot_id',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], "resource_id is invalid")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    def test_get_event_last_snapshot_id_resource_not_found(self, mock_get_resource, 
                                                       mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = None
        
        response = self.app.get(
            f'/resources/{self.resource_id}/last_snapshot_id',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], f"resource {self.resource_id} not found")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_last_snapshot_id')
    def test_get_event_last_snapshot_id_no_snapshots(self, mock_get_last_snapshot, mock_get_resource, 
                                                 mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        mock_get_last_snapshot.return_value = None
        
        response = self.app.get(
            f'/resources/{self.resource_id}/last_snapshot_id',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        self.assertIn('snapshot_id', response_data)
        self.assertIsNone(response_data['snapshot_id'])

    def test_get_event_last_snapshot_id_unauthorized(self):
        response = self.app.get(f'/resources/{self.resource_id}/last_snapshot_id')
        
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_get_event_last_snapshot_id_deleted_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = "2023-01-01 12:00:00"
        mock_get_user.return_value = mock_user
        
        response = self.app.get(
            f'/resources/{self.resource_id}/last_snapshot_id',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 403)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_get_event_last_snapshot_id_nonexistent_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "nonexistent@example.com"}
        mock_get_user.return_value = None
        
        response = self.app.get(
            f'/resources/{self.resource_id}/last_snapshot_id',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_last_snapshot_id')
    def test_get_event_last_snapshot_id_with_invalid_token(self, mock_get_last_snapshot, 
                                                       mock_get_resource, mock_validate_uuid, 
                                                       mock_get_user, mock_jwt_decode):
        mock_jwt_decode.side_effect = Exception("Invalid token")
        
        response = self.app.get(
            f'/resources/{self.resource_id}/last_snapshot_id',
            headers={'Authorization': f'bearer: invalid_token'}
        )
        
        self.assertEqual(response.status_code, 401)
        
        mock_get_user.assert_not_called()
        mock_validate_uuid.assert_not_called()
        mock_get_resource.assert_not_called()
        mock_get_last_snapshot.assert_not_called()
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_snapshot_times_by_resource_id')
    def test_get_snapshot_times_success(self, mock_get_snapshot_times, mock_get_resource, 
                                     mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        mock_get_snapshot_times.return_value = self.snapshot_times
        
        response = self.app.get(
            f'/resources/{self.resource_id}/snapshot_times',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        mock_validate_uuid.assert_called_once_with(self.resource_id)
        mock_get_resource.assert_called_once_with(cfg.postgres, self.resource_id)
        mock_get_snapshot_times.assert_called_once_with(cfg.s3, self.resource_id)
        
        self.assertIn('snapshots', response_data)
        self.assertIsInstance(response_data['snapshots'], list)
        self.assertEqual(len(response_data['snapshots']), len(self.snapshot_times))
        
        for i, snapshot_data in enumerate(response_data['snapshots']):
            self.assertIn('id', snapshot_data)
            self.assertIn('time', snapshot_data)
            expected_id = f"{self.resource_id}_{self.snapshot_times[i][1]}"
            expected_time = self.snapshot_times[i][0]
            self.assertEqual(snapshot_data['id'], expected_id)
            self.assertEqual(snapshot_data['time'], expected_time)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    def test_get_snapshot_times_invalid_uuid(self, mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = False
        
        response = self.app.get(
            '/resources/invalid-uuid/snapshot_times',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], "resource_id is invalid")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    def test_get_snapshot_times_resource_not_found(self, mock_get_resource, 
                                               mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = None
        
        response = self.app.get(
            f'/resources/{self.resource_id}/snapshot_times',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], f"resource {self.resource_id} not found")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_snapshot_times_by_resource_id')
    def test_get_snapshot_times_empty_list(self, mock_get_snapshot_times, mock_get_resource, 
                                       mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        mock_get_snapshot_times.return_value = []
        
        response = self.app.get(
            f'/resources/{self.resource_id}/snapshot_times',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        self.assertIn('snapshots', response_data)
        self.assertIsInstance(response_data['snapshots'], list)
        self.assertEqual(len(response_data['snapshots']), 0)

    def test_get_snapshot_times_unauthorized(self):
        response = self.app.get(f'/resources/{self.resource_id}/snapshot_times')
        
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_get_snapshot_times_deleted_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = "2023-01-01 12:00:00"
        mock_get_user.return_value = mock_user
        
        response = self.app.get(
            f'/resources/{self.resource_id}/snapshot_times',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 403)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_get_snapshot_times_nonexistent_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "nonexistent@example.com"}
        mock_get_user.return_value = None
        
        response = self.app.get(
            f'/resources/{self.resource_id}/snapshot_times',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_snapshot_times_by_resource_id')
    def test_get_snapshot_times_with_invalid_token(self, mock_get_snapshot_times, 
                                               mock_get_resource, mock_validate_uuid, 
                                               mock_get_user, mock_jwt_decode):
        mock_jwt_decode.side_effect = Exception("Invalid token")
        
        response = self.app.get(
            f'/resources/{self.resource_id}/snapshot_times',
            headers={'Authorization': f'bearer: invalid_token'}
        )
        
        self.assertEqual(response.status_code, 401)
        
        mock_get_user.assert_not_called()
        mock_validate_uuid.assert_not_called()
        mock_get_resource.assert_not_called()
        mock_get_snapshot_times.assert_not_called()
