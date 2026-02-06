FROM node:20-alpine

WORKDIR /app

# Install bun
RUN npm install -g bun

# Copy package files
COPY package.json bun.lockb* ./

# Install dependencies
RUN bun install

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start dev server
CMD ["bun", "run", "dev"]
