FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
# Use npm install to allow lockfile resolution when mismatched
RUN npm install --no-audit --no-fund
COPY . .
# Ensure production build uses provided env file
ARG REACT_APP_API_URL
ARG REACT_APP_API_KEY
ENV REACT_APP_API_URL=${REACT_APP_API_URL}
ENV REACT_APP_API_KEY=${REACT_APP_API_KEY}
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 8080
CMD ["nginx","-g","daemon off;"]
