# Use Node.js LTS version
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install dependencies first
COPY package*.json ./

# Install dependencies and build tools
RUN npm install
RUN npm install --save-dev @remix-run/serve @remix-run/dev

# Copy the rest of the application
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Set environment variables
ENV NODE_ENV=development
ENV PORT=3000

# Start the development server
CMD ["npm", "run", "dev"]