# Build stage
FROM node:18-alpine as build

# Set working directory
WORKDIR /app

# Copy package.json and yarn.lock
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy all files
COPY . .

# Set environment variables for build
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Create the build
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy build files from the build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Create a startup script to inject environment variables at runtime
RUN echo "#!/bin/sh" > /docker-entrypoint.d/40-generate-env-config.sh && \
    echo "envsubst '\$REACT_APP_API_URL' < /usr/share/nginx/html/env-config.template.js > /usr/share/nginx/html/env-config.js" >> /docker-entrypoint.d/40-generate-env-config.sh && \
    chmod +x /docker-entrypoint.d/40-generate-env-config.sh

# Start nginx
CMD ["nginx", "-g", "daemon off;"] 