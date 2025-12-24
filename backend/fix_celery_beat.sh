#!/bin/bash
# Fix duplicate Celery Beat processes causing duplicate auto-renewal charges

echo "🔍 Checking for duplicate Celery Beat processes..."

# Find all celery beat processes
BEAT_PIDS=$(ps aux | grep 'celery.*beat' | grep -v grep | awk '{print $2}')
BEAT_COUNT=$(echo "$BEAT_PIDS" | wc -l)

echo "Found $BEAT_COUNT Celery Beat process(es)"

if [ $BEAT_COUNT -gt 1 ]; then
    echo "⚠️  WARNING: Multiple Celery Beat processes detected!"
    echo "This causes duplicate task execution"
    echo ""
    echo "Processes:"
    ps aux | grep 'celery.*beat' | grep -v grep
    echo ""
    
    # Get the oldest process (keep it, kill others)
    OLDEST_PID=$(echo "$BEAT_PIDS" | head -1)
    echo "Keeping oldest process: PID $OLDEST_PID"
    echo ""
    
    # Kill newer processes
    echo "$BEAT_PIDS" | tail -n +2 | while read pid; do
        echo "🔪 Killing duplicate Celery Beat process: PID $pid"
        kill -9 $pid
    done
    
    echo ""
    echo "✅ Duplicate processes killed"
    echo "Remaining Celery Beat process:"
    ps aux | grep 'celery.*beat' | grep -v grep
    
elif [ $BEAT_COUNT -eq 1 ]; then
    echo "✅ Only one Celery Beat process running (correct)"
    ps aux | grep 'celery.*beat' | grep -v grep
else
    echo "❌ No Celery Beat process running!"
    echo "Auto-renewals won't work. Start Celery Beat with:"
    echo "  cd /var/www/oxidane/backend"
    echo "  source /var/www/oxidane/venv/bin/activate"
    echo "  celery -A oxidane beat --loglevel=info --detach"
fi

echo ""
echo "📊 Summary of all Celery processes:"
ps aux | grep celery | grep -v grep
