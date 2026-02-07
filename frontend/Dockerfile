# Frontend Dockerfile for DeckDex MTG
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Expose port
EXPOSE 5173

# Run dev server (for development)
# For production, use: RUN npm run build && CMD ["npm", "run", "preview"]
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
