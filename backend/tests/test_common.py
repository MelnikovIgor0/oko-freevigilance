import json
import base64
from unittest import TestCase
from unittest.mock import patch, MagicMock

from api.main import app, cfg

class TestGetScreenshot(TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.valid_token = "valid_jwt_token"
        
        self.valid_url = "https://example.com"
        self.invalid_url = "not_a_valid_url"
        
        self.base64_image = base64.b64encode(b"test_image_data").decode('utf-8')

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_url')
    @patch('api.main.get_url_image_base_64')
    def test_get_screenshot_success(self, mock_get_url_image, mock_validate_url, 
                                mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_url.return_value = True
        mock_get_url_image.return_value = self.base64_image
        
        payload = {
            "url": self.valid_url
        }
        
        response = self.app.post(
            '/screenshot',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        mock_validate_url.assert_called_once_with(self.valid_url)
        mock_get_url_image.assert_called_once_with(self.valid_url)
        
        self.assertIn('screenshot', response_data)
        self.assertEqual(response_data['screenshot'], self.base64_image)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_get_screenshot_missing_url(self, mock_get_user, mock_jwt_decode):
        # Настройка моков
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        
        payload = {}
        
        response = self.app.post(
            '/screenshot',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], "url is required")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_url')
    def test_get_screenshot_invalid_url(self, mock_validate_url, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_url.return_value = False
        
        payload = {
            "url": self.invalid_url
        }
        
        response = self.app.post(
            '/screenshot',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data.decode())
        self.assertEqual(response_data["error"], "invalid url")
        
        mock_validate_url.assert_called_once_with(self.invalid_url)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_url')
    @patch('api.main.get_url_image_base_64')
    def test_get_screenshot_with_real_urls(self, mock_get_url_image, mock_validate_url, 
                                       mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_url.return_value = True
        mock_get_url_image.return_value = self.base64_image
        
        test_urls = [
            "https://www.google.com",
            "https://github.com",
            "https://python.org",
            "https://example.com/path/to/page?param=value"
        ]
        
        for url in test_urls:
            mock_validate_url.reset_mock()
            mock_get_url_image.reset_mock()
            
            payload = {"url": url}
            
            response = self.app.post(
                '/screenshot',
                data=json.dumps(payload),
                content_type='application/json',
                headers={'Authorization': f'bearer: {self.valid_token}'}
            )
            
            self.assertEqual(response.status_code, 200, f"Failed for URL: {url}")
            response_data = json.loads(response.data.decode())
            
            mock_validate_url.assert_called_once_with(url)
            mock_get_url_image.assert_called_once_with(url)
            
            self.assertIn('screenshot', response_data)
            self.assertEqual(response_data['screenshot'], self.base64_image)

    def test_get_screenshot_unauthorized(self):
        payload = {
            "url": self.valid_url
        }
        
        response = self.app.post(
            '/screenshot',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_get_screenshot_deleted_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = "2023-01-01 12:00:00"
        mock_get_user.return_value = mock_user
        
        payload = {
            "url": self.valid_url
        }
        
        response = self.app.post(
            '/screenshot',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 403)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    def test_get_screenshot_nonexistent_user(self, mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "nonexistent@example.com"}
        mock_get_user.return_value = None
        
        payload = {
            "url": self.valid_url
        }
        
        response = self.app.post(
            '/screenshot',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data.decode())
        self.assertIn('error', response_data)

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_url')
    @patch('api.main.get_url_image_base_64')
    def test_get_screenshot_empty_response(self, mock_get_url_image, mock_validate_url, 
                                      mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_url.return_value = True
        
        mock_get_url_image.return_value = ""
        
        payload = {
            "url": self.valid_url
        }
        
        response = self.app.post(
            '/screenshot',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        self.assertIn('screenshot', response_data)
        self.assertEqual(response_data['screenshot'], "")

    @patch('api.main.jwt.decode')
    @patch('api.main.get_user_by_email')
    @patch('api.main.validate_url')
    @patch('api.main.get_url_image_base_64')
    def test_get_screenshot_large_image(self, mock_get_url_image, mock_validate_url, 
                                   mock_get_user, mock_jwt_decode):
        mock_jwt_decode.return_value = {"user": "test@example.com"}
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.deleted_at = None
        mock_get_user.return_value = mock_user
        mock_validate_url.return_value = True
        
        large_image_data = b"X" * 1024 * 1024
        large_base64_image = base64.b64encode(large_image_data).decode('utf-8')
        mock_get_url_image.return_value = large_base64_image
        
        payload = {
            "url": self.valid_url
        }
        
        response = self.app.post(
            '/screenshot',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'Authorization': f'bearer: {self.valid_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data.decode())
        
        self.assertIn('screenshot', response_data)
        self.assertEqual(response_data['screenshot'], large_base64_image)
