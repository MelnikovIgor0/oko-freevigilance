import json
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import uuid

from api.main import app, cfg

class TestResourcesEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.valid_token = "valid_token"
        self.valid_payload = {
            "url": "https://example.com",
            "name": "Test Resource",
            "description": "A test resource",
            "keywords": ["test", "example"],
            "interval": "1h",
            "channels": [1],
            "sensitivity": 0.8,
            "zone_type": "fullPage"
        }
        
        self.token_patcher = patch('api.main.token_required')
        self.mock_token_required = self.token_patcher.start()
        self.mock_token_required.return_value = lambda f: f
        
        self.resource_patcher = patch('api.main.create_resource')
        self.mock_create_resource = self.resource_patcher.start()
        self.resource = MagicMock()
        self.resource.id = 1
        self.resource.url = self.valid_payload["url"]
        self.resource.name = self.valid_payload["name"]
        self.resource.description = self.valid_payload["description"]
        self.resource.keywords = self.valid_payload["keywords"]
        self.resource.interval = "* * * * *"
        self.resource.starts_from = None
        self.resource.make_screenshot = True
        self.resource.enabled = True
        self.resource.polygon = {"sensitivity": 0.8}
        self.mock_create_resource.return_value = self.resource
        
        self.channel_patcher = patch('api.main.get_channel_by_id')
        self.mock_get_channel = self.channel_patcher.start()
        self.mock_get_channel.return_value = MagicMock()
        
        self.channel_resource_patcher = patch('api.main.create_channel_resource')
        self.mock_create_channel_resource = self.channel_resource_patcher.start()
        
        self.daemon_job_patcher = patch('api.main.create_daemon_cron_job_for_resource')
        self.mock_create_daemon_job = self.daemon_job_patcher.start()
        
        self.validate_url_patcher = patch('api.main.validate_url')
        self.mock_validate_url = self.validate_url_patcher.start()
        self.mock_validate_url.return_value = True
        
        self.validate_name_patcher = patch('api.main.validate_name')
        self.mock_validate_name = self.validate_name_patcher.start()
        self.mock_validate_name.return_value = True
        
        self.validate_description_patcher = patch('api.main.validate_description')
        self.mock_validate_description = self.validate_description_patcher.start()
        self.mock_validate_description.return_value = True
        
        self.validate_keywords_patcher = patch('api.main.validate_keywords')
        self.mock_validate_keywords = self.validate_keywords_patcher.start()
        self.mock_validate_keywords.return_value = True
        
        self.validate_interval_patcher = patch('api.main.validate_interval')
        self.mock_validate_interval = self.validate_interval_patcher.start()
        self.mock_validate_interval.return_value = True
        
        self.get_interval_patcher = patch('api.main.get_interval')
        self.mock_get_interval = self.get_interval_patcher.start()
        self.mock_get_interval.return_value = "3600"
        
        self.validate_date_time_patcher = patch('api.main.validate_date_time')
        self.mock_validate_date_time = self.validate_date_time_patcher.start()
        self.mock_validate_date_time.return_value = None
        
        self.validate_polygon_patcher = patch('api.main.validate_polygon')
        self.mock_validate_polygon = self.validate_polygon_patcher.start()
        self.mock_validate_polygon.return_value = True
    
    def tearDown(self):
        self.token_patcher.stop()
        self.resource_patcher.stop()
        self.channel_patcher.stop()
        self.channel_resource_patcher.stop()
        self.daemon_job_patcher.stop()
        self.validate_url_patcher.stop()
        self.validate_name_patcher.stop()
        self.validate_description_patcher.stop()
        self.validate_keywords_patcher.stop()
        self.validate_interval_patcher.stop()
        self.get_interval_patcher.stop()
        self.validate_date_time_patcher.stop()
        self.validate_polygon_patcher.stop()
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_channel_by_id')
    def test_create_resource_success(self, mock_get_channel_by_id, mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user_by_email.return_value = mock_user
        mock_get_channel_by_id.return_value = "mocked_channel"

        response = self.app.post(
            '/resources/create',
            data=json.dumps(self.valid_payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertIn('resource', response_data)
        self.assertEqual(response_data['resource']['id'], 1)
        self.assertEqual(response_data['resource']['url'], self.valid_payload['url'])
        self.assertEqual(response_data['resource']['name'], self.valid_payload['name'])

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_channel_by_id')
    def test_create_resource_with_areas(self, mock_get_channel_by_id, mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user_by_email.return_value = mock_user
        mock_get_channel_by_id.return_value = "mocked_channel"

        payload = self.valid_payload.copy()
        payload['zone_type'] = 'zone'
        payload['areas'] = [{"x": 10, "y": 10, "width": 100, "height": 100}]
        
        response = self.app.post(
            '/resources/create',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 201)
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_channel_by_id')
    def test_create_resource_missing_url(self, mock_get_channel_by_id, mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user_by_email.return_value = mock_user
        mock_get_channel_by_id.return_value = "mocked_channel"

        payload = self.valid_payload.copy()
        del payload['url']
        
        response = self.app.post(
            '/resources/create',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('url is missing', response.data.decode())

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_channel_by_id')
    def test_create_resource_missing_name(self, mock_get_channel_by_id, mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user_by_email.return_value = mock_user
        mock_get_channel_by_id.return_value = "mocked_channel"

        payload = self.valid_payload.copy()
        del payload['name']
        
        response = self.app.post(
            '/resources/create',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('name is missing', response.data.decode())
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_channel_by_id')
    def test_create_resource_invalid_url(self, mock_get_channel_by_id, mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user_by_email.return_value = mock_user
        mock_get_channel_by_id.return_value = "mocked_channel"

        self.mock_validate_url.return_value = False
        
        payload = self.valid_payload.copy()
        
        response = self.app.post(
            '/resources/create',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('url is invalid', response.data.decode())

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_channel_by_id')
    def test_create_resource_invalid_name(self, mock_get_channel_by_id, mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user_by_email.return_value = mock_user
        mock_get_channel_by_id.return_value = "mocked_channel"

        self.mock_validate_name.return_value = False
        
        payload = self.valid_payload.copy()
        
        response = self.app.post(
            '/resources/create',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('name is invalid', response.data.decode())
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_channel_by_id')
    def test_create_resource_missing_channels(self, mock_get_channel_by_id, mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user_by_email.return_value = mock_user
        mock_get_channel_by_id.return_value = "mocked_channel"

        payload = self.valid_payload.copy()
        del payload['channels']
        
        response = self.app.post(
            '/resources/create',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('at least one channel should be specified', response.data.decode())
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_channel_by_id')
    def test_create_resource_channel_not_found(self, mock_get_channel_by_id, mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user_by_email.return_value = mock_user
        mock_get_channel_by_id.return_value = None
        
        response = self.app.post(
            '/resources/create',
            data=json.dumps(self.valid_payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertIn('channel', response.data.decode())
    
    def test_create_resource_unauthorized(self):
        with patch('api.main.token_required', side_effect=Exception('Unauthorized')):
            response = self.app.post(
                '/resources/create',
                data=json.dumps(self.valid_payload),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 403)
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_channel_by_id')
    def test_create_resource_invalid_description(self, mock_get_channel_by_id, mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user_by_email.return_value = mock_user
        mock_get_channel_by_id.return_value = "mocked_channel"

        self.mock_validate_description.return_value = False
        
        payload = self.valid_payload.copy()
        
        response = self.app.post(
            '/resources/create',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('description is invalid', response.data.decode())

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_channel_by_id')
    def test_create_resource_invalid_keywords(self, mock_get_channel_by_id, mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user_by_email.return_value = mock_user
        mock_get_channel_by_id.return_value = "mocked_channel"

        self.mock_validate_keywords.return_value = False
        
        payload = self.valid_payload.copy()
        
        response = self.app.post(
            '/resources/create',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('keywords are invalid', response.data.decode())

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_channel_by_id')
    def test_create_resource_missing_interval(self, mock_get_channel_by_id, mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user_by_email.return_value = mock_user
        mock_get_channel_by_id.return_value = "mocked_channel"

        payload = self.valid_payload.copy()
        del payload['interval']
        
        response = self.app.post(
            '/resources/create',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('interval is missing', response.data.decode())

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_channel_by_id')
    def test_create_resource_invalid_interval(self, mock_get_channel_by_id, mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user_by_email.return_value = mock_user
        mock_get_channel_by_id.return_value = "mocked_channel"

        self.mock_validate_interval.return_value = False
        
        payload = self.valid_payload.copy()
        
        response = self.app.post(
            '/resources/create',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('interval is invalid', response.data.decode())

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_channel_by_id')
    def test_create_resource_invalid_starts_from(self, mock_get_channel_by_id, mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user_by_email.return_value = mock_user
        mock_get_channel_by_id.return_value = "mocked_channel"

        self.mock_validate_date_time.return_value = None
        
        payload = self.valid_payload.copy()

        payload['starts_from'] = 'invalid_timestamp'

        response = self.app.post(
            '/resources/create',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('starts_from is invalid', response.data.decode())
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_channel_by_id')
    def test_create_resource_invalid_zone_type(self, mock_get_channel_by_id, mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user_by_email.return_value = mock_user
        mock_get_channel_by_id.return_value = "mocked_channel"

        payload = self.valid_payload.copy()
        payload['zone_type'] = 'invalid_zone_type'
        
        response = self.app.post(
            '/resources/create',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('zone_type is invalid', response.data.decode())

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_channel_by_id')
    def test_create_resource_invalid_polygon(self, mock_get_channel_by_id, mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user_by_email.return_value = mock_user
        mock_get_channel_by_id.return_value = "mocked_channel"

        self.mock_validate_polygon.return_value = False
        
        payload = self.valid_payload.copy()
        payload['zone_type'] = 'zone'
        payload['areas'] = [{"x": 10, "y": 10, "width": 100, "height": 100}]
        
        response = self.app.post(
            '/resources/create',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('polygon is invalid', response.data.decode())
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_resource_by_resource_id')
    @patch('api.main.validate_uuid')
    def test_get_resource_success(self, mock_validate_uuid, mock_get_channel_resource, 
                                 mock_get_resource, mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_user.is_admin = False
        mock_get_user_by_email.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource

        channel1 = MagicMock()
        channel1.channel_id = "channel1"
        channel1.enabled = True
        channel2 = MagicMock()
        channel2.channel_id = "channel2"
        channel2.enabled = False
        mock_get_channel_resource.return_value = [channel1, channel2]

        response = self.app.get(
            '/resources/1',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["resource"]["id"], 1)
        self.assertEqual(response_data["resource"]["url"], "https://example.com")
        self.assertEqual(response_data["resource"]["channels"], ["channel1"])

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    def test_get_resource_invalid_uuid(self, mock_validate_uuid, mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user_by_email.return_value = mock_user
        mock_validate_uuid.return_value = False

        invalid_id = "not-a-uuid"
        response = self.app.get(
            f'/resources/{invalid_id}',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('resource_id is invalid', response.data.decode())

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.validate_uuid')
    def test_get_resource_not_found(self, mock_validate_uuid, mock_get_resource, 
                                   mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user_by_email.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = None

        response = self.app.get(
            '/resources/1',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )

        self.assertEqual(response.status_code, 404)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_resource_by_resource_id')
    @patch('api.main.validate_uuid')
    def test_get_resource_with_no_starts_from(self, mock_validate_uuid, mock_get_channel_resource, 
                                            mock_get_resource, mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user_by_email.return_value = mock_user
        mock_validate_uuid.return_value = True

        resource_without_start = self.resource
        resource_without_start.starts_from = None
        mock_get_resource.return_value = resource_without_start
        
        mock_get_channel_resource.return_value = []

        response = self.app.get(
            '/resources/1',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["resource"]["starts_from"], None)
        self.assertEqual(response_data["resource"]["channels"], [])

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_resource_by_resource_id')
    @patch('api.main.validate_uuid')
    def test_get_resource_with_all_channels_disabled(self, mock_validate_uuid, mock_get_channel_resource, 
                                                   mock_get_resource, mock_get_user_by_email, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user_by_email.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource

        channel1 = MagicMock()
        channel1.channel_id = "channel1"
        channel1.enabled = False
        channel2 = MagicMock()
        channel2.channel_id = "channel2"
        channel2.enabled = False
        mock_get_channel_resource.return_value = [channel1, channel2]

        response = self.app.get(
            '/resources/1',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["resource"]["channels"], [])

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_get_resource_unauthorized(self, mock_get_user_by_email, mock_jwt_decode):
        response = self.app.get('/resources/1')
        self.assertIn(response.status_code, [401, 403])
    

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.update_resource')
    @patch('api.main.update_resource_channels')
    @patch('api.main.validate_uuid')
    @patch('api.main.validate_description')
    @patch('api.main.validate_keywords')
    @patch('api.main.validate_interval')
    @patch('api.main.get_interval')
    @patch('api.main.validate_date_time')
    @patch('api.main.update_daemon_cron_job_for_resource')
    def test_patch_resource_success(self, mock_update_cron, mock_validate_date, mock_get_interval, 
                                   mock_validate_interval, mock_validate_keywords, mock_validate_description, 
                                   mock_validate_uuid, mock_update_channels, mock_update_resource, 
                                   mock_get_resource, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.side_effect = [self.resource, self.resource]
        mock_validate_description.return_value = True
        mock_validate_keywords.return_value = True
        mock_validate_interval.return_value = True
        mock_get_interval.return_value = "* * * * *"
        mock_validate_date.return_value = datetime(2023, 2, 1, 12, 0, 0)
        payload = {
            "description": "Updated Description",
            "keywords": ["updated", "keywords"],
            "interval": "* * * * *",
            "enabled": False,
            "areas": {"sensitivity": 0.05},
            "channels": [str(uuid.uuid4())],
            "starts_from": 228228227
        }
        
        response = self.app.patch(
            f'/resources/1',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["resource"]["id"], 1)
        mock_update_resource.assert_called_once()
        mock_update_channels.assert_called_once()
        mock_update_cron.assert_called_once()

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    def test_patch_resource_invalid_uuid(self, mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = False
        
        response = self.app.patch(
            f'/resources/invalid-uuid',
            data=json.dumps({}),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('resource_id is invalid', response.data.decode())

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.validate_uuid')
    def test_patch_resource_not_found(self, mock_validate_uuid, mock_get_resource, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = None
        
        response = self.app.patch(
            f'/resources/1',
            data=json.dumps({}),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertIn(f'resource 1 not found', response.data.decode())

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.validate_uuid')
    @patch('api.main.validate_description')
    def test_patch_resource_invalid_description(self, mock_validate_description, mock_validate_uuid, 
                                              mock_get_resource, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        mock_validate_description.return_value = False
        
        payload = {
            "description": "Invalid Description"
        }
        
        response = self.app.patch(
            f'/resources/1',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('description is invalid', response.data.decode())

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.validate_uuid')
    @patch('api.main.validate_description')
    @patch('api.main.validate_keywords')
    def test_patch_resource_invalid_keywords(self, mock_validate_keywords, mock_validate_description, 
                                           mock_validate_uuid, mock_get_resource, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        mock_validate_description.return_value = True
        mock_validate_keywords.return_value = False
        
        payload = {
            "description": "Valid Description",
            "keywords": ["invalid", "keywords"]
        }
        
        response = self.app.patch(f'/resources/1',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('keywords are invalid', response.data.decode())

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.validate_uuid')
    @patch('api.main.validate_description')
    @patch('api.main.validate_keywords')
    @patch('api.main.validate_interval')
    def test_patch_resource_invalid_interval(self, mock_validate_interval, mock_validate_keywords, 
                                           mock_validate_description, mock_validate_uuid, 
                                           mock_get_resource, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        mock_validate_description.return_value = True
        mock_validate_keywords.return_value = True
        mock_validate_interval.return_value = False
        
        payload = {
            "description": "Valid Description",
            "keywords": ["valid", "keywords"],
            "interval": "invalid-interval"
        }
        
        response = self.app.patch(
            f'/resources/1',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('interval is invalid', response.data.decode())

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_by_id')
    @patch('api.main.validate_uuid')
    def test_patch_resource_channel_not_found(self, mock_validate_uuid, mock_get_channel, 
                                            mock_get_resource, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        mock_get_channel.return_value = None
        
        channel_id = str(uuid.uuid4())
        payload = {
            "channels": [channel_id]
        }
        
        response = self.app.patch(
            f'/resources/1',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertIn(f'channel {channel_id} not found', response.data.decode())

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.validate_uuid')
    def test_patch_resource_sensitivity_without_polygon(self, mock_validate_uuid, 
                                                     mock_get_resource, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        
        resource_without_polygon = self.resource
        resource_without_polygon.polygon = None
        mock_get_resource.return_value = resource_without_polygon
        
        payload = {
            "sensitivity": 75.0
        }
        
        response = self.app.patch(
            f'/resources/1',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('sensitivity and polygon are mutually exclusive', response.data.decode())

if __name__ == '__main__':
    unittest.main()
