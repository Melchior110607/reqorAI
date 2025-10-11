# ✅ YOUR CHECKLIST - Webhook Configuration

## 📋 GMAIL SETUP (Google Cloud Console)

### Step 1: Enable Pub/Sub API
- [ ] Go to https://console.cloud.google.com/
- [ ] Select your project (the one with Gmail API)
- [ ] Go to **APIs & Services** > **Library**
- [ ] Search for **"Cloud Pub/Sub API"**
- [ ] Click **ENABLE**

### Step 2: Create Pub/Sub Topic
- [ ] Go to **Pub/Sub** > **Topics**
- [ ] Click **CREATE TOPIC**
- [ ] Topic ID: `gmail-notifications`
- [ ] Click **CREATE**
- [ ] **COPY THIS**: Full topic name will look like:
  ```
  projects/YOUR-PROJECT-ID/topics/gmail-notifications
  ```
  → **SEND ME THIS FULL PATH**

### Step 3: Grant Gmail Permission
- [ ] Stay on the topic page
- [ ] Click **PERMISSIONS** tab
- [ ] Click **ADD PRINCIPAL**
- [ ] New principal: `gmail-api-push@system.gserviceaccount.com`
- [ ] Role: **Pub/Sub Publisher**
- [ ] Click **SAVE**

### ⚠️ DON'T create subscription yet - I'll do it programmatically!

---

## 📋 OUTLOOK SETUP (Azure Portal)

### Step 1: Add Permissions
- [ ] Go to https://portal.azure.com/
- [ ] Navigate to **Azure Active Directory** > **App registrations**
- [ ] Select your app
- [ ] Go to **API permissions**
- [ ] Click **Add a permission**
- [ ] Select **Microsoft Graph** > **Delegated permissions**
- [ ] Check: **Mail.ReadWrite**
- [ ] Click **Add permissions**
- [ ] Click **Grant admin consent for [Your Org]** (IMPORTANT!)

### Step 2: Get Tenant ID
- [ ] Stay in your app page
- [ ] Go to **Overview**
- [ ] **COPY THIS**: Directory (tenant) ID (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
  → **SEND ME THIS TENANT ID**

---

## 📤 WHAT TO SEND ME

Once you've completed the above steps, reply with:

```
Gmail Pub/Sub topic: projects/YOUR-PROJECT-ID/topics/gmail-notifications
Azure Tenant ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Then I'll implement the webhooks! 🚀

---

## 🧪 FOR TESTING (Later)

When we test, you'll need to install ngrok:
```bash
brew install ngrok
# or download from https://ngrok.com/download
```

But don't do this yet - I'll guide you when we're ready to test.

---

## ❓ Questions?

- **Why Pub/Sub for Gmail?**: Gmail doesn't support direct webhooks, only push via Pub/Sub
- **Why direct webhook for Outlook?**: Microsoft Graph supports direct webhook subscriptions
- **Cost?**: Both are free for normal usage (< 10GB/month Pub/Sub, unlimited Graph webhooks)


