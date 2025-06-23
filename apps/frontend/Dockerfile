# Use Node.js 18 alpine image
FROM node:18-alpine

# Set environment variables
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1

# Set work directory
WORKDIR /app

# Install dependencies
RUN npm install -g pnpm

# Copy package files
COPY package*.json ./
COPY pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install

# Copy application code (excluding node_modules)
COPY app ./app
COPY next.config.js ./
COPY postcss.config.js ./
COPY tailwind.config.js ./
COPY tsconfig.json ./
COPY next-env.d.ts ./

# Expose port
EXPOSE 3000

# Start the development server
CMD ["pnpm", "dev"] 