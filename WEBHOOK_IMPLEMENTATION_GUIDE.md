# 🔔 Email Webhooks Implementation Guide

## 📊 Current vs New Architecture

### ❌ Current (Polling - Celery Beat)
```
Celery Beat (every X min) → Backend → Gmail/Outlook API → Fetch emails → Database
```
**Problems:**
- Delay (emails arrive after X minutes)
- Resource intensive (constant polling)
- Network errors mark connection as ERROR
- Not scalable

### ✅ New (Webhooks - Real-time)
```
Gmail/Outlook → Push notification → Backend endpoint → Database
```
**Benefits:**
- Real-time (< 1 second)
- No polling overhead
- Scalable
- Reliable

---

## 🔧 GMAIL WEBHOOK SETUP

### Part 1️⃣ : Google Cloud Console Configuration

#### Step 1: Enable Pub/Sub API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (the one with Gmail API enabled)
3. Go to **APIs & Services** > **Library**
4. Search for **"Cloud Pub/Sub API"**
5. Click **ENABLE**

#### Step 2: Create Pub/Sub Topic
1. Go to **Pub/Sub** > **Topics**
2. Click **CREATE TOPIC**
3. Topic ID: `gmail-notifications`
4. Leave other settings as default
5. Click **CREATE**
6. **IMPORTANT**: Copy the full topic name (e.g., `projects/your-project-id/topics/gmail-notifications`)

#### Step 3: Grant Gmail Permission
1. Stay on the topic page (`gmail-notifications`)
2. Click **PERMISSIONS** tab
3. Click **ADD PRINCIPAL**
4. In "New principals" field, enter:
   ```
   gmail-api-push@system.gserviceaccount.com
   ```
5. In "Role", select: **Pub/Sub Publisher**
6. Click **SAVE**

