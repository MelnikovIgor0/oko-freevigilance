import json
import unittest
from unittest.mock import patch, MagicMock

from flask import Flask
from api.main import app, get_user_by_email, cfg, jwt

class TestInfoEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
    @patch('api.main.get_user_by_email')
    @patch('api.main.jwt.decode')
    def test_info_success(self, mock_jwt_decode, mock_get_user):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_user.is_admin = False
        mock_get_user.return_value = mock_user
        
        response = self.app.get(
            '/users/info',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["user"]["id"], 1)
        self.assertEqual(data["user"]["username"], "testuser")
        self.assertEqual(data["user"]["email"], "test@example.com")
        self.assertIsNone(data["user"]["deleted_at"])
        self.assertFalse(data["user"]["is_admin"])
        
        mock_get_user.assert_called_once_with(cfg.postgres, "test@example.com")
    
    def test_info_missing_auth_header(self):
        response = self.app.get('/users/info')
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "token is missing")
    
    def test_info_empty_token(self):
        response = self.app.get(
            '/users/info',
            headers={"Authorization": "Bearer "}
        )
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "token is missing")
    
    def test_info_invalid_auth_format(self):
        response = self.app.get(
            '/users/info',
            headers={"Authorization": "InvalidFormat"}
        )
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "token is missing")
    
    @patch('api.main.jwt.decode')
    def test_info_invalid_token(self, mock_jwt_decode):
        mock_jwt_decode.side_effect = Exception("Invalid token")
        
        response = self.app.get(
            '/users/info',
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "token is invalid/expired")
    
    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_info_user_not_found(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "nonexistent@example.com"}
        mock_get_user.return_value = None
        
        response = self.app.get(
            '/users/info',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "user nonexistent@example.com not found")
        mock_get_user.assert_called_once_with(cfg.postgres, "nonexistent@example.com")
    
    @patch('api.main.jwt.decode')
    def test_info_expired_token(self, mock_jwt_decode):
        mock_jwt_decode.side_effect = jwt.ExpiredSignatureError("Token expired")
        
        response = self.app.get(
            '/users/info',
            headers={"Authorization": "Bearer expired_token"}
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "token is invalid/expired")
    
    @patch('api.main.jwt.decode')
    def test_info_invalid_signature(self, mock_jwt_decode):
        mock_jwt_decode.side_effect = jwt.InvalidSignatureError("Invalid signature")
        
        response = self.app.get(
            '/users/info',
            headers={"Authorization": "Bearer tampered_token"}
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "token is invalid/expired")

if __name__ == 'main':
    unittest.main()
