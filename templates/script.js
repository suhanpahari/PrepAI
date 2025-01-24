document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.querySelector('.login form');
    const signupForm = document.querySelector('.signup form');
    const dashboard = document.querySelector('.dashboard');

    loginForm.addEventListener('submit', function(event) {
        event.preventDefault();
        // Perform login validation here
        dashboard.style.display = 'block';
    });

    signupForm.addEventListener('submit', function(event) {
        event.preventDefault();
        // Perform signup validation here
        dashboard.style.display = 'block';
    });
});