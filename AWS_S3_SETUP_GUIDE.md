# AWS S3 Setup Guide for Production Video Storage

This guide walks you through setting up AWS S3 for storing course videos and user-uploaded files in production.

## Overview

- **Development**: Files stored locally in `backend/media/`
- **Production**: Files stored in AWS S3 with CloudFront CDN
- **Cost**: ~$0.23/month for 10GB (within AWS Free Tier for first 12 months)

---

## Step 1: Create AWS Account

1. Go to [AWS Console](https://console.aws.amazon.com/)
2. Sign up for a new account (requires credit card but won't charge within free tier limits)
3. Complete identity verification

---

## Step 2: Create S3 Bucket

### 2.1 Navigate to S3
1. In AWS Console, search for "S3" and open the service
2. Click **"Create bucket"**

### 2.2 Configure Bucket
1. **Bucket name**: Choose a unique name (e.g., `oxidane-media-production`)
   - Must be globally unique
   - Use lowercase, numbers, and hyphens only
   
2. **AWS Region**: Choose closest to your users (e.g., `us-east-1`)

3. **Object Ownership**: Select **"ACLs disabled (recommended)"**

4. **Block Public Access**:
   - ✅ **Keep all "Block public access" settings ON**
   - We'll use signed URLs for private access
   
5. **Bucket Versioning**: Enable (optional but recommended for backup)

6. **Encryption**: 
   - Enable **Server-side encryption (SSE-S3)**
   - Leave as default (Amazon S3 managed keys)

7. Click **"Create bucket"**

---

## Step 3: Create IAM User for Django

### 3.1 Navigate to IAM
1. Search for "IAM" in AWS Console
2. Click **"Users"** → **"Create user"**

### 3.2 Configure User
1. **User name**: `oxidane-django-app`
2. **Access type**: Select **"Access key - Programmatic access"**
3. Click **"Next"**

### 3.3 Set Permissions
1. Select **"Attach policies directly"**
2. Search for and select: **"AmazonS3FullAccess"**
   - ⚠️ For production, use custom policy below instead
3. Click **"Next"** → **"Create user"**

### 3.4 Save Credentials
⚠️ **IMPORTANT**: Copy these immediately (shown only once)
- **Access key ID**: `AKIA...`
- **Secret access key**: `wJalr...`

Store these securely - you'll need them for your `.env` file.

---

## Step 4: Create Custom IAM Policy (Recommended)

Instead of `AmazonS3FullAccess`, use this minimal policy:

### 4.1 Create Policy
1. Go to IAM → Policies → Create policy
2. Click **JSON** tab
3. Paste this policy (replace `your-bucket-name`):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name/*",
                "arn:aws:s3:::your-bucket-name"
            ]
        }
    ]
}
```

4. Click **"Next"**
5. **Policy name**: `OxidaneS3Access`
6. Click **"Create policy"**

### 4.2 Attach to User
1. Go to IAM → Users → `oxidane-django-app`
2. Click **Permissions** tab
3. Remove `AmazonS3FullAccess` if attached
4. Click **"Add permissions"** → **"Attach policies directly"**
5. Search for `OxidaneS3Access` and select it
6. Click **"Add permissions"**

---

## Step 5: Configure CORS for S3 Bucket

### 5.1 Add CORS Policy
1. Go to S3 → Your bucket
2. Click **"Permissions"** tab
3. Scroll to **"Cross-origin resource sharing (CORS)"**
4. Click **"Edit"**
5. Paste this configuration:

```json
[
    {
        "AllowedHeaders": [
            "*"
        ],
        "AllowedMethods": [
            "GET",
            "PUT",
            "POST",
            "DELETE",
            "HEAD"
        ],
        "AllowedOrigins": [
            "http://localhost:3000",
            "https://yourdomain.com"
        ],
        "ExposeHeaders": [
            "ETag"
        ],
        "MaxAgeSeconds": 3600
    }
]
```

6. Replace `https://yourdomain.com` with your actual frontend domain
7. Click **"Save changes"**

---

## Step 6: Set Up CloudFront CDN (Optional but Recommended)

CloudFront provides fast global content delivery and is **FREE** for first 1TB/month.

### 6.1 Create Distribution
1. Search for "CloudFront" in AWS Console
2. Click **"Create distribution"**

### 6.2 Configure Distribution
1. **Origin domain**: Select your S3 bucket from dropdown
2. **Origin access**: Select **"Origin access control settings (recommended)"**
3. Click **"Create new OAC"** → Use default settings → **"Create"**
4. **Viewer protocol policy**: **"Redirect HTTP to HTTPS"**
5. **Allowed HTTP methods**: **"GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE"**
6. **Cache policy**: Select **"CachingOptimized"**
7. Leave other settings as default
8. Click **"Create distribution"**

### 6.3 Update Bucket Policy
After creating distribution, AWS will prompt you to update bucket policy:
1. Click **"Copy policy"**
2. Go to S3 → Your bucket → Permissions → Bucket policy
3. Paste the policy and click **"Save changes"**

### 6.4 Get CloudFront Domain
1. Go to CloudFront → Distributions
2. Copy the **Distribution domain name** (e.g., `d1234abcd.cloudfront.net`)
3. Save this for your `.env` file

---

## Step 7: Configure Django Environment Variables

### 7.1 Update `.env` file

Add these to your production `.env`:

```bash
# AWS S3 Storage (Production)
USE_S3=True
AWS_ACCESS_KEY_ID=AKIA...your-access-key...
AWS_SECRET_ACCESS_KEY=wJalr...your-secret-key...
AWS_STORAGE_BUCKET_NAME=oxidane-media-production
AWS_S3_REGION_NAME=us-east-1

# CloudFront CDN (if using CloudFront)
AWS_CLOUDFRONT_DOMAIN=d1234abcd.cloudfront.net
```

### 7.2 Keep Development Local

In your local `.env`, keep:
```bash
USE_S3=False
```

This ensures development uses local storage.

---

## Step 8: Deploy and Test

### 8.1 Migrate Models
```bash
python manage.py makemigrations
python manage.py migrate
```

### 8.2 Test Upload
1. Log into admin panel
2. Create a lesson
3. Upload a video file
4. Check S3 bucket - file should appear in `media/lesson_videos/`

### 8.3 Test Video Playback
1. Go to course player on frontend
2. Video should load from S3/CloudFront URL
3. Check browser console - URL should be `https://your-cloudfront-domain/media/...`

---

## Cost Monitoring

### Free Tier (First 12 Months)
- **S3 Storage**: 5 GB free
- **S3 Requests**: 20,000 GET, 2,000 PUT requests/month
- **CloudFront**: 1 TB data transfer + 10M requests/month (always free)

### After Free Tier
- **S3 Storage**: $0.023/GB/month
- **S3 Data Transfer**: First 100 GB/month free
- **CloudFront**: First 1 TB/month free (always)

### Example Costs (10GB videos)
- **Year 1**: ~$0.12/month
- **Year 2+**: ~$0.23/month

### Set Up Billing Alerts
1. Go to AWS Console → Billing Dashboard
2. Click **"Budgets"**
3. Create budget: $1/month alert
4. Get email when approaching limit

---

## Security Best Practices

### ✅ Do's
- ✅ Keep `USE_S3=False` in local development
- ✅ Use IAM user with minimal permissions
- ✅ Keep AWS credentials in `.env` (never commit to Git)
- ✅ Enable S3 bucket versioning for backup
- ✅ Use CloudFront for better performance
- ✅ Set up billing alerts

### ❌ Don'ts
- ❌ Never make S3 bucket public
- ❌ Never commit AWS keys to Git
- ❌ Don't use root AWS account credentials
- ❌ Don't give S3 full access (use custom policy)

---

## Troubleshooting

### Issue: "Access Denied" errors
**Solution**: Check IAM policy has `s3:GetObject` and `s3:PutObject` permissions

### Issue: Videos not loading
**Solution**: 
1. Check CloudFront domain in `.env` is correct
2. Verify CORS policy allows your frontend domain
3. Check bucket policy allows CloudFront OAC

### Issue: Slow uploads
**Solution**: 
1. Check you're using closest AWS region
2. Consider direct browser → S3 uploads (presigned URLs)

### Issue: High costs
**Solution**:
1. Check AWS Cost Explorer
2. Verify you're not storing duplicate files
3. Consider lifecycle policies to delete old files

---

## Migration from Local to S3

If you already have videos in local storage:

### Option 1: AWS CLI Upload
```bash
pip install awscli
aws configure  # Enter your credentials
aws s3 sync backend/media/lesson_videos/ s3://your-bucket-name/media/lesson_videos/
```

### Option 2: Django Management Command
Create `courses/management/commands/migrate_to_s3.py`:

```python
from django.core.management.base import BaseCommand
from courses.models import Lesson

class Command(BaseCommand):
    def handle(self, *args, **options):
        lessons = Lesson.objects.filter(video_source='upload')
        for lesson in lessons:
            if lesson.video_file:
                # Re-save will trigger upload to S3
                lesson.video_file.save(
                    lesson.video_file.name,
                    lesson.video_file,
                    save=True
                )
                self.stdout.write(f'Migrated: {lesson.title}')
```

Run: `python manage.py migrate_to_s3`

---

## Support Resources

- **AWS S3 Documentation**: https://docs.aws.amazon.com/s3/
- **django-storages Documentation**: https://django-storages.readthedocs.io/
- **AWS Free Tier Details**: https://aws.amazon.com/free/
- **CloudFront Documentation**: https://docs.aws.amazon.com/cloudfront/

---

## Quick Reference Commands

```bash
# Install dependencies
pip install django-storages boto3

# Migrate database
python manage.py makemigrations
python manage.py migrate

# Test S3 connection (Python shell)
python manage.py shell
>>> from django.core.files.storage import default_storage
>>> default_storage.bucket_name
'oxidane-media-production'

# Collect static files to S3 (if needed)
python manage.py collectstatic --noinput
```

---

## Next Steps

1. ✅ Create AWS account
2. ✅ Create S3 bucket
3. ✅ Create IAM user
4. ✅ Configure CloudFront
5. ✅ Update `.env` with credentials
6. ✅ Test video upload in admin
7. ✅ Test video playback on frontend
8. ✅ Set up billing alerts
9. ✅ Monitor first month costs

**Estimated Setup Time**: 30-45 minutes

**Monthly Cost**: $0.23/month for 10GB (free first year)
