// Session timeout handling
let timeout;
const timeoutDuration = 10 * 60 * 1000; // 10 minutes in milliseconds

// Function to reset the timeout
function resetTimeout() {
    clearTimeout(timeout);
    timeout = setTimeout(logout, timeoutDuration);
}

// Function to handle logout
async function logout() {
    try {
        console.log("Attempting to reset IP before logout...");

        // Reset last IP address before logging out
        const response = await fetch('/accounts/reset-last-ip/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            console.error('Failed to reset last IP address:', response.statusText);
        } else {
            console.log("IP reset successful.");
        }
    } catch (error) {
        console.error('Error resetting last IP address:', error);
    } finally {
        console.log("Proceeding to logout...");
        window.location.href = '/accounts/logout/';
    }
}


// Function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
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

// Handle beforeunload event (browser close/refresh)
// ✅ Fix: Use sendBeacon() for tab close / refresh
window.addEventListener('beforeunload', function () {
    clearTimeout(timeout);
    navigator.sendBeacon('/accounts/reset-last-ip/');
});

// Initialize the timeout when the page loads
resetTimeout();