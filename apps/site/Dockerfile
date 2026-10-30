# Next standalone output (see next.config.mjs) — run the server bundle directly.
FROM node:22-alpine AS build
WORKDIR /app
COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY apps/site/package.json apps/site/
COPY packages/api-client/package.json packages/api-client/
COPY packages/ui/package.json packages/ui/
RUN corepack enable && pnpm install --filter @replo/site... --frozen-lockfile
COPY packages/api-client packages/api-client
COPY packages/ui packages/ui
COPY apps/site apps/site
RUN pnpm --filter @replo/site build

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production PORT=3100
COPY --from=build /app/apps/site/.next/standalone ./
COPY --from=build /app/apps/site/.next/static ./apps/site/.next/static
COPY --from=build /app/apps/site/public ./apps/site/public
EXPOSE 3100
CMD ["node", "apps/site/server.js"]
