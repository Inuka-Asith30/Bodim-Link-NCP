import pytest
from unittest.mock import patch, MagicMock
from notifications import send_welcome_email

@patch('notifications.smtplib.SMTP_SSL')
@patch('notifications.render_template')
def test_send_welcome_email_success(mock_render_template, mock_smtp_ssl):
    """Test that the welcome email sends successfully."""
    # Setup mocks
    mock_render_template.return_value = "<html>Mock Email Content</html>"
    
    mock_server = MagicMock()
    mock_smtp_ssl.return_value = mock_server
    
    # Call the function
    result = send_welcome_email("test@example.com", "Test User")
    
    # Verify result
    assert result is True
    
    # Verify mock interactions
    mock_render_template.assert_called_once_with('emails/welcome_student.html', name='Test User')
    mock_smtp_ssl.assert_called_once_with('smtp.gmail.com', 465)
    mock_server.login.assert_called_once()
    mock_server.send_message.assert_called_once()
    mock_server.quit.assert_called_once()

@patch('notifications.smtplib.SMTP_SSL')
def test_send_welcome_email_failure(mock_smtp_ssl):
    """Test that the welcome email handles exceptions gracefully."""
    # Force an exception when connecting
    mock_smtp_ssl.side_effect = Exception("Connection Failed")
    
    # Call the function
    result = send_welcome_email("test@example.com", "Test User")
    
    # Verify it caught the exception and returned False
    assert result is False
