# Railway Deployment Configuration

Railway is a modern deployment platform that makes it easy to deploy your Telegram bot.

## Quick Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-id)

## Manual Deployment

### 1. Create Railway Account
Visit [railway.app](https://railway.app) and sign up with your GitHub account.

### 2. Create New Project
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose this repository

### 3. Configure Environment Variables

Add these environment variables in Railway dashboard:

**Required Variables:**
```
BOT_TOKEN=1234567890:AAAbbbCCCdddEEEfffGGGhhhIIIjjj
GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}
SPREADSHEET_ID=1QL1CRY3M9Av-WlDS5gswA2Lq14OPdt0TME_dpwPIuC4
```

**Optional Variables:**
```
ADMIN_IDS=123456789,987654321
REPORT_CHAT_ID=-1001234567890
METRIKA_COUNTER_ID=101368505
METRIKA_OAUTH_TOKEN=y0_AAAA-BBBB-CCCC-DDDD-EEEE
USE_POSTGRES=true
DEBUG_MODE=false
```

### 4. Add Services

#### PostgreSQL (Optional)
1. Click "Add Service" → "Database" → "PostgreSQL"
2. Copy the DATABASE_URL from the service
3. Add DATABASE_URL to your environment variables

#### Redis (Optional)
1. Click "Add Service" → "Database" → "Redis"
2. Copy connection details and add:
   - REDIS_HOST
   - REDIS_PORT
   - REDIS_PASSWORD

### 5. Deploy

Railway will automatically deploy your bot when you push to the main branch.

## Environment Setup

### Google Sheets API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Sheets API
4. Create service account credentials
5. Download JSON key and add to GOOGLE_CREDENTIALS_JSON

### Telegram Bot Setup
1. Message @BotFather on Telegram
2. Create new bot with /newbot
3. Copy the token to BOT_TOKEN variable

### Yandex.Metrika Setup (Optional)
1. Go to [Yandex.Metrika](https://metrica.yandex.com/)
2. Get your counter ID
3. Generate OAuth token
4. Add to environment variables

## File Structure
```
telegram-bot/
├── bot.py              # Main bot file
├── config.py           # Configuration
├── requirements.txt    # Dependencies
├── Dockerfile         # Docker configuration
├── railway.toml       # Railway configuration
├── handlers/          # Command handlers
├── services/          # Core services
├── utils/             # Utility functions
└── .env.example       # Environment template
```

## Monitoring

Check your bot status in Railway dashboard:
- **Logs**: View real-time logs
- **Metrics**: Monitor CPU/Memory usage
- **Deployments**: Track deployment history

## Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check BOT_TOKEN is correct
   - Verify environment variables

2. **Google Sheets error**
   - Verify GOOGLE_CREDENTIALS_JSON format
   - Check API permissions

3. **Database connection**
   - Ensure DATABASE_URL is set
   - Check PostgreSQL service status

### Logs
View logs in Railway dashboard or use Railway CLI:
```bash
railway logs
```

## Scaling

Railway automatically scales based on usage. For high-traffic bots:
- Consider upgrading to Pro plan
- Enable auto-scaling
- Monitor resource usage

## Support

- Railway Documentation: https://docs.railway.app/
- Telegram Bot API: https://core.telegram.org/bots/api
- Project Issues: Create issue in GitHub repository
