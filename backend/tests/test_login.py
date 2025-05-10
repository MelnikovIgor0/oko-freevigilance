import json
import unittest
import datetime
from unittest.mock import patch, MagicMock

import jwt
from flask import Flask
from api.main import app, get_user_by_email, get_md5, cfg

class TestLoginEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_md5')
    @patch('api.main.jwt.encode')
    def test_login_success(self, mock_jwt_encode, mock_get_md5, mock_get_user):
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.password = "hashed_password"
        mock_user.deleted_at = None
        mock_user.is_admin = False
        mock_get_user.return_value = mock_user
        
        mock_get_md5.return_value = "hashed_password"
        mock_jwt_encode.return_value = "test_token"
        
        response = self.app.post(
            '/users/login',
            data=json.dumps({
                "email": "test@example.com",
                "password": "password123"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["accessToken"], "test_token")
        self.assertEqual(data["user"]["id"], 1)
        self.assertEqual(data["user"]["username"], "testuser")
        self.assertEqual(data["user"]["email"], "test@example.com")
        self.assertIsNone(data["user"]["deleted_at"])
        
        mock_get_user.assert_called_once_with(cfg.postgres, "test@example.com")
        mock_get_md5.assert_called_once_with("password123")
        
        mock_jwt_encode.assert_called_once()
        args, kwargs = mock_jwt_encode.call_args
        payload = args[0]
        self.assertEqual(payload["user"], "test@example.com")
        self.assertTrue("exp" in payload)
    
    def test_login_missing_email(self):
        response = self.app.post(
            '/users/login',
            data=json.dumps({
                "password": "password123"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "Invalid credentials 1")
    
    def test_login_missing_password(self):
        response = self.app.post(
            '/users/login',
            data=json.dumps({
                "email": "test@example.com"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "Invalid credentials 1")
    
    def test_login_missing_both_fields(self):
        response = self.app.post(
            '/users/login',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "Invalid credentials 1")
    
    @patch('api.main.get_user_by_email')
    def test_login_user_not_found(self, mock_get_user):
        mock_get_user.return_value = None
        
        response = self.app.post(
            '/users/login',
            data=json.dumps({
                "email": "nonexistent@example.com",
                "password": "password123"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "Invalid credentials 2")
        mock_get_user.assert_called_once_with(cfg.postgres, "nonexistent@example.com")
    
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_md5')
    def test_login_incorrect_password(self, mock_get_md5, mock_get_user):
        mock_user = MagicMock()
        mock_user.password = "correct_hash"
        mock_user.deleted_at = None
        mock_user.is_admin = False
        mock_get_user.return_value = mock_user
        
        mock_get_md5.return_value = "incorrect_hash"
        
        
        response = self.app.post(
            '/users/login',
            data=json.dumps({
                "email": "test@example.com",
                "password": "wrong_password"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "Invalid credentials 2")
        mock_get_user.assert_called_once_with(cfg.postgres, "test@example.com")
        mock_get_md5.assert_called_once_with("wrong_password")
    
    @patch('api.main.get_user_by_email')
    @patch('api.main.get_md5')
    @patch('api.main.jwt.encode')
    @patch('api.main.datetime')
    def test_login_jwt_token_expiration(self, mock_datetime, mock_jwt_encode, mock_get_md5, mock_get_user):
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.password = "hashed_password"
        mock_user.deleted_at = None
        mock_user.is_admin = False
        mock_get_user.return_value = mock_user
        
        mock_get_md5.return_value = "hashed_password"
        mock_jwt_encode.return_value = "test_token"
        
        now = datetime.datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.datetime.utcnow.return_value = now
        mock_datetime.timedelta = datetime.timedelta
        
        response = self.app.post(
            '/users/login',
            data=json.dumps({
                "email": "test@example.com",
                "password": "password123"
            }),
            content_type='application/json'
        )
        
        mock_jwt_encode.assert_called_once()
        args, kwargs = mock_jwt_encode.call_args
        payload = args[0]
        expected_exp = now + datetime.timedelta(minutes=1440)
        self.assertEqual(payload["exp"], expected_exp)

if __name__ == 'main':
    unittest.main()
