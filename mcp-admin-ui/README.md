# MCP Admin UI UI: Built with React & Tailwind

## Installation

### Prerequisites

To get started, ensure you have the following prerequisites installed and set up:

- Node.js 18.x or later (recommended to use Node.js 20.x or later)

### Running

1. Install dependencies:

   ```bash
   npm install
   ```

   > Use the `--legacy-peer-deps` flag, if you face issues while installing.

2. **Create an environment file:**

   In the project root, create a file named `.env` and add the following line:

   ```bash
   VITE_API_BASE_URL=https://mcp-gw1.jesterbot.com
   ```

   > This sets the base URL for your API server.
   > You can update this value depending on your environment (e.g., dev, staging, or production).

3. Start the development server:

   ```bash
   npm run dev
   ```

## Deployment

### Code Repository

The MCP Admin UI UI source code is hosted at:

👉 [https://github.com/amartyashubham2005/screener2019-mcp-admin-ui.git](https://github.com/amartyashubham2005/screener2019-mcp-admin-ui.git)

The directory on the production VM (`~/workspace/screener2019-mcp-admin-ui`) is a **Git clone** of this repository.
This means you can update the production codebase with:

```bash
git pull origin main
```

### Current Production Deployment

The MCP Admin UI UI is currently deployed on **Azure**, running on a VM with the following setup:

* VM IP: `20.54.255.24`
* Host user: `ankit`
* Project directory: `~/workspace/screener2019-mcp-admin-ui` (git repo clone)
* Reverse proxy: **Nginx** configured to serve `jesterbot.com`

### Accessing the Server

1. Login to Azure:

   ```bash
   az login
   ```

2. Connect to the VM via SSH:

   ```bash
   az ssh vm --ip 20.54.255.24
   ```

3. Switch to the correct user and navigate to the project directory:

   ```bash
   sudo su - ankit
   cd ~/workspace/screener2019-mcp-admin-ui
   ```

### Updating & Building for Production

1. Pull the latest code from GitHub:

   ```bash
   git pull origin main
   ```

2. Build the production-ready assets:

   ```bash
   npm run build
   ```

This will generate optimized assets inside the `dist/` (or `build/`, depending on your config) directory, which Nginx will serve.

### Nginx Configuration

The application is served using **Nginx** as a reverse proxy.
The configuration file can be found at:

```
/etc/nginx/sites-available/default
```

Relevant configuration for `app.jesterbot.com`:

```
root /home/ankit/workspace/screener2019-mcp-admin-ui/dist;

index index.html index.htm index.nginx-debian.html;
server_name app.jesterbot.com; # managed by Certbot

location / {
    try_files $uri $uri/ /index.html;
}
```

### Notes

* **No Nginx restart required:**
  After running `npm run build`, there is no need to restart Nginx.
  The new static files will automatically be served from the `dist/` folder.

* **Domain:** The UI is accessible at [https://app.jesterbot.com](https://app.jesterbot.com).

## Summary of Commands

```bash
# On local (build for production)
npm run build

# On Azure VM
az login
az ssh vm --ip 20.54.255.24
sudo su - ankit
cd ~/workspace/screener2019-mcp-admin-ui

# Update code
git pull origin main

# Rebuild production assets
npm run build
```
