import json
import unittest
from unittest.mock import patch, MagicMock

from flask import Flask
from api.main import app, validate_username, validate_email, validate_password, get_user_by_username, create_user

class TestRegisterEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
    @patch('api.main.validate_username')
    @patch('api.main.validate_email')
    @patch('api.main.validate_password')
    @patch('api.main.get_user_by_username')
    @patch('api.main.create_user')
    def test_register_success(self, mock_create_user, mock_get_user, mock_validate_password, 
                              mock_validate_email, mock_validate_username):
        mock_validate_username.return_value = True
        mock_validate_email.return_value = True
        mock_validate_password.return_value = True
        mock_get_user.return_value = None
        
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_create_user.return_value = mock_user
        
        response = self.app.post(
            '/users/register',
            data=json.dumps({
                "username": "testuser",
                "email": "test@example.com",
                "password": "Password123!"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["user"]["id"], 1)
        self.assertEqual(data["user"]["username"], "testuser")
        self.assertEqual(data["user"]["email"], "test@example.com")
        
        mock_validate_username.assert_called_once_with("testuser")
        mock_validate_email.assert_called_once_with("test@example.com")
        mock_validate_password.assert_called_once_with("Password123!")
        mock_get_user.assert_called_once()
        mock_create_user.assert_called_once()
    
    def test_register_missing_username(self):
        response = self.app.post(
            '/users/register',
            data=json.dumps({
                "email": "test@example.com",
                "password": "Password123!"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "username is missing")
    
    def test_register_missing_email(self):
        response = self.app.post(
            '/users/register',
            data=json.dumps({
                "username": "testuser",
                "password": "Password123!"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "email is missing")
    
    def test_register_missing_password(self):
        response = self.app.post(
            '/users/register',
            data=json.dumps({
                "username": "testuser",
                "email": "test@example.com"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "password is missing")
    
    @patch('api.main.validate_username')
    def test_register_invalid_username(self, mock_validate_username):
        mock_validate_username.return_value = False
        
        response = self.app.post(
            '/users/register',
            data=json.dumps({
                "username": "invalid!user",
                "email": "test@example.com",
                "password": "Password123!"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "username is invalid")
        mock_validate_username.assert_called_once_with("invalid!user")
    
    @patch('api.main.validate_username')
    @patch('api.main.validate_email')
    def test_register_invalid_email(self, mock_validate_email, mock_validate_username):
        mock_validate_username.return_value = True
        mock_validate_email.return_value = False
        
        response = self.app.post(
            '/users/register',
            data=json.dumps({
                "username": "testuser",
                "email": "invalid_email",
                "password": "Password123!"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "email is invalid")
        mock_validate_email.assert_called_once_with("invalid_email")
    
    @patch('api.main.validate_username')
    @patch('api.main.validate_email')
    @patch('api.main.validate_password')
    def test_register_invalid_password(self, mock_validate_password, 
                                     mock_validate_email, mock_validate_username):
        mock_validate_username.return_value = True
        mock_validate_email.return_value = True
        mock_validate_password.return_value = False
        
        response = self.app.post(
            '/users/register',
            data=json.dumps({
                "username": "testuser",
                "email": "test@example.com",
                "password": "weak"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "password is invalid")
        mock_validate_password.assert_called_once_with("weak")
    
    @patch('api.main.validate_username')
    @patch('api.main.validate_email')
    @patch('api.main.validate_password')
    @patch('api.main.get_user_by_username')
    def test_register_user_already_exists(self, mock_get_user, mock_validate_password, 
                                       mock_validate_email, mock_validate_username):
        mock_validate_username.return_value = True
        mock_validate_email.return_value = True
        mock_validate_password.return_value = True
        mock_get_user.return_value = MagicMock()
        
        response = self.app.post(
            '/users/register',
            data=json.dumps({
                "username": "existing_user",
                "email": "test@example.com",
                "password": "Password123!"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "user already exists")
        mock_get_user.assert_called_once()

if __name__ == '__main__':
    unittest.main()
