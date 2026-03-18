This frontend is a very small static demo. To use it:

1. Start the backend (see project README).
2. Serve the frontend folder or open `frontend/index.html` in the browser.

The demo expects the backend to be served at the same origin (http://localhost:5000). If the backend runs on a different origin, update `fetch('/predict'...)` to point to the correct URL.