// Session timeout handling
let timeout;
const timeoutDuration = 20 * 60 * 1000; // 20 minutes in milliseconds

// Function to reset the timeout
function resetTimeout() {
    clearTimeout(timeout);
    timeout = setTimeout(logout, timeoutDuration);
}

// Function to handle logout
function logout() {
    window.location.href = '/accounts/logout/';
}

// Add event listeners for user activity
document.addEventListener('mousemove', resetTimeout);
document.addEventListener('keypress', resetTimeout);
document.addEventListener('click', resetTimeout);
document.addEventListener('scroll', resetTimeout);

// Handle visibility change
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden (tab/window closed or minimized)
        clearTimeout(timeout);
    } else {
        // Page is visible again
        resetTimeout();
    }
});

// Handle beforeunload event
window.addEventListener('beforeunload', function() {
    // Clear the timeout when the page is about to unload
    clearTimeout(timeout);
});

// Initialize the timeout when the page loads
resetTimeout();