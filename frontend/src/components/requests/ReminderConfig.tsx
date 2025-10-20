'use client';

import { useState, useEffect } from 'react';

interface ReminderConfigProps {
  requestId: number;
  initialConfig: {
    reminder_enabled: boolean;
    reminder_frequency: string;
    reminder_message: string | null;
    last_reminder_sent_at: string | null;
    reminder_count: number;
  };
  onUpdate: () => void;
}

export default function ReminderConfig({ requestId, initialConfig, onUpdate }: ReminderConfigProps) {
  const [enabled, setEnabled] = useState(initialConfig.reminder_enabled);
  const [frequency, setFrequency] = useState(initialConfig.reminder_frequency || 'weekly');
  const [customMessage, setCustomMessage] = useState(initialConfig.reminder_message || '');
  const [saving, setSaving] = useState(false);
  const [sending, setSending] = useState(false);

  // Update state when initialConfig changes
  useEffect(() => {
    setEnabled(initialConfig.reminder_enabled);
    setFrequency(initialConfig.reminder_frequency || 'weekly');
    setCustomMessage(initialConfig.reminder_message || '');
  }, [initialConfig]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      
      const params = new URLSearchParams({
        reminder_enabled: enabled.toString(),
        reminder_frequency: frequency
      });
      
      if (customMessage) {
        params.append('reminder_message', customMessage);
      }
      
      const response = await fetch(`http://localhost:8000/requests/${requestId}/configure-reminder?${params.toString()}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        }
      });

      if (response.ok) {
        alert('✅ Configuration saved!');
        onUpdate();
      } else {
        const errorData = await response.json();
        alert(`❌ Failed: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error saving reminder config:', error);
      alert('Error saving reminder configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleSendNow = async () => {
    if (!confirm('Send reminder email now?')) return;

    setSending(true);
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/requests/${requestId}/send-reminder-now`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        alert(`✅ Reminder sent to ${data.sent_to}!`);
        onUpdate();
      } else {
        const error = await response.json();
        alert(`❌ Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error sending reminder:', error);
      alert('Error sending reminder');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Auto-Reminder System</h3>
      
      <div className="space-y-4">
        {/* Enable Toggle */}
        <div className="flex items-center justify-between">
          <label htmlFor="reminder-enabled" className="text-sm font-medium text-gray-900">
            Enable Reminders
          </label>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              id="reminder-enabled"
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {enabled && (
          <>
            {/* Frequency */}
            <div>
              
              <label className="block text-sm font-medium text-gray-900 mb-2">
                Frequency
              </label>
              
              <select
              
                value={frequency}
                onChange={(e) => setFrequency(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              >
                <option value="daily">Daily</option>
                <option value="weekly"> Weekly </option>
                <option value="biweekly">Biweekly</option>
                <option value="monthly"> Monthly </option>
              </select>
            </div>

            {/* Custom Message */}
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">
                Custom Message (optional)
              </label>
              
              <textarea
                value={customMessage}
                onChange={(e) => setCustomMessage(e.target.value)}
                rows={3}
                placeholder="Leave empty for AI-generated message..."
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
              />
            </div>

            {/* Stats */}
            {initialConfig.reminder_count > 0 && (
              <div className="text-sm text-gray-900">
                <p><strong>{initialConfig.reminder_count}</strong> reminder(s) sent</p>
                {initialConfig.last_reminder_sent_at && (
                  <p className="text-gray-900">Last: {new Date(initialConfig.last_reminder_sent_at).toLocaleString()}</p>
                )}
              </div>
            )}

            {/* Buttons */}
            <div className="flex gap-2 pt-2">
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 disabled:bg-gray-400"
              >
                {saving ? 'Saving...' : 'Save Configuration'}
              </button>
              <button
                onClick={handleSendNow}
                disabled={sending}
                className="flex-1 bg-green-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-700 disabled:bg-gray-400"
              >
                {sending ? 'Sending...' : 'Send Now'}
              </button>
            </div>
          </>
        )}

        {!enabled && (
          <p className="text-sm text-gray-900">
            Enable to automatically send follow-up emails
          </p>
        )}
      </div>
    </div>
  );
}
