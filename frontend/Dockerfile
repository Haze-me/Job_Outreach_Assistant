# ── Stage 1: Builder ──────────────────────────────────────────────────────────
# Node 22 rather than 20: Vite 8 requires ^20.19.0 || >=22.12.0, and Node 20
# reached end-of-life in April 2026. This stage does not ship — the final image
# is nginx — so it only affects build time.
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files first for layer caching
COPY package.json package-lock.json ./
RUN npm ci

# Copy all source files
COPY . .

# Build the Vite/React app — outputs to /app/dist by default
# VITE_ prefixed env vars are embedded at build time.
# We pass the API Gateway URL as a build arg so the built JS knows where to call.
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# ── Stage 2: Final (Nginx) ────────────────────────────────────────────────────
FROM nginx:1.27-alpine

# Remove default Nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom Nginx config
COPY nginx.conf /etc/nginx/conf.d/app.conf

# Copy built static files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
