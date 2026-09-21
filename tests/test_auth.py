def test_register(client, app):
    # Test valid registration
    response = client.post(
        '/register',
        data={'username': 'testuser', 'email': 'test@test.com', 'password': 'password123', 'confirm_password': 'password123'}
    )
    assert response.status_code == 302 # Redirects to login
    assert response.headers['Location'] == '/login'
    
    # Verify in DB
    with app.app_context():
        from database.db import get_db
        user = get_db().execute("SELECT * FROM users WHERE username = 'testuser'").fetchone()
        assert user is not None
        assert user['email'] == 'test@test.com'

def test_login_logout(client):
    # Setup user
    client.post('/register', data={'username': 'testuser', 'email': 'test@test.com', 'password': 'password123', 'confirm_password': 'password123'})
    
    # Test login
    response = client.post(
        '/login',
        data={'username': 'testuser', 'password': 'password123'}
    )
    assert response.status_code == 302
    assert response.headers['Location'] == '/dashboard'
    
    # Test logout
    response = client.get('/logout')
    assert response.status_code == 302
    assert response.headers['Location'] == '/'

def test_protected_route_redirect(client):
    # Try accessing protected route without login
    response = client.get('/dashboard')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']
