// Admin Token Setup Script
// Run this in your browser console to set the authentication token

console.log('🔧 Setting up admin authentication token...');

// Your JWT token
const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtaWNoYWVsYXJpY2hhcmQiLCJ1c2VyX2lkIjoxLCJleHAiOjE3NTk2MjI5NDh9.hHkX4AiC-sJMWlHRURQw43ky_fOloV_dgHILvysST-E';

// Set token in all possible localStorage keys
localStorage.setItem('token', token);
localStorage.setItem('auth_token', token);
localStorage.setItem('access_token', token);
localStorage.setItem('jwt_token', token);

console.log('✅ Token set in localStorage under multiple keys');
console.log('📋 Available localStorage keys:', Object.keys(localStorage));

// Verify the token works
fetch('/api/auth/me', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
})
.then(response => response.json())
.then(user => {
    console.log('✅ Token verification successful!');
    console.log('👤 User:', user.username);
    console.log('🔑 Admin:', user.is_admin);
    console.log('🎯 You can now access the admin page!');
})
.catch(error => {
    console.error('❌ Token verification failed:', error);
});

console.log('🚀 Setup complete! Try accessing /admin now.');
