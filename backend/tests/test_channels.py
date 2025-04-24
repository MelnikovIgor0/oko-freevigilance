import json
import unittest
from unittest.mock import patch, MagicMock

from api.main import app, cfg

class TestChannelEndpoints(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_name')
    @patch('api.main.get_channel_by_name')
    @patch('api.main.create_channel')
    def test_new_channel_success(self, mock_create_channel, mock_get_channel, mock_validate_name, 
                                mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        mock_validate_name.return_value = True
        mock_get_channel.return_value = None
        
        mock_channel = MagicMock()
        mock_channel.id = 1
        mock_channel.type = "telegram"
        mock_channel.name = "test_channel"
        mock_channel.enabled = True
        mock_channel.params = {"chat_id": "-100123456789"}
        mock_create_channel.return_value = mock_channel
        
        response = self.app.post(
            '/channels/create',
            data=json.dumps({
                "name": "test_channel",
                "type": "telegram",
                "params": {"chat_id": "-100123456789"}
            }),
            content_type='application/json',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["channel"]["id"], 1)
        self.assertEqual(data["channel"]["type"], "telegram")
        self.assertEqual(data["channel"]["name"], "test_channel")
        self.assertTrue(data["channel"]["enabled"])
        self.assertEqual(data["channel"]["params"], {"chat_id": "-100123456789"})
        
        mock_validate_name.assert_any_call("test_channel")
        mock_validate_name.assert_any_call("telegram")
        mock_get_channel.assert_called_once_with(cfg.postgres, "test_channel")
        mock_create_channel.assert_called_once_with(
            cfg.postgres, 
            {"chat_id": "-100123456789"}, 
            "telegram", 
            "test_channel"
        )
    
    def test_unauthorized_access(self):
        response = self.app.post(
            '/channels/create',
            data=json.dumps({
                "name": "test_channel",
                "type": "telegram",
                "params": {"chat_id": "-100123456789"}
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "token is missing")
        
    def test_invalid_token_format(self):
        response = self.app.post(
            '/channels/create',
            data=json.dumps({
                "name": "test_channel",
                "type": "telegram",
                "params": {"chat_id": "-100123456789"}
            }),
            content_type='application/json',
            headers={"Authorization": "InvalidFormat"}
        )
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "invalid auth token")
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_new_channel_missing_name(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_get_user.return_value = mock_user
        
        response = self.app.post(
            '/channels/create',
            data=json.dumps({
                "type": "telegram",
                "params": {"chat_id": "-100123456789"}
            }),
            content_type='application/json',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "name is missing")
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_name')
    def test_new_channel_invalid_name(self, mock_validate_name, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_get_user.return_value = mock_user
        
        mock_validate_name.return_value = False
        
        response = self.app.post(
            '/channels/create',
            data=json.dumps({
                "name": "invalid@name",
                "type": "telegram",
                "params": {"chat_id": "-100123456789"}
            }),
            content_type='application/json',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "name is invalid")
        mock_validate_name.assert_called_once_with("invalid@name")
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_name')
    @patch('api.main.get_channel_by_name')
    def test_new_channel_already_exists(self, mock_get_channel, mock_validate_name, 
                                      mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_get_user.return_value = mock_user
        
        mock_validate_name.return_value = True
        mock_get_channel.return_value = MagicMock()
        
        response = self.app.post(
            '/channels/create',
            data=json.dumps({
                "name": "existing_channel",
                "type": "telegram",
                "params": {"chat_id": "-100123456789"}
            }),
            content_type='application/json',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "channel already exists")
        mock_get_channel.assert_called_once_with(cfg.postgres, "existing_channel")
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_name')
    @patch('api.main.get_channel_by_name')
    def test_new_channel_missing_type(self, mock_get_channel, mock_validate_name, 
                                    mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_get_user.return_value = mock_user
        
        mock_validate_name.return_value = True
        mock_get_channel.return_value = None
        
        response = self.app.post(
            '/channels/create',
            data=json.dumps({
                "name": "test_channel",
                "params": {"chat_id": "-100123456789"}
            }),
            content_type='application/json',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "type is missing")
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_name')
    @patch('api.main.get_channel_by_name')
    def test_new_channel_invalid_type(self, mock_get_channel, mock_validate_name, 
                                    mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_get_user.return_value = mock_user
        
        mock_validate_name.side_effect = [True, False]
        mock_get_channel.return_value = None
        
        response = self.app.post(
            '/channels/create',
            data=json.dumps({
                "name": "test_channel",
                "type": "invalid@type",
                "params": {"chat_id": "-100123456789"}
            }),
            content_type='application/json',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "type is invalid")
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_name')
    @patch('api.main.get_channel_by_name')
    def test_new_channel_missing_params(self, mock_get_channel, mock_validate_name, 
                                       mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_get_user.return_value = mock_user
        
        mock_validate_name.return_value = True
        mock_get_channel.return_value = None
        
        response = self.app.post(
            '/channels/create',
            data=json.dumps({
                "name": "test_channel",
                "type": "telegram"
            }),
            content_type='application/json',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "params are missing")
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_name')
    @patch('api.main.get_channel_by_name')
    def test_new_channel_empty_params(self, mock_get_channel, mock_validate_name, 
                                    mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_get_user.return_value = mock_user
        
        mock_validate_name.return_value = True
        mock_get_channel.return_value = None
        
        response = self.app.post(
            '/channels/create',
            data=json.dumps({
                "name": "test_channel",
                "type": "telegram",
                "params": {}
            }),
            content_type='application/json',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "params are missing")
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_all_channels')
    def test_find_all_channels_success(self, mock_get_all_channels, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        mock_channel1 = MagicMock()
        mock_channel1.id = 1
        mock_channel1.type = "telegram"
        mock_channel1.name = "channel1"
        mock_channel1.enabled = True
        mock_channel1.params = {"token": "123456:ABC-DEF1", "chat_id": "-100123456781"}
        
        mock_channel2 = MagicMock()
        mock_channel2.id = 2
        mock_channel2.type = "slack"
        mock_channel2.name = "channel2"
        mock_channel2.enabled = False
        mock_channel2.params = {"webhook_url": "https://hooks.slack.com/services/xxx/yyy/zzz"}
        
        mock_get_all_channels.return_value = [mock_channel1, mock_channel2]
        
        response = self.app.get(
            '/channels/all',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        
        self.assertEqual(len(data["channels"]), 2)
        
        self.assertEqual(data["channels"][0]["id"], 1)
        self.assertEqual(data["channels"][0]["type"], "telegram")
        self.assertEqual(data["channels"][0]["name"], "channel1")
        self.assertTrue(data["channels"][0]["enabled"])
        self.assertEqual(data["channels"][0]["params"], {"token": "123456:ABC-DEF1", "chat_id": "-100123456781"})
        
        self.assertEqual(data["channels"][1]["id"], 2)
        self.assertEqual(data["channels"][1]["type"], "slack")
        self.assertEqual(data["channels"][1]["name"], "channel2")
        self.assertFalse(data["channels"][1]["enabled"])
        self.assertEqual(data["channels"][1]["params"], {"webhook_url": "https://hooks.slack.com/services/xxx/yyy/zzz"})
        
        mock_get_all_channels.assert_called_once_with(cfg.postgres)
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_all_channels')
    def test_find_all_channels_empty(self, mock_get_all_channels, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        mock_get_all_channels.return_value = []
        
        response = self.app.get(
            '/channels/all',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        
        self.assertEqual(len(data["channels"]), 0)
        self.assertEqual(data["channels"], [])
        
        mock_get_all_channels.assert_called_once_with(cfg.postgres)
    
    def test_unauthorized_access(self):
        response = self.app.get('/channels/all')
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "token is missing")
    
    def test_invalid_token_format(self):
        response = self.app.get(
            '/channels/all',
            headers={"Authorization": "InvalidFormat"}
        )
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "invalid auth token")
    
    @patch('api.main.jwt.decode')
    def test_invalid_token(self, mock_jwt_decode):
        mock_jwt_decode.side_effect = Exception("Invalid token")
        
        response = self.app.get(
            '/channels/all',
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "token is invalid/expired")
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_user_not_found(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "nonexistent@example.com"}
        mock_get_user.return_value = None
        
        response = self.app.get(
            '/channels/all',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "user nonexistent@example.com not found")
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_channel_by_id')
    def test_get_channel_success(self, mock_get_channel_by_id, mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        mock_validate_uuid.return_value = True
        
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        mock_channel = MagicMock()
        mock_channel.id = channel_id
        mock_channel.type = "telegram"
        mock_channel.name = "test_channel"
        mock_channel.enabled = True
        mock_channel.params = {"token": "123456:ABC-DEF", "chat_id": "-100123456789"}
        mock_get_channel_by_id.return_value = mock_channel
        
        response = self.app.get(
            f'/channels/{channel_id}',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        
        self.assertEqual(data["channel"]["id"], channel_id)
        self.assertEqual(data["channel"]["type"], "telegram")
        self.assertEqual(data["channel"]["name"], "test_channel")
        self.assertTrue(data["channel"]["enabled"])
        self.assertEqual(data["channel"]["params"], {"token": "123456:ABC-DEF", "chat_id": "-100123456789"})
        
        mock_validate_uuid.assert_called_once_with(channel_id)
        mock_get_channel_by_id.assert_called_once_with(cfg.postgres, channel_id)
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    def test_get_channel_invalid_id(self, mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        mock_validate_uuid.return_value = False
        
        channel_id = "invalid-id"
        
        response = self.app.get(
            f'/channels/{channel_id}',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "channel_id is invalid")
        mock_validate_uuid.assert_called_once_with(channel_id)
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_channel_by_id')
    def test_get_channel_not_found(self, mock_get_channel_by_id, mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        mock_validate_uuid.return_value = True
        
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        mock_get_channel_by_id.return_value = None
        
        response = self.app.get(
            f'/channels/{channel_id}',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], f"channel {channel_id} not found")
        
        mock_validate_uuid.assert_called_once_with(channel_id)
        mock_get_channel_by_id.assert_called_once_with(cfg.postgres, channel_id)
    
    def test_unauthorized_access(self):
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = self.app.get(f'/channels/{channel_id}')
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "token is missing")
    
    def test_invalid_token_format(self):
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = self.app.get(
            f'/channels/{channel_id}',
            headers={"Authorization": "InvalidFormat"}
        )
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "invalid auth token")
    
    @patch('api.main.jwt.decode')
    def test_invalid_token(self, mock_jwt_decode):
        mock_jwt_decode.side_effect = Exception("Invalid token")
        
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = self.app.get(
            f'/channels/{channel_id}',
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "token is invalid/expired")
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_user_not_found(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "nonexistent@example.com"}
        mock_get_user.return_value = None
        
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = self.app.get(
            f'/channels/{channel_id}',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "user nonexistent@example.com not found")
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_channel_by_id')
    @patch('api.main.update_channel')
    def test_patch_channel_success_full_update(self, mock_update_channel, mock_get_channel_by_id, 
                                       mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        mock_validate_uuid.return_value = True
        
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        mock_channel = MagicMock()
        mock_channel.id = channel_id
        mock_get_channel_by_id.return_value = mock_channel
        
        new_params = {"token": "updated-token", "chat_id": "-100987654321"}
        new_enabled = False
        
        response = self.app.patch(
            f'/channels/{channel_id}',
            data=json.dumps({
                "params": new_params,
                "enabled": new_enabled
            }),
            content_type='application/json',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data, {})
        
        mock_validate_uuid.assert_called_once_with(channel_id)
        mock_get_channel_by_id.assert_called_once_with(cfg.postgres, channel_id)
        mock_update_channel.assert_called_once_with(cfg.postgres, channel_id, new_params, new_enabled)
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_channel_by_id')
    @patch('api.main.update_channel')
    def test_patch_channel_success_params_only(self, mock_update_channel, mock_get_channel_by_id, 
                                      mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        mock_validate_uuid.return_value = True
        
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        mock_channel = MagicMock()
        mock_channel.id = channel_id
        mock_get_channel_by_id.return_value = mock_channel
        
        new_params = {"token": "updated-token", "chat_id": "-100987654321"}
        
        response = self.app.patch(
            f'/channels/{channel_id}',
            data=json.dumps({
                "params": new_params
            }),
            content_type='application/json',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data, {})
        
        mock_validate_uuid.assert_called_once_with(channel_id)
        mock_get_channel_by_id.assert_called_once_with(cfg.postgres, channel_id)
        mock_update_channel.assert_called_once_with(cfg.postgres, channel_id, new_params, None)
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_channel_by_id')
    @patch('api.main.update_channel')
    def test_patch_channel_success_enabled_only(self, mock_update_channel, mock_get_channel_by_id, 
                                       mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        mock_validate_uuid.return_value = True
        
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        mock_channel = MagicMock()
        mock_channel.id = channel_id
        mock_get_channel_by_id.return_value = mock_channel
        
        new_enabled = False
        
        response = self.app.patch(
            f'/channels/{channel_id}',
            data=json.dumps({
                "enabled": new_enabled
            }),
            content_type='application/json',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data, {})
        
        mock_validate_uuid.assert_called_once_with(channel_id)
        mock_get_channel_by_id.assert_called_once_with(cfg.postgres, channel_id)
        mock_update_channel.assert_called_once_with(cfg.postgres, channel_id, None, new_enabled)
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_channel_by_id')
    @patch('api.main.update_channel')
    def test_patch_channel_success_empty_update(self, mock_update_channel, mock_get_channel_by_id, 
                                       mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        mock_validate_uuid.return_value = True
        
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        mock_channel = MagicMock()
        mock_channel.id = channel_id
        mock_get_channel_by_id.return_value = mock_channel
        
        response = self.app.patch(
            f'/channels/{channel_id}',
            data=json.dumps({}),
            content_type='application/json',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data, {})
        
        mock_validate_uuid.assert_called_once_with(channel_id)
        mock_get_channel_by_id.assert_called_once_with(cfg.postgres, channel_id)
        mock_update_channel.assert_called_once_with(cfg.postgres, channel_id, None, None)
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    def test_patch_channel_invalid_id(self, mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        mock_validate_uuid.return_value = False
        
        channel_id = "invalid-id"
        
        response = self.app.patch(
            f'/channels/{channel_id}',
            data=json.dumps({
                "params": {"token": "updated-token"},
                "enabled": False
            }),
            content_type='application/json',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "channel_id is invalid")
        mock_validate_uuid.assert_called_once_with(channel_id)
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_channel_by_id')
    def test_patch_channel_not_found(self, mock_get_channel_by_id, mock_validate_uuid, 
                                  mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        mock_validate_uuid.return_value = True
        
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        mock_get_channel_by_id.return_value = None
        
        response = self.app.patch(
            f'/channels/{channel_id}',
            data=json.dumps({
                "params": {"token": "updated-token"},
                "enabled": False
            }),
            content_type='application/json',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], f"channel {channel_id} not found")
        
        mock_validate_uuid.assert_called_once_with(channel_id)
        mock_get_channel_by_id.assert_called_once_with(cfg.postgres, channel_id)
    
    def test_unauthorized_access(self):
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = self.app.patch(
            f'/channels/{channel_id}',
            data=json.dumps({
                "params": {"token": "updated-token"},
                "enabled": False
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "token is missing")
    
    def test_invalid_token_format(self):
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = self.app.patch(
            f'/channels/{channel_id}',
            data=json.dumps({
                "params": {"token": "updated-token"},
                "enabled": False
            }),
            content_type='application/json',
            headers={"Authorization": "InvalidFormat"}
        )
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "invalid auth token")
    
    @patch('api.main.jwt.decode')
    def test_invalid_token(self, mock_jwt_decode):
        mock_jwt_decode.side_effect = Exception("Invalid token")
        
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = self.app.patch(
            f'/channels/{channel_id}',
            data=json.dumps({
                "params": {"token": "updated-token"},
                "enabled": False
            }),
            content_type='application/json',
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "token is invalid/expired")
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_user_not_found(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "nonexistent@example.com"}
        mock_get_user.return_value = None
        
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = self.app.patch(
            f'/channels/{channel_id}',
            data=json.dumps({
                "params": {"token": "updated-token"},
                "enabled": False
            }),
            content_type='application/json',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "user nonexistent@example.com not found")
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_channel_by_id')
    @patch('api.main.update_channel')
    def test_delete_channel_success(self, mock_update_channel, mock_get_channel_by_id, 
                                 mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        mock_validate_uuid.return_value = True
        
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        mock_channel = MagicMock()
        mock_channel.id = channel_id
        mock_get_channel_by_id.return_value = mock_channel
        
        response = self.app.delete(
            f'/channels/{channel_id}',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data, {})
        
        mock_validate_uuid.assert_called_once_with(channel_id)
        mock_get_channel_by_id.assert_called_once_with(cfg.postgres, channel_id)
        mock_update_channel.assert_called_once_with(cfg.postgres, channel_id, None, False)
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    def test_delete_channel_invalid_id(self, mock_validate_uuid, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        mock_validate_uuid.return_value = False
        
        channel_id = "invalid-id"
        
        response = self.app.delete(
            f'/channels/{channel_id}',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "channel_id is invalid")
        
        mock_validate_uuid.assert_called_once_with(channel_id)
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_uuid')
    @patch('api.main.get_channel_by_id')
    def test_delete_channel_not_found(self, mock_get_channel_by_id, mock_validate_uuid, 
                                   mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        mock_validate_uuid.return_value = True
        
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        mock_get_channel_by_id.return_value = None
        
        response = self.app.delete(
            f'/channels/{channel_id}',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], f"channel {channel_id} not found")
        
        mock_validate_uuid.assert_called_once_with(channel_id)
        mock_get_channel_by_id.assert_called_once_with(cfg.postgres, channel_id)
    
    def test_unauthorized_access(self):
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = self.app.delete(f'/channels/{channel_id}')
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "token is missing")
    
    def test_invalid_token_format(self):
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = self.app.delete(
            f'/channels/{channel_id}',
            headers={"Authorization": "InvalidFormat"}
        )
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "invalid auth token")
    
    @patch('api.main.jwt.decode')
    def test_invalid_token(self, mock_jwt_decode):
        mock_jwt_decode.side_effect = Exception("Invalid token")
        
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = self.app.delete(
            f'/channels/{channel_id}',
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "token is invalid/expired")
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_user_not_found(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "nonexistent@example.com"}
        mock_get_user.return_value = None
        
        channel_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = self.app.delete(
            f'/channels/{channel_id}',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "user nonexistent@example.com not found")

if __name__ == 'main':
    unittest.main()
