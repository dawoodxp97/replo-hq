# Static SPA build served by nginx with SPA fallback routing.
FROM node:22-alpine AS build
WORKDIR /app
COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY apps/web/package.json apps/web/
COPY packages/api-client/package.json packages/api-client/
COPY packages/ui/package.json packages/ui/
RUN corepack enable && pnpm install --filter @replo/web... --frozen-lockfile
COPY packages/api-client packages/api-client
COPY packages/ui packages/ui
COPY apps/web apps/web
RUN pnpm --filter @replo/web build

FROM nginx:1.27-alpine
COPY --from=build /app/apps/web/dist /usr/share/nginx/html
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
