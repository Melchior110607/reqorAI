'use client';

import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Textarea } from '@/components/ui/Textarea';
import { clientsAPI } from '@/services/api';
import { Client, RequestType, RequestPriority, ReminderFrequency } from '@/types';

interface RequestFormData {
  title: string;
  description: string;
  client_id: number | '';
  type: RequestType;
  priority: RequestPriority;
  due_date: string;
  reminder_frequency: ReminderFrequency;
  email_recipients: string;
  is_priority: boolean;
}

interface RequestFormProps {
  onSubmit: (data: any) => Promise<void>;
  onCancel: () => void;
  initialData?: Partial<RequestFormData>;
  loading?: boolean;
}

export function RequestForm({ onSubmit, onCancel, initialData, loading }: RequestFormProps) {
  const [clients, setClients] = useState<Client[]>([]);
  const [formLoading, setFormLoading] = useState(false);
  const [formData, setFormData] = useState<RequestFormData>({
    title: '',
    description: '',
    client_id: '',
    type: RequestType.OUTGOING,
    priority: RequestPriority.MEDIUM,
    due_date: '',
    reminder_frequency: ReminderFrequency.NEVER,
    email_recipients: '',
    is_priority: false,
    ...initialData,
  });

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const data = await clientsAPI.getAll();
      setClients(data);
    } catch (error) {
      console.error('Error fetching clients:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormLoading(true);
    
    try {
      const submitData = {
        ...formData,
        client_id: Number(formData.client_id),
        email_recipients: formData.email_recipients ? formData.email_recipients.split(',').map(email => email.trim()) : [],
        due_date: formData.due_date || null,
      };

      await onSubmit(submitData);
    } catch (error) {
      console.error('Error in form submission:', error);
      throw error; // Re-throw pour que les pages puissent gérer l'erreur
    } finally {
      setFormLoading(false);
    }
  };

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }));
  }, []);

  const typeOptions = [
    { value: RequestType.OUTGOING, label: 'Outgoing (Our request)' },
    { value: RequestType.INCOMING, label: 'Incoming (Client request)' },
  ];

  const priorityOptions = [
    { value: RequestPriority.LOW, label: 'Low' },
    { value: RequestPriority.MEDIUM, label: 'Medium' },
    { value: RequestPriority.HIGH, label: 'High' },
    { value: RequestPriority.URGENT, label: 'Urgent' },
  ];

  const reminderOptions = [
    { value: ReminderFrequency.NEVER, label: 'Never' },
    { value: ReminderFrequency.DAILY, label: 'Daily' },
    { value: ReminderFrequency.WEEKLY, label: 'Weekly' },
    { value: ReminderFrequency.MONTHLY, label: 'Monthly' },
  ];

  const clientOptions = [
    { value: '', label: 'Select a client' },
    ...clients.map(client => ({ value: client.id.toString(), label: `${client.name} (${client.company})` }))
  ];

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        label="Title"
        name="title"
        value={formData.title}
        onChange={handleChange}
        required
        placeholder="Enter request title"
      />

      <Textarea
        label="Description"
        name="description"
        value={formData.description}
        onChange={handleChange}
        required
        placeholder="Describe the request in detail"
        rows={4}
      />

      <Select
        label="Client"
        name="client_id"
        value={formData.client_id.toString()}
        onChange={handleChange}
        options={clientOptions}
        required
      />

      <Select
        label="Type"
        name="type"
        value={formData.type}
        onChange={handleChange}
        options={typeOptions}
      />

      <div className="grid grid-cols-2 gap-4">
        <Select
          label="Priority"
          name="priority"
          value={formData.priority}
          onChange={handleChange}
          options={priorityOptions}
        />

        <Select
          label="Reminder Frequency"
          name="reminder_frequency"
          value={formData.reminder_frequency}
          onChange={handleChange}
          options={reminderOptions}
        />
      </div>

      <Input
        label="Due Date"
        name="due_date"
        type="datetime-local"
        value={formData.due_date}
        onChange={handleChange}
      />

      <Input
        label="Email Recipients"
        name="email_recipients"
        value={formData.email_recipients}
        onChange={handleChange}
        placeholder="email1@example.com, email2@example.com"
      />

      <div className="flex items-center">
        <input
          type="checkbox"
          id="is_priority"
          name="is_priority"
          checked={formData.is_priority}
          onChange={handleChange}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <label htmlFor="is_priority" className="ml-2 block text-sm text-gray-900">
          Mark as priority (will appear at the top)
        </label>
      </div>

      <div className="flex justify-end space-x-3 pt-4">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={formLoading || loading} disabled={formLoading || loading}>
          {initialData ? 'Update Request' : 'Create Request'}
        </Button>
      </div>
    </form>
  );
}
