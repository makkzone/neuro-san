# Neuro-SAN Startup Scripts

This folder contains easy-to-use startup scripts for launching the Neuro-SAN server and client on different operating systems.

## Quick Start

### macOS / Linux

**Start the server:**
```bash
chmod +x startup/start-server.sh
./startup/start-server.sh
```

**Start the client (in another terminal):**
```bash
chmod +x startup/start-client.sh
./startup/start-client.sh
```

### Windows

**Start the server:**
```cmd
startup\start-server.bat
```

**Start the client (in another terminal):**
```cmd
startup\start-client.bat
```

## What These Scripts Do

### Server Scripts (`start-server.sh` / `start-server.bat`)

1. ✅ Check for virtual environment (create if missing)
2. ✅ Activate virtual environment
3. ✅ Set PYTHONPATH
4. ✅ Install dependencies (if not already installed)
5. ✅ Enable CORS headers (for web applications)
6. ✅ Check for API keys (warns if missing)
7. ✅ Start the Neuro-SAN server on port 8080

### Client Scripts (`start-client.sh` / `start-client.bat`)

1. ✅ Activate virtual environment
2. ✅ Set PYTHONPATH
3. ✅ Start the CLI client with specified agent

## Client Usage

### Direct Mode (No Server Required)
```bash
# macOS/Linux
./startup/start-client.sh hello_world

# Windows
startup\start-client.bat hello_world
```

### Server Mode (Connects to Running Server)
```bash
# macOS/Linux
./startup/start-client.sh hello_world --http

# Windows
startup\start-client.bat hello_world --http
```

## Available Agents

Based on the server logs, you can use any of these agents:
- `hello_world` - Simple greeting agent (default)
- `copy_cat` - Echo agent
- `math_guy` - Math operations
- `date_time` - Current date and time
- `music_nerd` - Music-related queries
- `gist` - Terse announcements
- And many more...

## Environment Variables

### Required
- `OPENAI_API_KEY` - Your OpenAI API key

### Optional
- `AGENT_HTTP_PORT` - Server port (default: 8080)
- `AGENT_SERVER_NAME` - Server name for health reporting
- Other provider API keys (AWS, Azure, Anthropic, etc.)

### Setting Environment Variables

**macOS/Linux:**
```bash
export OPENAI_API_KEY="your-key-here"
```

**Windows:**
```cmd
set OPENAI_API_KEY=your-key-here
```

## Troubleshooting

### Port Already in Use
If you see "Address already in use" error:
```bash
# macOS/Linux
lsof -i :8080
kill <PID>

# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

### Virtual Environment Issues
Delete the `.venv` or `venv` folder and run the script again to recreate it.

### Missing Dependencies
The scripts automatically install dependencies, but you can manually run:
```bash
pip install -r requirements.txt
```

## Server Endpoints

Once the server is running:
- **Server URL:** http://localhost:8080
- **Health Check:** http://localhost:8080/health
- **API endpoints:** See the OpenAPI spec for details

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.
