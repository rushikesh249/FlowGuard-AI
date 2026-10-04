#!/bin/bash

# Configuration
API_URL="http://localhost:8000"
EMAIL="admin@flowguard.com"
PASSWORD="securepassword123"
NEW_PASSWORD="newpassword456"
ROLE="Admin"

echo "====================================="
echo "Testing FlowGuard AI Authentication"
echo "====================================="
echo ""

# 1. Register
echo "1. Registering user ($EMAIL)..."
curl -s -X POST "$API_URL/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"email": "'"$EMAIL"'", "password": "'"$PASSWORD"'", "role": "'"$ROLE"'"}'
echo ""
echo ""

# 2. Login
echo "2. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=$EMAIL&password=$PASSWORD")
echo "$LOGIN_RESPONSE"
echo ""

# Extract token using inline python
TOKEN=$(python -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" <<< "$LOGIN_RESPONSE")

if [ -z "$TOKEN" ]; then
    echo "Failed to extract access token!"
    exit 1
fi

# 3. Get Current User
echo "3. Fetching current user details..."
curl -s -X GET "$API_URL/users/me" \
     -H "Authorization: Bearer $TOKEN"
echo ""
echo ""

# 4. Reset Password
echo "4. Resetting password..."
curl -s -X POST "$API_URL/auth/reset-password" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"current_password": "'"$PASSWORD"'", "new_password": "'"$NEW_PASSWORD"'"}'
echo ""
echo ""

# 5. Logout
echo "5. Logging out..."
curl -s -X POST "$API_URL/auth/logout" \
     -H "Authorization: Bearer $TOKEN"
echo ""
echo ""

# 6. Login with new password
echo "6. Logging in with NEW password..."
LOGIN_NEW_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=$EMAIL&password=$NEW_PASSWORD")
echo "$LOGIN_NEW_RESPONSE"
echo ""
echo ""

echo "Test Complete."
