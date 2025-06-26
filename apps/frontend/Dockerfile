# Use Node.js 18 alpine image
FROM node:18-alpine

# Accept build arguments for npm registry mirror
ARG NPM_REGISTRY=""

# Set environment variables
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1

# Set work directory
WORKDIR /app

# Install dependencies with configurable registry
RUN if [ -n "$NPM_REGISTRY" ]; then \
        npm install -g pnpm --registry=$NPM_REGISTRY; \
    else \
        npm install -g pnpm; \
    fi

# Copy package files
COPY package*.json ./
COPY pnpm-lock.yaml* ./

# Install dependencies with configurable registry
RUN if [ -n "$NPM_REGISTRY" ]; then \
        pnpm install --registry=$NPM_REGISTRY; \
    else \
        pnpm install; \
    fi

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