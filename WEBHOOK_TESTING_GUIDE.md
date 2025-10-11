# 🧪 Webhook Testing Guide

## ✅ What's Been Implemented

### Backend Complete:
- ✅ Database table `webhook_subscriptions`
- ✅ Gmail webhook endpoint `/webhook/gmail`
- ✅ Outlook webhook endpoint `/webhook/outlook`
- ✅ Gmail watch service (setup, stop, renew)
- ✅ Outlook subscription service (create, delete, renew)
- ✅ Celery tasks for automatic renewal
- ✅ API endpoint `/email/webhook/setup/{connection_id}` to activate webhooks

### Configuration Required:
- Gmail Pub/Sub topic: `projects/bbrm-474222/topics/gmail-notifications` ✅
- Outlook Tenant ID: `3e90cbca-024c-4aa6-97b6-bcf8e9f95d15` ✅

---

## 🚀 STEP-BY-STEP TESTING

### Step 1: Add Environment Variables

Add these to your `.env` file (same location as your existing variables):

```bash
# Gmail Webhook Configuration
GMAIL_PUBSUB_TOPIC="projects/bbrm-474222/topics/gmail-notifications"
GMAIL_PROJECT_ID="bbrm-474222"

# Outlook Webhook Configuration
OUTLOOK_TENANT_ID="3e90cbca-024c-4aa6-97b6-bcf8e9f95d15"

# Webhook Base URL (will update with ngrok later)
WEBHOOK_BASE_URL="http://localhost:8000"
```

### Step 2: Create Database Table

Run the SQL migration:

```bash
docker exec -it projectai-postgres-1 psql -U admin -d bbrm_db -f /path/to/create_webhook_subscriptions_table.sql
```

Or copy the SQL and run it manually:

```bash
docker exec -it projectai-postgres-1 psql -U admin -d bbrm_db
```

Then paste the content of `create_webhook_subscriptions_table.sql`.

### Step 3: Restart Backend Services

```bash
docker-compose restart backend celery_worker celery_beat
```

### Step 4: Install and Setup ngrok

#### Install ngrok:
```bash
# macOS
brew install ngrok

# Or download from https://ngrok.com/download
```

#### Start ngrok:
```bash
ngrok http 8000
```

You'll see output like:
```
Forwarding   https://abc123def456.ngrok-free.app -> http://localhost:8000
```

**Copy the https URL** (e.g., `https://abc123def456.ngrok-free.app`)

### Step 5: Update Webhook Base URL

**Option A - Temporary (for this session):**

Update the environment variable in Docker:
```bash
docker exec -it projectai-backend-1 /bin/bash
# Inside container:
export WEBHOOK_BASE_URL="https://abc123def456.ngrok-free.app"
exit
```

**Option B - Permanent (update .env):**

Update `.env`:
```bash
WEBHOOK_BASE_URL="https://abc123def456.ngrok-free.app"
```

Then restart backend:
```bash
docker-compose restart backend
```

### Step 6: Update Google Cloud Pub/Sub Subscription

Since Gmail uses Pub/Sub, we need to create a **Push subscription** now:

