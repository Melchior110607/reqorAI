'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Select } from '@/components/ui/Select';
import { requestsAPI } from '@/services/api';
import { RequestWithClient, RequestStatus, RequestType, RequestPriority } from '@/types';
import { 
  ArrowLeft, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Mail,
  Upload,
  FileText,
  Send,
  Edit,
  Save,
  X
} from 'lucide-react';

export default function RequestDetailPage() {
  const params = useParams();
  const router = useRouter();
  const requestId = parseInt(params.id as string);
  
  const [request, setRequest] = useState<RequestWithClient | null>(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    status: '',
    priority: '',
    title: '',
    description: ''
  });
  
  // Pour incoming requests
  const [emailText, setEmailText] = useState('');
  const [attachments, setAttachments] = useState<File[]>([]);
  const [dragActive, setDragActive] = useState(false);
  
  // Pour outgoing requests
  const [responses, setResponses] = useState<any[]>([]);
  const [reminderText, setReminderText] = useState('');
  const [autoReminderEnabled, setAutoReminderEnabled] = useState(false);

  useEffect(() => {
    fetchRequest();
  }, [requestId]);

  const fetchRequest = async () => {
    try {
      const data = await requestsAPI.getById(requestId);
      setRequest(data);
      setEditData({
        status: data.status,
        priority: data.priority,
        title: data.title,
        description: data.description
      });
    } catch (error) {
      console.error('Error fetching request:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async () => {
    if (!request) return;
    
    try {
      const updatedRequest = await requestsAPI.update(request.id, {
        status: editData.status as RequestStatus,
        priority: editData.priority as RequestPriority,
        title: editData.title,
        description: editData.description
      });
      
      // Mettre à jour l'état local avec les nouvelles données
      setRequest(prev => prev ? {
        ...prev,
        status: editData.status as RequestStatus,
        priority: editData.priority as RequestPriority,
        title: editData.title,
        description: editData.description
      } : null);
      
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating request:', error);
      alert('Error updating request');
    }
  };

  const getStatusIcon = (status: RequestStatus) => {
    switch (status) {
      case RequestStatus.PENDING:
        return <Clock className="w-5 h-5 text-yellow-500" />;
      case RequestStatus.COMPLETED:
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case RequestStatus.OVERDUE:
        return <AlertCircle className="w-5 h-5 text-red-500" />;
    }
  };

  const getStatusColor = (status: RequestStatus) => {
    switch (status) {
      case RequestStatus.PENDING:
        return 'bg-yellow-100 text-yellow-800';
      case RequestStatus.COMPLETED:
        return 'bg-green-100 text-green-800';
      case RequestStatus.OVERDUE:
        return 'bg-red-100 text-red-800';
    }
  };

  const getPriorityColor = (priority: RequestPriority) => {
    switch (priority) {
      case 'low':
        return 'bg-gray-100 text-gray-800';
      case 'medium':
        return 'bg-blue-100 text-blue-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'urgent':
        return 'bg-red-100 text-red-800';
    }
  };

  // Drag and drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const files = Array.from(e.dataTransfer.files);
      setAttachments(prev => [...prev, ...files]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      setAttachments(prev => [...prev, ...files]);
    }
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const handleSendEmail = async () => {
    if (!request || !emailText.trim()) {
      alert('Please enter some text before sending');
      return;
    }

    // TODO: Implement email sending logic
    console.log('Sending email:', {
      requestId: request.id,
      text: emailText,
      attachments: attachments,
      recipients: request.email_recipients
    });
    
    alert('Email functionality will be implemented in the next phase');
    setEmailText('');
    setAttachments([]);
  };

  const handleSendReminder = async () => {
    if (!request) return;

    const defaultMessage = `
Dear ${request.client_name},

I hope this email finds you well. I wanted to follow up on our request regarding: "${request.title}".

Request Details:
- Description: ${request.description}
- Priority: ${request.priority}
- Created: ${new Date(request.created_at).toLocaleDateString()}
${request.due_date ? `- Due Date: ${new Date(request.due_date).toLocaleDateString()}` : ''}

${reminderText || 'We would appreciate an update on the status of this request at your earliest convenience.'}

Thank you for your attention to this matter.

Best regards,
${request.user?.company_name || 'Your Company'}
    `.trim();

    // TODO: Implement email sending logic
    console.log('Sending reminder:', {
      requestId: request.id,
      message: defaultMessage,
      recipients: request.email_recipients,
      autoReminder: autoReminderEnabled
    });
    
    alert('Reminder email functionality will be implemented in the next phase with email API integration');
    setReminderText('');
  };

  if (loading) {
    return (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
        </div>
    );
  }

  if (!request) {
    return (
        <div className="text-center py-12">
          <p className="text-gray-500">Request not found</p>
          <Button onClick={() => router.back()} className="mt-4">
            Go Back
          </Button>
        </div>
    );
  }

  const statusOptions = [
    { value: RequestStatus.PENDING, label: 'Pending' },
    { value: RequestStatus.COMPLETED, label: 'Completed' },
    { value: RequestStatus.OVERDUE, label: 'Overdue' }
  ];

  const priorityOptions = [
    { value: 'low', label: 'Low' },
    { value: 'medium', label: 'Medium' },
    { value: 'high', label: 'High' },
    { value: 'urgent', label: 'Urgent' }
  ];

  return (
      <div className="px-4 py-6 sm:px-0">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => router.back()}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {isEditing ? (
                  <Input
                    value={editData.title}
                    onChange={(e) => setEditData(prev => ({ ...prev, title: e.target.value }))}
                    className="text-3xl font-bold"
                  />
                ) : (
                  request.title
                )}
              </h1>
              <p className="text-gray-600 mt-2">
                {request.type === RequestType.INCOMING ? 'Incoming' : 'Outgoing'} Request • {request.client_name} ({request.client_company})
              </p>
            </div>
            
            <div className="flex items-center space-x-3">
              {isEditing ? (
                <>
                  <Button onClick={handleStatusUpdate} variant="primary">
                    <Save className="w-4 h-4 mr-2" />
                    Save
                  </Button>
                  <Button onClick={() => setIsEditing(false)} variant="outline">
                    <X className="w-4 h-4 mr-2" />
                    Cancel
                  </Button>
                </>
              ) : (
                <Button onClick={() => setIsEditing(true)} variant="outline">
                  <Edit className="w-4 h-4 mr-2" />
                  Edit
                </Button>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Request Details */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Request Details</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">Description</label>
                  {isEditing ? (
                    <Textarea
                      value={editData.description}
                      onChange={(e) => setEditData(prev => ({ ...prev, description: e.target.value }))}
                      rows={4}
                      className="mt-1"
                    />
                  ) : (
                    <p className="mt-1 text-gray-900">{request.description}</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Status</label>
                    {isEditing ? (
                      <Select
                        value={editData.status}
                        onChange={(e) => setEditData(prev => ({ ...prev, status: e.target.value }))}
                        options={statusOptions}
                        className="mt-1"
                      />
                    ) : (
                      <div className="mt-1 flex items-center">
                        {getStatusIcon(request.status)}
                        <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                          {request.status}
                        </span>
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-700">Priority</label>
                    {isEditing ? (
                      <Select
                        value={editData.priority}
                        onChange={(e) => setEditData(prev => ({ ...prev, priority: e.target.value }))}
                        options={priorityOptions}
                        className="mt-1"
                      />
                    ) : (
                      <div className="mt-1">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(request.priority)}`}>
                          {request.priority}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Created</label>
                    <p className="mt-1 text-gray-900">{new Date(request.created_at).toLocaleDateString()}</p>
                  </div>
                  
                  {request.due_date && (
                    <div>
                      <label className="text-sm font-medium text-gray-700">Due Date</label>
                      <p className="mt-1 text-gray-900">{new Date(request.due_date).toLocaleDateString()}</p>
                    </div>
                  )}
                </div>

                {request.email_recipients && request.email_recipients.length > 0 && (
                  <div>
                    <label className="text-sm font-medium text-gray-700">Email Recipients</label>
                    <div className="mt-1 flex flex-wrap gap-2">
                      {request.email_recipients.map((email, index) => (
                        <span key={index} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          <Mail className="w-3 h-3 mr-1" />
                          {email}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Incoming Request: Email Composition */}
            {request.type === RequestType.INCOMING && (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">Send Response</h2>
                
                {/* Drag & Drop Area */}
                <div
                  className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                    dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  <Upload className="mx-auto h-12 w-12 text-gray-400" />
                  <p className="mt-2 text-sm text-gray-600">
                    Drag and drop files here, or{' '}
                    <label className="cursor-pointer text-blue-600 hover:text-blue-500">
                      browse
                      <input
                        type="file"
                        multiple
                        onChange={handleFileInput}
                        className="hidden"
                      />
                    </label>
                  </p>
                </div>

                {/* Attachments List */}
                {attachments.length > 0 && (
                  <div className="mt-4">
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Attachments</h3>
                    <div className="space-y-2">
                      {attachments.map((file, index) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                          <div className="flex items-center">
                            <FileText className="w-4 h-4 text-gray-500 mr-2" />
                            <span className="text-sm text-gray-900">{file.name}</span>
                            <span className="text-xs text-gray-500 ml-2">({(file.size / 1024).toFixed(1)} KB)</span>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeAttachment(index)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Email Text */}
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Response Message
                  </label>
                  <Textarea
                    value={emailText}
                    onChange={(e) => setEmailText(e.target.value)}
                    rows={6}
                    placeholder="Type your response here..."
                  />
                </div>

                <div className="mt-4 flex justify-end">
                  <Button onClick={handleSendEmail} className="flex items-center">
                    <Send className="w-4 h-4 mr-2" />
                    Send Response
                  </Button>
                </div>
              </div>
            )}

            {/* Outgoing Request: Send Reminder */}
            {request.type === RequestType.OUTGOING && (
              <>
                <div className="bg-white shadow rounded-lg p-6">
                  <h2 className="text-lg font-medium text-gray-900 mb-4">Send Reminder</h2>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Additional Message (Optional)
                      </label>
                      <Textarea
                        value={reminderText}
                        onChange={(e) => setReminderText(e.target.value)}
                        rows={4}
                        placeholder="Add any additional message to the default reminder template..."
                      />
                    </div>

                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="autoReminder"
                        checked={autoReminderEnabled}
                        onChange={(e) => setAutoReminderEnabled(e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="autoReminder" className="ml-2 block text-sm text-gray-900">
                        Enable automatic reminders based on frequency setting ({request.reminder_frequency})
                      </label>
                    </div>

                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Preview of Default Message:</h4>
                      <div className="text-xs text-gray-600 whitespace-pre-line">
                        {`Dear ${request.client_name},

I hope this email finds you well. I wanted to follow up on our request regarding: "${request.title}".

Request Details:
- Description: ${request.description}
- Priority: ${request.priority}
- Created: ${new Date(request.created_at).toLocaleDateString()}
${request.due_date ? `- Due Date: ${new Date(request.due_date).toLocaleDateString()}` : ''}

${reminderText || 'We would appreciate an update on the status of this request at your earliest convenience.'}

Thank you for your attention to this matter.

Best regards,
Your Company`}
                      </div>
                    </div>

                    <div className="flex justify-end">
                      <Button onClick={handleSendReminder} className="flex items-center">
                        <Send className="w-4 h-4 mr-2" />
                        Send Reminder
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="bg-white shadow rounded-lg p-6">
                  <h2 className="text-lg font-medium text-gray-900 mb-4">Responses</h2>
                  
                  {responses.length === 0 ? (
                    <div className="text-center py-8">
                      <Mail className="mx-auto h-12 w-12 text-gray-400" />
                      <h3 className="mt-2 text-sm font-medium text-gray-900">No responses yet</h3>
                      <p className="mt-1 text-sm text-gray-500">
                        Responses from the client will appear here once they reply.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {responses.map((response, index) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-gray-900">{response.sender}</span>
                            <span className="text-xs text-gray-500">{response.date}</span>
                          </div>
                          <p className="text-gray-700">{response.message}</p>
                          {response.attachments && response.attachments.length > 0 && (
                            <div className="mt-2">
                              <p className="text-xs text-gray-500">Attachments: {response.attachments.join(', ')}</p>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={async () => {
                    try {
                      await requestsAPI.update(request.id, { status: RequestStatus.COMPLETED });
                      setRequest(prev => prev ? { ...prev, status: RequestStatus.COMPLETED } : null);
                    } catch (error) {
                      console.error('Error updating status:', error);
                      alert('Error updating status');
                    }
                  }}
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Mark as Completed
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={async () => {
                    try {
                      await requestsAPI.update(request.id, { status: RequestStatus.PENDING });
                      setRequest(prev => prev ? { ...prev, status: RequestStatus.PENDING } : null);
                    } catch (error) {
                      console.error('Error updating status:', error);
                      alert('Error updating status');
                    }
                  }}
                >
                  <Clock className="w-4 h-4 mr-2" />
                  Mark as Pending
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={async () => {
                    try {
                      await requestsAPI.update(request.id, { status: RequestStatus.OVERDUE });
                      setRequest(prev => prev ? { ...prev, status: RequestStatus.OVERDUE } : null);
                    } catch (error) {
                      console.error('Error updating status:', error);
                      alert('Error updating status');
                    }
                  }}
                >
                  <AlertCircle className="w-4 h-4 mr-2" />
                  Mark as Overdue
                </Button>
              </div>
            </div>

            {/* Request Info */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Request Information</h3>
              <div className="space-y-3 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Type:</span>
                  <span className="ml-2 text-gray-900 capitalize">{request.type}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Reminder:</span>
                  <span className="ml-2 text-gray-900 capitalize">{request.reminder_frequency}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Priority Flag:</span>
                  <span className="ml-2 text-gray-900">{request.is_priority ? 'Yes' : 'No'}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Last Updated:</span>
                  <span className="ml-2 text-gray-900">{new Date(request.updated_at).toLocaleDateString()}</span>
                </div>
              </div>
              
            </div>
          </div>
        </div>
      </div>
  );
}
