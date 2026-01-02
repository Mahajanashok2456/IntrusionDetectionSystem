#!/bin/sh

# Replace the placeholder in env-config.js with the actual environment variable value
sed -i "s|__REACT_APP_API_URL__|${REACT_APP_API_URL}|g" /usr/share/nginx/html/env-config.js

# Start Nginx
exec nginx -g "daemon off;"
