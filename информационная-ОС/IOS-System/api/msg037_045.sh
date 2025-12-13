# Install Redoc
npm install -g redoc-cli

# Generate static HTML docs
redoc-cli bundle docs/api/openapi.yaml -o docs/api/index.html

# Serve docs
redoc-cli serve docs/api/openapi.yaml

# Access at: http://localhost:8080