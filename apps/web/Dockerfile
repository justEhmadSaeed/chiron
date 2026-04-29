FROM node:20-alpine

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@9.15.9 --activate

# Copy root configuration and lockfiles
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml turbo.json ./
COPY apps/web/package.json ./apps/web/

# Install dependencies
RUN pnpm install

# Copy source code
COPY . .

WORKDIR /app/apps/web

EXPOSE 3000

# Start Vite dev server on port 3000
CMD ["pnpm", "run", "dev", "--host", "0.0.0.0", "--port", "3000"]
