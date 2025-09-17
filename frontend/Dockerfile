FROM node:alpine

WORKDIR /usr/src/app

RUN npm install -g live-server
RUN npm install -g sass

COPY . .

EXPOSE 8080

CMD sh -c "sass --watch static:static & live-server --host=0.0.0.0 --port=8080 --no-browser"
