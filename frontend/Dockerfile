# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Relative on purpose. The bundle runs in the user's browser, not in the
# cluster, so cluster DNS ("backend:8000") and localhost are both meaningless
# to it. A relative path resolves against whichever origin served the page, so
# the Ingress routing /api to the backend is all that is needed -- and the same
# image works on localhost, staging and production without a rebuild.
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# ── Stage 2: Final (Nginx) ────────────────────────────────────────────────────
FROM nginx:1.27-alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/app.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]