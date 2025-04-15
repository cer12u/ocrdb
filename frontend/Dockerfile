FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the application
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 80

# Install a simple HTTP server to serve the static content
RUN npm install -g http-server

# Command to run the application
CMD ["http-server", "dist", "-p", "80"]
