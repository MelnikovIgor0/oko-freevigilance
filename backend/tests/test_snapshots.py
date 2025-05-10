import json
import uuid
from unittest import TestCase
from unittest.mock import patch, MagicMock

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
            headers={'Authorization': f'Bearer {self.valid_token}'}
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
            headers={'Authorization': f'Bearer {self.valid_token}'}
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
            headers={'Authorization': f'Bearer {self.valid_token}'}
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
            headers={'Authorization': f'Bearer invalid_token'}
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
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 403)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_get_event_nonexistent_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "nonexistent@example.com"}
        mock_get_user.return_value = None
        
        response = self.app.get(
            f'/events/{self.event_id}',
            headers={'Authorization': f'Bearer {self.valid_token}'}
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
                headers={'Authorization': f'Bearer {self.valid_token}'}
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
                headers={'Authorization': f'Bearer {self.valid_token}'}
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
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        self.assertIsNone(response_data["event"]["snapshot_id"])
