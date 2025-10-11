#!/bin/bash

# Script to apply webhook migration to database

echo "🔧 Applying webhook migration..."

# Check if docker is running
if ! docker ps &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if postgres container exists
if ! docker ps | grep -q "projectai-postgres"; then
    echo "❌ PostgreSQL container not found. Is docker-compose running?"
    exit 1
fi

# Apply migration
echo "📊 Creating webhook_subscriptions table..."
docker exec -i projectai-postgres-1 psql -U admin -d bbrm_db < create_webhook_subscriptions_table.sql

if [ $? -eq 0 ]; then
    echo "✅ Migration applied successfully!"
    echo ""
    echo "📋 Verifying table creation..."
    docker exec -it projectai-postgres-1 psql -U admin -d bbrm_db -c "\d webhook_subscriptions"
    echo ""
    echo "🎉 Done! Now restart services:"
    echo "   docker-compose restart backend celery_worker celery_beat"
else
    echo "❌ Migration failed. Check the error above."
    exit 1
fi

