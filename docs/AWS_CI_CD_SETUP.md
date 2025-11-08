# AWS CI/CD Setup Guide

This guide explains how to set up automatic AWS deployment on pushes to the main branch using GitHub Actions.

## Overview

The CI/CD pipeline automatically:
1. Builds and pushes Docker images to ECR
2. Updates ECS services (API and Worker)
3. Builds and deploys the frontend to S3/CloudFront
4. Invalidates CloudFront cache

## Prerequisites

1. AWS infrastructure already deployed (using `auto_deploy.sh`)
2. GitHub repository with Actions enabled
3. AWS IAM user with deployment permissions

## Step 1: Create IAM User for CI/CD

Create an IAM user with the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:UpdateService",
        "ecs:DescribeServices",
        "ecs:DescribeTasks",
        "ecs:ListTasks"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:PutBucketPolicy"
      ],
      "Resource": [
        "arn:aws:s3:::tutor-scoring-frontend",
        "arn:aws:s3:::tutor-scoring-frontend/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateInvalidation",
        "cloudfront:ListDistributions",
        "cloudfront:GetDistribution"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:*:secret:tutor-scoring/*"
      ]
    }
  ]
}
```

Create an access key for this user and save the credentials.

## Step 2: Extract Configuration Values

Run the helper script to get all required secret values:

```bash
cd scripts/aws_deploy
./setup_github_secrets.sh
```

This will display all the values you need to add as GitHub Secrets.

## Step 3: Add GitHub Secrets

1. Go to your GitHub repository
2. Navigate to: **Settings → Secrets and variables → Actions**
3. Click **New repository secret** for each of the following:

### Required Secrets

| Secret Name | Description | Source |
|------------|-------------|--------|
| `AWS_ACCESS_KEY_ID` | IAM user access key | From Step 1 |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key | From Step 1 |
| `AWS_VPC_ID` | VPC ID | From `aws_config.env` |
| `AWS_PUB_SUBNET_1` | Public subnet 1 | From `aws_config.env` |
| `AWS_PUB_SUBNET_2` | Public subnet 2 | From `aws_config.env` |
| `AWS_PRIV_SUBNET_1` | Private subnet 1 | From `aws_config.env` |
| `AWS_PRIV_SUBNET_2` | Private subnet 2 | From `aws_config.env` |
| `AWS_ALB_SG` | ALB security group | From `aws_config.env` |
| `AWS_API_SG` | API security group | From `aws_config.env` |
| `AWS_WORKER_SG` | Worker security group | From `aws_config.env` |
| `AWS_DB_SG` | Database security group | From `aws_config.env` |
| `AWS_REDIS_SG` | Redis security group | From `aws_config.env` |
| `AWS_API_REPO_URI` | ECR API repository URI | From `aws_config.env` |
| `AWS_WORKER_REPO_URI` | ECR Worker repository URI | From `aws_config.env` |
| `AWS_EXEC_ROLE_ARN` | ECS task execution role ARN | From `aws_config.env` |
| `AWS_TASK_ROLE_ARN` | ECS task role ARN | From `aws_config.env` |
| `AWS_DB_ENDPOINT` | RDS endpoint | From `aws_config.env` |
| `AWS_REDIS_ENDPOINT` | ElastiCache endpoint | From `aws_config.env` |
| `AWS_DB_SECRET_ARN` | Database secret ARN | From `aws_config.env` |
| `AWS_REDIS_SECRET_ARN` | Redis secret ARN | From `aws_config.env` |
| `AWS_APP_SECRET_ARN` | App secrets ARN | From `aws_config.env` |
| `AWS_ALB_DNS` | ALB DNS name | From `aws_config.env` |
| `AWS_CLOUDFRONT_URL` | CloudFront URL | From `aws_config.env` |

## Step 4: Verify Workflow File

The workflow file is located at `.github/workflows/deploy-aws.yml`. It will automatically:
- Trigger on pushes to `main` branch
- Build and push Docker images
- Update ECS services
- Deploy frontend
- Invalidate CloudFront cache

## Step 5: Test the Deployment

1. Make a small change to your code
2. Commit and push to the `main` branch:
   ```bash
   git add .
   git commit -m "Test CI/CD deployment"
   git push origin main
   ```
3. Go to **Actions** tab in GitHub to watch the deployment
4. Check the workflow logs if there are any issues

## Manual Trigger

You can also manually trigger the deployment:
1. Go to **Actions** tab
2. Select **Deploy to AWS** workflow
3. Click **Run workflow**

## Troubleshooting

### Workflow fails with "Permission denied"
- Check that the IAM user has all required permissions
- Verify AWS credentials are correct in GitHub Secrets

### Docker build fails
- Check that Dockerfile paths are correct
- Verify ECR repositories exist

### ECS service update fails
- Verify cluster and service names match
- Check that task definitions are up to date

### Frontend deployment fails
- Check S3 bucket exists and has correct permissions
- Verify CloudFront distribution exists

### CloudFront invalidation fails
- Check distribution ID is correct
- Verify IAM user has CloudFront permissions

## Security Notes

- Never commit `aws_config.env` to the repository
- Rotate AWS credentials regularly
- Use least-privilege IAM policies
- Review GitHub Actions logs regularly for security issues

## Workflow Details

The workflow runs on Ubuntu and:
1. Checks out code
2. Configures AWS credentials
3. Sets up Docker Buildx for multi-platform builds
4. Sets up Node.js for frontend build
5. Creates `aws_config.env` from GitHub Secrets
6. Builds and pushes Docker images
7. Updates ECS services
8. Builds and deploys frontend
9. Invalidates CloudFront cache

Total deployment time: ~10-15 minutes (depending on build times and ECS service stabilization)

