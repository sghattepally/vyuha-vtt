# ui/Dockerfile

# 1. Start with a Node.js base image. Alpine is a good lightweight choice.
FROM node:22-alpine

# 2. Set the working directory inside the container.
WORKDIR /app

# 3. Copy package.json and install dependencies first for better caching.
COPY package*.json ./
RUN npm install

# 4. Copy the rest of your UI source code into the container.
COPY . .

# 5. The command to run when the container starts.
# We run the 'dev' script from your package.json.
CMD ["npm", "run", "dev"]