1. Go to [Google Cloud Console](https://console.cloud.google.com/) > Pub/Sub > Subscriptions
2. Click **CREATE SUBSCRIPTION**
3. Configuration:
   - Subscription ID: `gmail-push-subscription`
   - Select topic: `gmail-notifications`
   - Delivery type: **Push**
   - Endpoint URL: `https://YOUR-NGROK-URL/webhook/gmail` (replace with your ngrok URL)
   - Example: `https://abc123def456.ngrok-free.app/webhook/gmail`
4. Click **CREATE**

---

## 🧪 TESTING WEBHOOKS

### Test 1: Setup Gmail Webhook

#### 1. Get your Gmail connection ID

Open browser console and go to Email Settings page, then:
```javascript
// In browser console
fetch('http://localhost:8000/email/connections', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN' // Get from localStorage
  }
})
.then(r => r.json())
.then(console.log)
```

Find the `id` of your Gmail connection.

#### 2. Setup webhook via API

```bash
curl -X POST http://localhost:8000/email/webhook/setup/CONNECTION_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Or use the frontend (we'll add a button later).

#### 3. Send yourself a test email

Send an email to your Gmail account (the one you connected).

#### 4. Check logs

Watch ngrok for incoming requests:
```bash
# ngrok shows all HTTP requests in real-time
```

Watch backend logs:
```bash
docker logs -f projectai-backend-1
```

You should see:
```
📨 Gmail webhook received: {...}
📬 Processing Gmail notification for your@email.com
✅ Notification processed: X emails fetched
```

#### 5. Verify in database

```bash
docker exec -it projectai-postgres-1 psql -U admin -d bbrm_db
```

```sql
-- Check webhook subscription
SELECT * FROM webhook_subscriptions;

-- Check intercepted emails
SELECT id, subject, sender_email, email_received_at 
FROM intercepted_emails 
ORDER BY email_received_at DESC 
LIMIT 5;
```

---

### Test 2: Setup Outlook Webhook

#### 1. Get your Outlook connection ID

Same as Gmail test above.

#### 2. Setup webhook via API

```bash
curl -X POST http://localhost:8000/email/webhook/setup/CONNECTION_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 3. Send yourself a test email

Send an email to your Outlook/Hotmail account.

#### 4. Check logs

Same as Gmail test. You should see:
```
📨 Outlook webhook received: 1 notifications
📬 Processing Outlook notification for your@outlook.com
✅ Notification processed: X emails fetched
```

---

## 🔍 DEBUGGING

### Check Webhook Status

Visit: `http://localhost:8000/webhook/status`

This shows:
- Total subscriptions
- Active vs expired
- Last notification time
- Notification count

### Check Subscription Expiry

```sql
SELECT 
    id,
    provider,
    status,
    expires_at,
    notification_count,
    last_notification_at
FROM webhook_subscriptions
ORDER BY expires_at;
```

### Test Webhook Renewal

Force renewal manually:

```python
# In Python shell or temporary script
from app.database.config import SessionLocal
from app.services.gmail_webhook_service import GmailWebhookService
from app.models.email_connection import EmailConnection

db = SessionLocal()
gmail_webhook = GmailWebhookService(db)

# Renew all expiring watches
result = gmail_webhook.check_and_renew_expiring_watches()
print(result)
```

### Common Issues

**Issue 1: Gmail webhook not receiving notifications**

Check:
1. Pub/Sub subscription endpoint URL is correct (ngrok URL)
2. Subscription is ACTIVE in Google Cloud Console
3. Gmail watch was setup successfully (check `webhook_subscriptions` table)
4. ngrok is still running (it stops after inactivity)

**Issue 2: Outlook webhook validation fails**

Check:
1. `WEBHOOK_BASE_URL` is set to ngrok URL
2. Backend was restarted after updating env var
3. Microsoft Graph API permissions include `Mail.ReadWrite`
4. Admin consent was granted

**Issue 3: Webhooks stop working after some time**

This is expected:
- Gmail watches expire after 7 days
- Outlook subscriptions expire after 3 days
- Celery Beat renewal tasks will handle this automatically

Manual renewal:
```bash
# Trigger renewal tasks manually
docker exec -it projectai-celery_worker-1 celery -A app.celery_app call app.tasks.webhook_renewal.renew_gmail_watches
docker exec -it projectai-celery_worker-1 celery -A app.celery_app call app.tasks.webhook_renewal.renew_outlook_subscriptions
```

---

## 📊 MONITORING

### Real-time Logs

**Backend:**
```bash
docker logs -f projectai-backend-1 | grep -E "(📨|📬|✅|❌)"
```

**Celery Worker:**
```bash
docker logs -f projectai-celery_worker-1 | grep -E "(🔄|✅|❌)"
```

**ngrok:**
Open http://127.0.0.1:4040 in browser for ngrok web interface showing all requests.

### Performance Check

Before webhooks (polling):
- Latency: 30-300 seconds
- CPU: Constant polling
- API calls: Every X minutes

After webhooks:
- Latency: < 1 second
- CPU: Only on email arrival
- API calls: Only on notification

---

## 🎯 NEXT STEPS

Once webhooks are tested and working:

1. ✅ Update frontend Email Settings page to show webhook status
2. ✅ Add "Setup Webhook" button for each connection
3. ✅ Show expiration date and renewal status
4. ⬜ Deploy to production with real domain (replace ngrok)
5. ⬜ Monitor webhook reliability for 48 hours
6. ⬜ Completely disable polling (keep only as fallback)

---

## 🚀 PRODUCTION DEPLOYMENT

For production, you'll need:

1. **Real domain** (e.g., `https://api.reqorai.com`)
2. Update `WEBHOOK_BASE_URL` in .env
3. Update Pub/Sub subscription endpoint
4. Recreate Outlook subscriptions with new URL

Webhooks will continue working even after server restarts, as long as:
- Database persists (`webhook_subscriptions` table)
- Celery Beat runs renewal tasks
- Subscription endpoint remains accessible

---

Ready to test? Follow Step 1-6 and then run Test 1 (Gmail) ! 🧪

