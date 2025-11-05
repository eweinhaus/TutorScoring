# Quick Start - AWS Deployment

## Step 1: Get AWS Credentials

Run this for detailed instructions:
```bash
./get_aws_credentials.sh
```

Or run interactive setup:
```bash
./setup_aws_credentials.sh
```

**Quick Steps:**
1. Go to: https://console.aws.amazon.com/iam/home#/security_credentials
2. Sign in with: etweinhaus@gmail.com
3. Click "Create access key"
4. Copy Access Key ID and Secret Access Key
5. Run: `./setup_aws_credentials.sh` and paste them

## Step 2: Start Docker

If Docker Desktop is installed:
```bash
open -a Docker
```

Wait for Docker to start (check system tray for Docker icon).

## Step 3: Deploy

```bash
export PATH="/opt/homebrew/bin:$PATH"
./auto_deploy.sh
```

That's it! The script will handle everything else.
