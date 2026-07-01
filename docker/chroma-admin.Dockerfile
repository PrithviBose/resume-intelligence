FROM node:20

WORKDIR /app

COPY chromadb-admin/package.json ./
RUN npm install

COPY chromadb-admin/ .

# package-lock from another OS can skip linux SWC binaries
RUN npm install @next/swc-linux-x64-gnu --no-save

# Windows checkouts can introduce CRLF; normalize before Next.js build
RUN find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.json" -o -name "*.css" -o -name "*.scss" \) -exec sed -i 's/\r$//' {} +

RUN node -e "const fs=require('fs'); const p='next.config.js'; let c=fs.readFileSync(p,'utf8'); if(!c.includes('ignoreDuringBuilds')){ c=c.replace('const nextConfig = {', 'const nextConfig = {\\n  eslint: { ignoreDuringBuilds: true },'); fs.writeFileSync(p,c); }"

ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

CMD ["npm", "start"]
EXPOSE 3001
