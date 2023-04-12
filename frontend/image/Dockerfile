FROM node:18

WORKDIR /frontend

ADD ./frontend/package.json .
ADD ./frontend/public ./public
ADD ./frontend/src ./src
RUN npm install
RUN npm install -g react-scripts@5.0.1

EXPOSE 3000