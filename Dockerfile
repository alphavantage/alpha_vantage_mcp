FROM --platform=linux/amd64 nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
