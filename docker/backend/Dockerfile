FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./
COPY esbuild.config.mjs ./

# Install dependencies
RUN npm install

# Copy source code
COPY src/ ./src/

# Build the plugin
RUN npm run build

# Python backend
FROM python:3.11-slim

WORKDIR /app

# Copy Python requirements
COPY requirements.txt .
COPY app.py .
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy built plugin from builder stage
COPY --from=builder /app/main.js ./main.js

# Copy other necessary files
COPY .env.example .env

# Expose ports
EXPOSE 5000

# Start the application
CMD ["python", "app.py"] 