# syntax=docker/dockerfile:1
#
# Frontend image. Build context is ./frontend
#
#   docker build -t haze21/joa-frontend:latest ./frontend
#
# The result is nginx serving a static bundle. It does not proxy /api -- the
# Ingress routes /api to the backend Service, so the browser sees one origin
# and the image stays free of any environment-specific backend address.

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
FROM node:22-alpine AS build

WORKDIR /app

# npm ci needs both files and installs exactly the lockfile, which is what
# makes a CI build reproducible.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vite inlines VITE_* variables at build time -- they cannot be changed later
# by the container's environment. "/api" is correct behind the Ingress; override
# only if the API lives on a different origin.
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# ---------------------------------------------------------------------------
# Serve
# ---------------------------------------------------------------------------
FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

# The stock nginx image already runs workers as the `nginx` user; port 80 is
# fine because the container is not privileged.
EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD wget -qO- http://127.0.0.1/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
