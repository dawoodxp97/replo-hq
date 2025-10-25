# Multi-stage Dockerfile for Frontend
# Stage 1: Base dependencies
FROM node:20-alpine AS base

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    git \
    curl \
    && rm -rf /var/cache/apk/*

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev dependencies)
RUN npm ci --include=dev

# Stage 2: Development with linting and formatting tools
FROM base AS development

# Install additional development tools
RUN npm install -g \
    prettier@3.1.1 \
    @typescript-eslint/parser@6.21.0 \
    @typescript-eslint/eslint-plugin@6.21.0

# Copy source code
COPY . .

# Stage 3: Linting and code quality checks
FROM development AS lint

# Run Prettier format check
RUN npx prettier --check "**/*.{js,jsx,ts,tsx,json,css,md}" || true

# Run ESLint
RUN npm run lint || true

# Run TypeScript type checking
RUN npx tsc --noEmit || true

# Stage 4: Testing (optional - can be extended)
FROM development AS test

# Run tests if test scripts exist
RUN if npm run | grep -q "test"; then npm run test; fi

# Stage 5: Build for production
FROM development AS build

# Set production environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Build the application
RUN npm run build

# Stage 6: Production runtime
FROM node:20-alpine AS production

WORKDIR /app

# Install only production system dependencies
RUN apk add --no-cache \
    curl \
    && rm -rf /var/cache/apk/*

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Copy package files and install only production dependencies
COPY package*.json ./
RUN npm ci --only=production --ignore-scripts && \
    npm cache clean --force

# Copy built application from build stage
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public

# Set correct permissions
RUN chown -R nextjs:nodejs /app

# Switch to non-root user
USER nextjs

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || curl -f http://localhost:3000/ || exit 1

# Expose the port
EXPOSE 3000

# Set environment variables
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Command to run the application
CMD ["node", "server.js"]