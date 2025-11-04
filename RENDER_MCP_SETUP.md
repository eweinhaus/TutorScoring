# Render MCP Setup Guide

## Step 1: Get Your Render API Key

1. Go to https://dashboard.render.com
2. Click on your profile (top right)
3. Go to **Account Settings**
4. Click on **API Keys** in the left sidebar
5. Click **Create a new API key**
6. Give it a name (e.g., "MCP Server")
7. Copy the API key (you'll only see it once!)

## Step 2: Configure Cursor MCP

I've created a template configuration file at `.cursor/mcp.json`. 

**To complete the setup:**

1. Open `.cursor/mcp.json`
2. Replace `YOUR_RENDER_API_KEY_HERE` with your actual Render API key
3. Save the file
4. Restart Cursor

## Alternative: Using Cursor Settings

If Cursor doesn't read from `.cursor/mcp.json`, you can configure MCP through Cursor's settings:

1. Open Cursor Settings (Cmd+,)
2. Search for "MCP" or "Model Context Protocol"
3. Add a new MCP server:
   - **Name**: `render`
   - **Type**: `http`
   - **URL**: `https://mcp.render.com/mcp`
   - **Headers**: 
     ```json
     {
       "Authorization": "Bearer YOUR_RENDER_API_KEY_HERE"
     }
     ```
4. Save and restart Cursor

## Verification

After setup, you should be able to:
- Deploy services using Render MCP
- Manage your Render infrastructure
- Use natural language commands to interact with Render

## Security Note

⚠️ **Important**: Never commit your API key to git! The `.cursor/mcp.json` file should be in `.gitignore`.

## Next Steps

Once configured, you can deploy your application by saying:
- "Deploy to Render using the render.yaml blueprint"
- "Create services from render.yaml"
- "List my Render services"

