import json
import uuid
from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import patch, MagicMock

from api.main import app, cfg

class TestGetFiltredEvents(TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.valid_token = "valid_jwt_token"
        
        self.resource_id_1 = str(uuid.uuid4())
        self.resource_id_2 = str(uuid.uuid4())
        
        now = datetime.now()
        self.start_time = (now - timedelta(days=7)).isoformat() + "Z"
        self.end_time = now.isoformat() + "Z"
        
        self.test_events = [
            {
                "id": str(uuid.uuid4()),
                "resource_id": self.resource_id_1,
                "timestamp": self.start_time,
                "type": "keyword",
                "status": "CREATED"
            },
            {
                "id": str(uuid.uuid4()),
                "resource_id": self.resource_id_2,
                "timestamp": self.end_time,
                "type": "image",
                "status": "NOTIFIED"
            }
        ]

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.validate_date_time')
    @patch('api.main.filter_monitoring_events')
    def test_get_filtred_events_all_filters(self, mock_filter_events, mock_validate_date, 
                                        mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        
        mock_validate_date.side_effect = [
            datetime.fromisoformat(self.start_time.replace('Z', '+00:00')),
            datetime.fromisoformat(self.end_time.replace('Z', '+00:00'))
        ]
        
        mock_filter_events.return_value = self.test_events
        
        payload = {
            "resource_ids": [self.resource_id_1, self.resource_id_2],
            "start_time": self.start_time,
            "end_time": self.end_time,
            "event_type": "keyword"
        }
        
        response = self.app.post(
            '/events/filter',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        mock_validate_uuid.assert_called()
        mock_validate_date.assert_called()
        
        self.assertIn('events', response_data)
        self.assertEqual(response_data['events'], self.test_events)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.filter_monitoring_events')
    def test_get_filtred_events_resource_ids_only(self, mock_filter_events, 
                                              mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_filter_events.return_value = self.test_events
        
        payload = {
            "resource_ids": [self.resource_id_1, self.resource_id_2]
        }
        
        response = self.app.post(
            '/events/filter',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        mock_filter_events.assert_called_once_with(
            cfg.postgres, 
            [self.resource_id_1, self.resource_id_2], 
            None, 
            None,
            None
        )
        
        self.assertIn('events', response_data)
        self.assertEqual(response_data['events'], self.test_events)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_date_time')
    @patch('api.main.filter_monitoring_events')
    def test_get_filtred_events_time_range_only(self, mock_filter_events, 
                                            mock_validate_date, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        start_datetime = datetime.fromisoformat(self.start_time.replace('Z', '+00:00'))
        end_datetime = datetime.fromisoformat(self.end_time.replace('Z', '+00:00'))
        mock_validate_date.side_effect = [start_datetime, end_datetime]
        
        mock_filter_events.return_value = self.test_events
        
        payload = {
            "start_time": self.start_time,
            "end_time": self.end_time
        }
        
        response = self.app.post(
            '/events/filter',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        mock_filter_events.assert_called_once_with(
            cfg.postgres, 
            None, 
            start_datetime, 
            end_datetime,
            None
        )
        
        self.assertIn('events', response_data)
        self.assertEqual(response_data['events'], self.test_events)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.filter_monitoring_events')
    def test_get_filtred_events_event_type_only(self, mock_filter_events, 
                                            mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_filter_events.return_value = self.test_events
        
        payload = {
            "event_type": "image"
        }
        
        response = self.app.post(
            '/events/filter',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        mock_filter_events.assert_called_once_with(
            cfg.postgres, 
            None, 
            None, 
            None,
            "image"
        )
        
        self.assertIn('events', response_data)
        self.assertEqual(response_data['events'], self.test_events)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.filter_monitoring_events')
    def test_get_filtred_events_empty_filters(self, mock_filter_events, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_filter_events.return_value = self.test_events
        
        payload = {}
        
        response = self.app.post(
            '/events/filter',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        self.assertIn('events', response_data)
        self.assertEqual(response_data['events'], self.test_events)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_get_filtred_events_invalid_resource_ids_format(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        payload = {
            "resource_ids": "not-a-list"
        }
        
        response = self.app.post(
            '/events/filter',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], "resource_ids should be list")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    def test_get_filtred_events_invalid_resource_id_value(self, mock_validate_uuid, 
                                                      mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = False
        
        payload = {
            "resource_ids": ["invalid-uuid"]
        }
        
        response = self.app.post(
            '/events/filter',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], "invalid resource_id value")
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_date_time')
    def test_get_filtred_events_invalid_end_time(self, mock_validate_date, 
                                             mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        start_datetime = datetime.fromisoformat(self.start_time.replace('Z', '+00:00'))
        mock_validate_date.side_effect = [start_datetime, None]
        
        payload = {
            "start_time": self.start_time,
            "end_time": "invalid-date-format"
        }
        
        response = self.app.post(
            '/events/filter',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], "end_time is invalid")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_date_time')
    def test_get_filtred_events_end_time_before_start_time(self, mock_validate_date, 
                                                       mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        end_datetime = datetime.fromisoformat(self.start_time.replace('Z', '+00:00'))
        start_datetime = datetime.fromisoformat(self.end_time.replace('Z', '+00:00'))
        mock_validate_date.side_effect = [start_datetime, end_datetime]
        
        payload = {
            "start_time": self.end_time,
            "end_time": self.start_time
        }
        
        response = self.app.post(
            '/events/filter',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], "end_time is more than start_time")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.validate_date_time')
    @patch('api.main.filter_monitoring_events')
    def test_get_filtred_events_multiple_resource_ids(self, mock_filter_events, mock_validate_date, 
                                                  mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_filter_events.return_value = self.test_events
        
        resource_ids = [str(uuid.uuid4()) for _ in range(5)]
        
        payload = {
            "resource_ids": resource_ids
        }
        
        response = self.app.post(
            '/events/filter',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        mock_filter_events.assert_called_once_with(
            cfg.postgres, 
            resource_ids, 
            None, 
            None,
            None
        )
        
        self.assertIn('events', response_data)
        self.assertEqual(response_data['events'], self.test_events)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.filter_monitoring_events')
    def test_get_filtred_events_empty_resource_ids_list(self, mock_filter_events, 
                                                    mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_filter_events.return_value = self.test_events
        
        payload = {
            "resource_ids": []
        }
        
        response = self.app.post(
            '/events/filter',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        mock_filter_events.assert_called_once_with(
            cfg.postgres, 
            [], 
            None, 
            None,
            None
        )
        
        self.assertIn('events', response_data)
        self.assertEqual(response_data['events'], self.test_events)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_date_time')
    @patch('api.main.filter_monitoring_events')
    def test_get_filtred_events_exact_time_range(self, mock_filter_events, 
                                             mock_validate_date, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user" : "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        exact_time = datetime.now()
        exact_time_iso = exact_time.isoformat() + "Z"
        
        mock_validate_date.return_value = exact_time
        
        mock_filter_events.return_value = self.test_events
        
        payload = {
            "start_time": exact_time_iso,
            "end_time": exact_time_iso
        }
        
        response = self.app.post(
            '/events/filter',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        mock_filter_events.assert_called_once_with(
            cfg.postgres, 
            None, 
            exact_time, 
            exact_time,
            None
        )
        
        self.assertIn('events', response_data)
        self.assertEqual(response_data['events'], self.test_events)

    def test_get_filtred_events_unauthorized(self):
        payload = {
            "resource_ids": [self.resource_id_1]
        }
        
        response = self.app.post(
            '/events/filter',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_get_filtred_events_deleted_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = "2023-01-01 12:00:00"
        mock_get_user.return_value = mock_user
        
        payload = {
            "resource_ids": [self.resource_id_1]
        }
        
        response = self.app.post(
            '/events/filter',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 403)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_get_filtred_events_nonexistent_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "nonexistent@example.com"}
        mock_get_user.return_value = None
        
        payload = {
            "resource_ids": [self.resource_id_1]
        }
        
        response = self.app.post(
            '/events/filter',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)