#### Step 4: Create Pub/Sub Subscription (Push)
1. Go to **Pub/Sub** > **Subscriptions**
2. Click **CREATE SUBSCRIPTION**
3. Subscription ID: `gmail-push-subscription`
4. Select topic: `gmail-notifications`
5. Delivery type: **Push**
6. Endpoint URL: `https://YOUR_DOMAIN/webhook/gmail` (we'll set up ngrok for testing)
7. Leave other settings as default
8. Click **CREATE**

#### Step 5: Update OAuth Scopes
1. Go to **APIs & Services** > **Credentials**
2. Click on your OAuth 2.0 Client ID
3. Ensure these scopes are allowed:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.metadata`
   - `https://www.googleapis.com/auth/pubsub` (NEW - needed for watch)

---

## 🔧 OUTLOOK WEBHOOK SETUP

### Part 2️⃣ : Azure Portal Configuration

#### Step 1: Update API Permissions
1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Select your app
4. Go to **API permissions**
5. Click **Add a permission**
6. Select **Microsoft Graph** > **Delegated permissions**
7. Add these permissions:
   - `Mail.Read` (already there)
   - `Mail.ReadWrite` (NEW - needed for subscriptions)
8. Click **Add permissions**
9. Click **Grant admin consent** (important!)

#### Step 2: Note Your App Details
You'll need these values (copy them):
- **Application (client) ID**: `6b0df61d-3791-4cdf-9929-89c3f18d343b` (from .env)
- **Directory (tenant) ID**: Found in app overview page
- **Client Secret**: `wBP8Q~Mm2vnmtbXmC-DtQHWiNuL4bsEOlnUS.bb8` (from .env)

---

## 🚀 BACKEND IMPLEMENTATION

### Part 3️⃣ : What I'll Implement

#### 1. New Webhook Endpoints
```python
# backend/app/api/webhooks.py
@router.post("/gmail")  # Receives Gmail push notifications
@router.post("/outlook")  # Receives Outlook notifications
@router.post("/outlook/validation")  # Validation endpoint for subscription
```

#### 2. Gmail Watch Service
```python
# backend/app/services/gmail_webhook_service.py
- watch_user_mailbox()  # Start watching for new emails
- renew_watch()  # Renew watch every 7 days
- process_notification()  # Process incoming push
```

#### 3. Outlook Subscription Service
```python
# backend/app/services/outlook_webhook_service.py
- create_subscription()  # Create webhook subscription
- renew_subscription()  # Renew every 3 days
- validate_token()  # Validate subscription request
- process_notification()  # Process incoming webhook
```

#### 4. Background Jobs (Celery)
```python
# Keep Celery Beat ONLY for:
- Renewing Gmail watch (every 6 days)
- Renewing Outlook subscriptions (every 2 days)
- Cleanup old emails (optional)
```

#### 5. Database Changes
```sql
-- New table: webhook_subscriptions
CREATE TABLE webhook_subscriptions (
    id SERIAL PRIMARY KEY,
    connection_id INTEGER REFERENCES email_connections(id),
    provider VARCHAR(50),  -- 'gmail' or 'outlook'
    subscription_id VARCHAR(255),  -- Microsoft Graph subscription ID
    topic_name VARCHAR(255),  -- Gmail Pub/Sub topic
    expires_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50),  -- 'active', 'expired', 'failed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 🧪 TESTING SETUP (ngrok)

### Part 4️⃣ : Expose Local Server

Since webhooks need a public URL, we'll use **ngrok** for testing:

#### Install ngrok
```bash
# macOS
brew install ngrok

# Or download from https://ngrok.com/download
```

#### Start ngrok
```bash
ngrok http 8000
```

You'll get a public URL like: `https://abc123.ngrok.io`

#### Update Webhook URLs
1. **Gmail**: Update Pub/Sub subscription endpoint to `https://abc123.ngrok.io/webhook/gmail`
2. **Outlook**: Will use `https://abc123.ngrok.io/webhook/outlook` when creating subscription

---

## 📋 IMPLEMENTATION PLAN

### Phase 1: Gmail Webhooks ✅
1. ✅ You: Configure Google Cloud Pub/Sub (Steps above)
2. ⬜ Me: Create Gmail webhook endpoint
3. ⬜ Me: Implement watch service
4. ⬜ Me: Test with ngrok
5. ⬜ Me: Add watch renewal job

### Phase 2: Outlook Webhooks ✅
1. ✅ You: Update Azure permissions (Steps above)
2. ⬜ Me: Create Outlook webhook endpoint
3. ⬜ Me: Implement subscription service
4. ⬜ Me: Test with ngrok
5. ⬜ Me: Add subscription renewal job

### Phase 3: Migration & Cleanup
1. ⬜ Me: Keep both systems (polling + webhooks) for 24h
2. ⬜ Me: Verify webhooks work reliably
3. ⬜ Me: Disable polling tasks
4. ⬜ Me: Update UI to show webhook status

---

## 🎯 WHAT YOU NEED TO DO NOW

### For Gmail:
1. ✅ Enable Pub/Sub API
2. ✅ Create topic `gmail-notifications`
3. ✅ Grant permission to `gmail-api-push@system.gserviceaccount.com`
4. ⏸️ **WAIT** - Don't create subscription yet (I'll do it programmatically)

### For Outlook:
1. ✅ Add `Mail.ReadWrite` permission in Azure Portal
2. ✅ Grant admin consent
3. ✅ Copy your Tenant ID from app overview page

### Share with me:
- Gmail Pub/Sub topic full name (e.g., `projects/PROJECT_ID/topics/gmail-notifications`)
- Azure Tenant ID

---

## 🔒 SECURITY NOTES

### Gmail:
- Pub/Sub validates requests automatically
- We'll verify message signatures

### Outlook:
- Microsoft sends validation token on subscription creation
- We'll verify `clientState` on each notification
- Notifications include encrypted change data

---

## 📊 MONITORING

After implementation, you'll see:
- Real-time email arrival (< 1 second)
- Webhook status in Email Settings page
- Subscription expiration dates
- Auto-renewal logs in Celery

---

## ❓ FAQ

**Q: What if webhooks fail?**
A: We'll keep a fallback polling mechanism (every 1 hour) for critical cases.

**Q: Ngrok URL changes on restart?**
A: Yes. For production, you'll need a real domain (e.g., `https://api.reqorai.com`).

**Q: What about multiple users?**
A: Each user gets their own Gmail watch + Outlook subscription.

**Q: Costs?**
A: Pub/Sub (Gmail) is free for < 10GB/month. Outlook webhooks are free.

---

Ready to implement? Complete the steps above and share:
1. Gmail Pub/Sub topic name
2. Azure Tenant ID

Then I'll build the webhook system! 🚀


