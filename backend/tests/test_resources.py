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
        self.mock_get_interval.return_value = "* * * * *"
        
        self.validate_date_time_patcher = patch('api.main.validate_date_time')
        self.mock_validate_date_time = self.validate_date_time_patcher.start()
        self.mock_validate_date_time.return_value = None
        
        self.validate_polygon_patcher = patch('api.main.validate_polygon')
        self.mock_validate_polygon = self.validate_polygon_patcher.start()
        self.mock_validate_polygon.return_value = True

        self.resource_id = '1'
        self.channel_id = str(uuid.uuid4())
        self.channel = MagicMock()
        self.channel.id = self.channel_id
        
        self.channel_resource = MagicMock()
        self.channel_resource.channel_id = self.channel_id
        self.channel_resource.resource_id = self.resource_id
        self.channel_resource.enabled = True

        self.active_channel_id = str(uuid.uuid4())
        self.inactive_channel_id = str(uuid.uuid4())

        self.active_channel_resource = MagicMock()
        self.active_channel_resource.channel_id = self.active_channel_id
        self.active_channel_resource.resource_id = self.resource_id
        self.active_channel_resource.enabled = True
        
        self.inactive_channel_resource = MagicMock()
        self.inactive_channel_resource.channel_id = self.inactive_channel_id
        self.inactive_channel_resource.resource_id = self.resource_id
        self.inactive_channel_resource.enabled = False
    
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
            headers={'Authorization': f'bearer: {self.valid_token}'}
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
        resource_without_polygon.polygon = {"sensitivity": 5}
        mock_get_resource.return_value = resource_without_polygon
        
        payload = {
            "sensitivity": 75.0
        }
        
        response = self.app.patch(
            f'/resources/1',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.validate_uuid')
    def test_patch_resource_invalid_sensitivity_type(self, mock_validate_uuid, 
                                                mock_get_resource, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        
        payload = {
            "sensitivity": "high"
        }
        
        response = self.app.patch(
            f'/resources/1',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('sensitivity is invalid', response.data.decode())

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.validate_uuid')
    @patch('api.main.validate_date_time')
    def test_patch_resource_invalid_starts_from(self, mock_validate_date_time, mock_validate_uuid, 
                                            mock_get_resource, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        mock_validate_date_time.return_value = False
        
        payload = {
            "starts_from": "invalid-date-format"
        }
        
        response = self.app.patch(
            f'/resources/1',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('starts_from is invalid', response.data.decode())

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.update_resource')
    @patch('api.main.update_resource_channels')
    @patch('api.main.validate_uuid')
    @patch('api.main.update_daemon_cron_job_for_resource')
    def test_patch_resource_only_enabled(self, mock_update_cron, mock_validate_uuid, 
                                        mock_update_channels, mock_update_resource, 
                                        mock_get_resource, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.side_effect = [self.resource, self.resource]
        
        payload = {
            "enabled": False
        }
        
        response = self.app.patch(
            f'/resources/1',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        mock_update_resource.assert_called_once_with(
            cfg.postgres,
            '1',
            None,
            None,
            None,
            False,
            self.resource.polygon,
            None,
        )
        mock_update_cron.assert_called_once()
        mock_update_channels.assert_not_called()

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.validate_uuid')
    def test_patch_resource_invalid_channel_uuid(self, mock_validate_uuid, 
                                            mock_get_resource, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource

        mock_validate_uuid.side_effect = [True, False]
        
        payload = {
            "channels": ["invalid-channel-uuid"]
        }
        
        response = self.app.patch(
            f'/resources/1',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('channel uuid invalid-channel-uuid is invalid', response.data.decode())

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.update_resource')
    @patch('api.main.update_daemon_cron_job_for_resource')
    @patch('api.main.validate_uuid')
    def test_patch_resource_with_list_polygon(self, mock_validate_uuid, mock_update_cron, 
                                            mock_update_resource, mock_get_resource, 
                                            mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        
        resource_with_list_polygon = self.resource
        resource_with_list_polygon.polygon = [{"sensitivity": 50, "x": 10, "y": 10, "width": 100, "height": 100}]
        mock_get_resource.side_effect = [resource_with_list_polygon, resource_with_list_polygon]
        
        payload = {
            "areas": [{"x": 20, "y": 20, "width": 200, "height": 200}]
        }
        
        response = self.app.patch(
            f'/resources/1',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        args, kwargs = mock_update_resource.call_args
        self.assertEqual(args[6][0]['sensitivity'], 50)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.update_resource')
    @patch('api.main.update_daemon_cron_job_for_resource')
    @patch('api.main.validate_uuid')
    def test_patch_resource_with_object_polygon(self, mock_validate_uuid, mock_update_cron, 
                                            mock_update_resource, mock_get_resource, 
                                            mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        
        resource_with_object_polygon = self.resource
        resource_with_object_polygon.polygon = {"sensitivity": 50, "x": 10, "y": 10, "width": 100, "height": 100}
        mock_get_resource.side_effect = [resource_with_object_polygon, resource_with_object_polygon]
        payload = {
            "areas": {"x": 20, "y": 20, "width": 200, "height": 200}
        }
        
        response = self.app.patch(
            f'/resources/1',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        args, kwargs = mock_update_resource.call_args
        self.assertEqual(args[6]['sensitivity'], 50)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.update_resource')
    @patch('api.main.update_daemon_cron_job_for_resource')
    @patch('api.main.validate_uuid')
    def test_patch_resource_with_sensitivity(self, mock_validate_uuid, mock_update_cron, 
                                        mock_update_resource, mock_get_resource, 
                                        mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.side_effect = [self.resource, self.resource]
        
        payload = {
            "sensitivity": 75.0
        }
        
        response = self.app.patch(
            f'/resources/1',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        args, kwargs = mock_update_resource.call_args

        updated_polygon = args[6]
        self.assertEqual(updated_polygon['sensitivity'], 75.0)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.update_resource')
    @patch('api.main.update_resource_channels')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_channel_by_id')
    @patch('api.main.update_daemon_cron_job_for_resource')
    def test_patch_resource_with_channels(self, mock_update_cron, mock_get_channel, mock_validate_uuid, 
                                        mock_update_channels, mock_update_resource, 
                                        mock_get_resource, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.side_effect = [self.resource, self.resource]
        
        channel_id = str(uuid.uuid4())
        mock_channel = MagicMock()
        mock_channel.id = channel_id
        mock_get_channel.return_value = mock_channel
        
        payload = {
            "channels": [channel_id]
        }
        
        response = self.app.patch(
            f'/resources/1',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        mock_update_channels.assert_called_once_with(cfg.postgres, '1', [channel_id])
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.update_resource')
    @patch('api.main.update_daemon_cron_job_for_resource')
    @patch('api.main.validate_uuid')
    def test_delete_resource_success(self, mock_validate_uuid, mock_update_cron, 
                                   mock_update_resource, mock_get_resource, 
                                   mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True

        mock_get_resource.side_effect = [self.resource, self.resource]
        
        response = self.app.delete(
            f'/resources/1',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        mock_update_resource.assert_called_once_with(
            cfg.postgres, 
            '1', 
            None,
            None,
            None,
            False,
            None
        )
        mock_update_cron.assert_called_once_with(self.resource, cfg.server)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    def test_delete_resource_invalid_uuid(self, mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = False
        
        response = self.app.delete(
            '/resources/invalid-uuid',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('resource_id is invalid', response.data.decode())

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.validate_uuid')
    def test_delete_resource_not_found(self, mock_validate_uuid, mock_get_resource, 
                                     mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = None
        
        response = self.app.delete(
            f'/resources/1',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertIn(f'resource 1 not found', response.data.decode())

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.update_resource')
    @patch('api.main.update_daemon_cron_job_for_resource')
    @patch('api.main.validate_uuid')
    def test_delete_resource_cron_job_updated(self, mock_validate_uuid, mock_update_cron, 
                                            mock_update_resource, mock_get_resource, 
                                            mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        
        updated_resource = self.resource
        updated_resource.enabled = False
        mock_get_resource.side_effect = [self.resource, updated_resource]
        
        response = self.app.delete(
            f'/resources/1',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        mock_update_cron.assert_called_once_with(updated_resource, cfg.server)
        self.assertEqual(response.data.decode(), '{}\n')

    def test_delete_resource_unauthorized(self):
        response = self.app.delete(f'/resources/1')
        
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_all_resources')
    @patch('api.main.get_channel_resource_by_resource_id')
    def test_all_resources_success(self, mock_get_channel_resource, mock_get_all_resources, 
                                 mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        mock_get_all_resources.return_value = [self.resource, self.resource]
        
        def get_channels_for_resource(conn, resource_id):
            return []
        
        mock_get_channel_resource.side_effect = get_channels_for_resource
        
        response = self.app.get(
            '/resources/all',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        self.assertIn('resources', response_data)
        resources = response_data['resources']
        self.assertEqual(len(resources), 2)
        
        resource1_data = next((r for r in resources if r['id'] == self.resource.id), None)
        self.assertIsNotNone(resource1_data)
        self.assertEqual(resource1_data['url'], "https://example.com")
        self.assertEqual(resource1_data['name'], "Test Resource")
        self.assertEqual(resource1_data['description'], "A test resource")
        self.assertEqual(resource1_data['keywords'], ["test", "example"])
        self.assertEqual(resource1_data['interval'], "* * * * *")
        self.assertEqual(resource1_data['starts_from'], None)
        self.assertTrue(resource1_data['make_screenshot'])
        self.assertTrue(resource1_data['enabled'])
        self.assertEqual(resource1_data['areas'], self.resource.polygon)
        self.assertEqual(resource1_data['channels'], [])

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_all_resources')
    @patch('api.main.get_channel_resource_by_resource_id')
    def test_all_resources_empty_list(self, mock_get_channel_resource, mock_get_all_resources, 
                                    mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        mock_get_all_resources.return_value = []
        
        response = self.app.get(
            '/resources/all',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        self.assertIn('resources', response_data)
        self.assertEqual(len(response_data['resources']), 0)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_all_resources')
    @patch('api.main.get_channel_resource_by_resource_id')
    def test_all_resources_with_no_channels(self, mock_get_channel_resource, mock_get_all_resources, 
                                          mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        mock_get_all_resources.return_value = [self.resource]
        
        mock_get_channel_resource.return_value = []
        
        response = self.app.get(
            '/resources/all',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        resources = response_data['resources']
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]['channels'], [])

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_all_resources')
    @patch('api.main.get_channel_resource_by_resource_id')
    def test_all_resources_with_only_disabled_channels(self, mock_get_channel_resource, mock_get_all_resources, 
                                                    mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        mock_get_all_resources.return_value = [self.resource]
        
        disabled_channel = MagicMock()
        disabled_channel.channel_id = str(uuid.uuid4())
        disabled_channel.enabled = False
        mock_get_channel_resource.return_value = [disabled_channel]
        
        response = self.app.get(
            '/resources/all',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        resources = response_data['resources']
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]['channels'], [])

    def test_all_resources_unauthorized(self):
        response = self.app.get('/resources/all')
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_by_id')
    @patch('api.main.get_channel_resource_by_resource_id')
    @patch('api.main.create_channel_resource')
    def test_add_channel_to_resource_success(self, mock_create_channel_resource, 
                                           mock_get_channel_resource, mock_get_channel, 
                                           mock_get_resource, mock_validate_uuid, 
                                           mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        mock_get_channel.return_value = self.channel
        mock_get_channel_resource.return_value = []
        
        payload = {
            "resource_id": self.resource_id,
            "channel_id": self.channel_id
        }
        
        response = self.app.post(
            '/add_channel_to_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["message"], "channel linked to resource")
        
        mock_create_channel_resource.assert_called_once_with(
            cfg.postgres, self.channel_id, self.resource_id
        )

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_by_id')
    @patch('api.main.get_channel_resource_by_resource_id')
    @patch('api.main.create_channel_resource')
    def test_add_channel_already_linked(self, mock_create_channel_resource, 
                                      mock_get_channel_resource, mock_get_channel, 
                                      mock_get_resource, mock_validate_uuid, 
                                      mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        mock_get_channel.return_value = self.channel
        
        mock_get_channel_resource.return_value = [self.channel_resource]
        
        payload = {
            "resource_id": self.resource_id,
            "channel_id": self.channel_id
        }
        
        response = self.app.post(
            '/add_channel_to_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["message"], "channel already linked to resource")
        
        mock_create_channel_resource.assert_not_called()

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_by_id')
    @patch('api.main.get_channel_resource_by_resource_id')
    @patch('api.main.create_channel_resource')
    def test_add_channel_disabled_link(self, mock_create_channel_resource, 
                                     mock_get_channel_resource, mock_get_channel, 
                                     mock_get_resource, mock_validate_uuid, 
                                     mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        mock_get_channel.return_value = self.channel
        
        disabled_channel_resource = MagicMock()
        disabled_channel_resource.channel_id = self.channel_id
        disabled_channel_resource.resource_id = self.resource_id
        disabled_channel_resource.enabled = False
        mock_get_channel_resource.return_value = [disabled_channel_resource]
        
        payload = {
            "resource_id": self.resource_id,
            "channel_id": self.channel_id
        }
        
        response = self.app.post(
            '/add_channel_to_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["message"], "channel linked to resource")
        
        mock_create_channel_resource.assert_called_once_with(
            cfg.postgres, self.channel_id, self.resource_id
        )

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_add_channel_missing_parameters(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        payload = {
            "resource_id": self.resource_id
        }
        
        response = self.app.post(
            '/add_channel_to_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], "resource_id and channel_id are required")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    def test_add_channel_invalid_uuid(self, mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = False
        
        payload = {
            "resource_id": "invalid-uuid",
            "channel_id": self.channel_id
        }
        
        response = self.app.post(
            '/add_channel_to_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], "resource_id and channel_id are invalid")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    def test_add_channel_resource_not_found(self, mock_get_resource, 
                                          mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = None
        
        payload = {
            "resource_id": self.resource_id,
            "channel_id": self.channel_id
        }
        
        response = self.app.post(
            '/add_channel_to_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], f"resource {self.resource_id} not found")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_by_id')
    def test_add_channel_channel_not_found(self, mock_get_channel, mock_get_resource, 
                                         mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        mock_get_channel.return_value = None
        
        payload = {
            "resource_id": self.resource_id,
            "channel_id": self.channel_id
        }
        
        response = self.app.post(
            '/add_channel_to_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], f"channel {self.channel_id} not found")

    def test_add_channel_unauthorized(self):
        payload = {
            "resource_id": self.resource_id,
            "channel_id": self.channel_id
        }
        
        response = self.app.post(
            '/add_channel_to_resource/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_by_id')
    @patch('api.main.get_channel_resource_by_resource_id')
    @patch('api.main.create_channel_resource')
    def test_add_channel_different_channel_linked(self, mock_create_channel_resource, 
                                               mock_get_channel_resource, mock_get_channel, 
                                               mock_get_resource, mock_validate_uuid, 
                                               mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        mock_get_channel.return_value = self.channel
        
        different_channel_resource = MagicMock()
        different_channel_resource.channel_id = str(uuid.uuid4())
        different_channel_resource.resource_id = self.resource_id
        different_channel_resource.enabled = True
        mock_get_channel_resource.return_value = [different_channel_resource]
        
        payload = {
            "resource_id": self.resource_id,
            "channel_id": self.channel_id
        }
        
        response = self.app.post(
            '/add_channel_to_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["message"], "channel linked to resource")
        
        mock_create_channel_resource.assert_called_once_with(
            cfg.postgres, self.channel_id, self.resource_id
        )
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    def test_add_channel_one_invalid_uuid(self, mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        mock_validate_uuid.side_effect = [True, False]
        
        payload = {
            "resource_id": self.resource_id,
            "channel_id": "invalid-channel-id"
        }
        
        response = self.app.post(
            '/add_channel_to_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], "resource_id and channel_id are invalid")
        
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_add_channel_deleted_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = "2023-01-01 12:00:00"
        mock_get_user.return_value = mock_user
        
        payload = {
            "resource_id": self.resource_id,
            "channel_id": self.channel_id
        }
        
        response = self.app.post(
            '/add_channel_to_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )

        self.assertEqual(response.status_code, 403)
        
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_add_channel_with_nonexistent_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "nonexistent@example.com"}
        mock_get_user.return_value = None
        
        payload = {
            "resource_id": self.resource_id,
            "channel_id": self.channel_id
        }
        
        response = self.app.post(
            '/add_channel_to_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 401)
        
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_by_id')
    @patch('api.main.get_channel_resource_by_resource_id')
    @patch('api.main.create_channel_resource')
    def test_add_channel_with_multiple_existing_links(self, mock_create_channel_resource, 
                                                  mock_get_channel_resource, mock_get_channel, 
                                                  mock_get_resource, mock_validate_uuid, 
                                                  mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        mock_get_channel.return_value = self.channel
        
        channel_resource1 = MagicMock()
        channel_resource1.channel_id = str(uuid.uuid4())
        channel_resource1.resource_id = self.resource_id
        channel_resource1.enabled = True
        
        channel_resource2 = MagicMock()
        channel_resource2.channel_id = str(uuid.uuid4())
        channel_resource2.resource_id = self.resource_id
        channel_resource2.enabled = True
        
        mock_get_channel_resource.return_value = [channel_resource1, channel_resource2]
        
        payload = {
            "resource_id": self.resource_id,
            "channel_id": self.channel_id
        }
        
        response = self.app.post(
            '/add_channel_to_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["message"], "channel linked to resource")
        
        mock_create_channel_resource.assert_called_once_with(
            cfg.postgres, self.channel_id, self.resource_id
        )
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_by_id')
    @patch('api.main.change_channel_resource_enabled')
    def test_remove_channel_success(self, mock_change_channel_resource, 
                                  mock_get_channel, mock_get_resource, 
                                  mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        
        active_channel = MagicMock()
        active_channel.id = self.channel_id
        active_channel.enabled = True
        mock_get_channel.return_value = active_channel
        
        payload = {
            "resource_id": self.resource_id,
            "channel_id": self.channel_id
        }
        
        response = self.app.delete(
            '/remove_channel_from_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), '{}\n')

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_by_id')
    @patch('api.main.change_channel_resource_enabled')
    def test_remove_channel_already_unlinked(self, mock_change_channel_resource, 
                                           mock_get_channel, mock_get_resource, 
                                           mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        
        inactive_channel = MagicMock()
        inactive_channel.id = self.channel_id
        inactive_channel.enabled = False
        mock_get_channel.return_value = inactive_channel
        
        payload = {
            "resource_id": self.resource_id,
            "channel_id": self.channel_id
        }
        
        response = self.app.delete(
            '/remove_channel_from_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 202)
        response_data = json.loads(response.data.decode())
        self.assertEqual(
            response_data["message"], 
            f"channel {self.channel_id} is already unlinked from resource {self.resource_id}"
        )

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_remove_channel_missing_parameters(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        payload = {
            "resource_id": self.resource_id
        }
        
        response = self.app.delete(
            '/remove_channel_from_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], "resource_id and channel_id are required")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    def test_remove_channel_invalid_uuid(self, mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = False
        
        payload = {
            "resource_id": "invalid-uuid",
            "channel_id": self.channel_id
        }
        
        response = self.app.delete(
            '/remove_channel_from_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], "resource_id and channel_id are invalid")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    def test_remove_channel_resource_not_found(self, mock_get_resource, 
                                             mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = None
        
        payload = {
            "resource_id": self.resource_id,
            "channel_id": self.channel_id
        }
        
        response = self.app.delete(
            '/remove_channel_from_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], f"resource {self.resource_id} not found")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_by_id')
    def test_remove_channel_channel_not_found(self, mock_get_channel, mock_get_resource, 
                                            mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        mock_get_channel.return_value = None
        
        payload = {
            "resource_id": self.resource_id,
            "channel_id": self.channel_id
        }
        
        response = self.app.delete(
            '/remove_channel_from_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(
            response_data["error"], 
            f"channel {self.channel_id} never was linked to resource {self.resource_id}"
        )

    def test_remove_channel_unauthorized(self):
        payload = {
            "resource_id": self.resource_id,
            "channel_id": self.channel_id
        }
        
        response = self.app.delete(
            '/remove_channel_from_resource/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_remove_channel_invalid_json(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        response = self.app.delete(
            '/remove_channel_from_resource/',
            data="invalid json data",
            content_type='application/json',
            headers={'Authorization': f'Bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    def test_remove_channel_one_invalid_uuid(self, mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        mock_validate_uuid.side_effect = [True, False]
        
        payload = {
            "resource_id": self.resource_id,
            "channel_id": "invalid-channel-id"
        }
        
        response = self.app.delete(
            '/remove_channel_from_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], "resource_id and channel_id are invalid")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_remove_channel_deleted_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = 228228227
        mock_get_user.return_value = mock_user
        
        payload = {
            "resource_id": self.resource_id,
            "channel_id": self.channel_id
        }
        
        response = self.app.delete(
            '/remove_channel_from_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 403)
        
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_remove_channel_nonexistent_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "nonexistent@example.com"}
        mock_get_user.return_value = None
        
        payload = {
            "resource_id": self.resource_id,
            "channel_id": self.channel_id
        }
        
        response = self.app.delete(
            '/remove_channel_from_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'Bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 401)
        
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_by_id')
    @patch('api.main.change_channel_resource_enabled')
    def test_remove_channel_verify_correct_payload(self, mock_change_channel_resource, 
                                                mock_get_channel, mock_get_resource, 
                                                mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        
        active_channel = MagicMock()
        active_channel.id = self.channel_id
        active_channel.enabled = True
        mock_get_channel.return_value = active_channel
        
        payload = {
            "resource_id": self.resource_id,
            "channel_id": self.channel_id,
            "extra_field": "Should be ignored",
            "another_extra": 123
        }
        
        response = self.app.delete(
            '/remove_channel_from_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_by_id')
    @patch('api.main.change_channel_resource_enabled')
    def test_remove_channel_idempotent_behavior(self, mock_change_channel_resource, 
                                             mock_get_channel, mock_get_resource, 
                                             mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        
        inactive_channel = MagicMock()
        inactive_channel.id = self.channel_id
        inactive_channel.enabled = False
        mock_get_channel.return_value = inactive_channel
        
        payload = {
            "resource_id": self.resource_id,
            "channel_id": self.channel_id
        }
        
        response1 = self.app.delete(
            '/remove_channel_from_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        response2 = self.app.delete(
            '/remove_channel_from_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response1.status_code, 202)
        self.assertEqual(response2.status_code, 202)
        
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_by_id')
    @patch('api.main.change_channel_resource_enabled')
    def test_remove_channel_empty_request_body(self, mock_change_channel_resource, mock_get_channel, mock_get_resource, 
                                            mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        payload = {}
        
        response = self.app.delete(
            '/remove_channel_from_resource/',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], "resource_id and channel_id are required")
        
        mock_validate_uuid.assert_not_called()
        mock_get_resource.assert_not_called()
        mock_get_channel.assert_not_called()
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_resource_by_resource_id')
    def test_get_channels_by_resource_success(self, mock_get_channel_resource, 
                                           mock_get_resource, mock_validate_uuid, 
                                           mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        
        mock_get_channel_resource.return_value = [
            self.active_channel_resource,
            self.inactive_channel_resource
        ]
        
        response = self.app.get(
            f'/channels_by_resource/{self.resource_id}',
            headers={'Authorization': f'Bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        self.assertIn('channels', response_data)
        self.assertEqual(len(response_data['channels']), 1)
        self.assertEqual(response_data['channels'][0], self.active_channel_id)
        self.assertNotIn(self.inactive_channel_id, response_data['channels'])

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_resource_by_resource_id')
    def test_get_channels_by_resource_no_channels(self, mock_get_channel_resource, 
                                               mock_get_resource, mock_validate_uuid, 
                                               mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        
        mock_get_channel_resource.return_value = []
        
        response = self.app.get(
            f'/channels_by_resource/{self.resource_id}',
            headers={'Authorization': f'Bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        self.assertIn('channels', response_data)
        self.assertEqual(len(response_data['channels']), 0)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_resource_by_resource_id')
    def test_get_channels_by_resource_only_inactive_channels(self, mock_get_channel_resource, 
                                                          mock_get_resource, mock_validate_uuid, 
                                                          mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        
        mock_get_channel_resource.return_value = [self.inactive_channel_resource]
        
        response = self.app.get(
            f'/channels_by_resource/{self.resource_id}',
            headers={'Authorization': f'Bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        self.assertIn('channels', response_data)
        self.assertEqual(len(response_data['channels']), 0)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    @patch('api.main.get_channel_resource_by_resource_id')
    def test_get_channels_by_resource_multiple_active_channels(self, mock_get_channel_resource, 
                                                            mock_get_resource, mock_validate_uuid, 
                                                            mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = self.resource
        
        active_channel1 = MagicMock()
        active_channel1.channel_id = str(uuid.uuid4())
        active_channel1.resource_id = self.resource_id
        active_channel1.enabled = True
        
        active_channel2 = MagicMock()
        active_channel2.channel_id = str(uuid.uuid4())
        active_channel2.resource_id = self.resource_id
        active_channel2.enabled = True
        
        mock_get_channel_resource.return_value = [
            active_channel1,
            active_channel2,
            self.inactive_channel_resource
        ]
        
        response = self.app.get(
            f'/channels_by_resource/{self.resource_id}',
            headers={'Authorization': f'Bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        self.assertIn('channels', response_data)
        self.assertEqual(len(response_data['channels']), 2)
        self.assertIn(active_channel1.channel_id, response_data['channels'])
        self.assertIn(active_channel2.channel_id, response_data['channels'])
        self.assertNotIn(self.inactive_channel_id, response_data['channels'])

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    def test_get_channels_by_resource_invalid_uuid(self, mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = False
        
        response = self.app.get(
            '/channels_by_resource/invalid-uuid',
            headers={'Authorization': f'Bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], "resource_id is invalid")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_resource_by_id')
    def test_get_channels_by_resource_not_found(self, mock_get_resource, 
                                             mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_uuid.return_value = True
        mock_get_resource.return_value = None
        
        response = self.app.get(
            f'/channels_by_resource/{self.resource_id}',
            headers={'Authorization': f'Bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], f"resource {self.resource_id} not found")

    def test_get_channels_by_resource_unauthorized(self):
        response = self.app.get(f'/channels_by_resource/{self.resource_id}')
        
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_get_channels_by_resource_deleted_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = 228228227
        mock_get_user.return_value = mock_user
        
        response = self.app.get(
            f'/channels_by_resource/{self.resource_id}',
            headers={'Authorization': f'Bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 403)


if __name__ == '__main__':
    unittest.main()
