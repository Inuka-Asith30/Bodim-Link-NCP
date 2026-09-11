import pytest
from unittest.mock import patch, MagicMock

def test_index_route(client):
    """Test that the index page loads correctly."""
    response = client.get('/')
    assert response.status_code == 200

def test_logout_route(client):
    """Test that the logout route clears session and redirects."""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Test User'

    response = client.get('/logout')
    
    # Should redirect to index
    assert response.status_code == 302
    assert response.headers['Location'] == '/'
    
    # Verify session is cleared
    with client.session_transaction() as sess:
        assert 'user_id' not in sess

@patch('app.get_db_connection')
def test_login_invalid_credentials(mock_get_db_connection, client):
    """Test login with invalid credentials."""
    # Mock the database connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    
    # Setup mock chain
    mock_get_db_connection.return_value = mock_connection
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    
    # Return no user found
    mock_cursor.fetchone.return_value = None
    
    response = client.post('/login', data={
        'email': 'wrong@example.com',
        'password': 'wrongpassword'
    })
    
    # In a real app this might redirect or re-render login with an error
    # Our app renders login.html (status code 200) with a flash message
    assert response.status_code == 200
    
    # The view should have called fetchone
    mock_cursor.execute.assert_called_once()
