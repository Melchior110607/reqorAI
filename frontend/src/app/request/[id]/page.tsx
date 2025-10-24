'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Select } from '@/components/ui/Select';
import { requestsAPI } from '@/services/api';
import { RequestWithClient, RequestStatus, RequestType, RequestPriority } from '@/types';
import ReminderConfig from '../../../components/requests/ReminderConfig';
import TextType from '@/components/ui/TextType';
import { 
  ArrowLeft, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Mail,
  Send,
  Edit,
  Save,
  X,
  RefreshCw,
  Sparkles,
  MessageSquare,
  CheckCircle2,
  Bell,
  AlertTriangle,
  Paperclip,
  Upload,
  FileText,
  Trash2
} from 'lucide-react';

export default function RequestDetailPage() {
  const params = useParams();
  const router = useRouter();
  const requestId = parseInt(params.id as string);
  
  const [request, setRequest] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    status: '',
    priority: '',
    title: '',
    description: '',
    due_date: ''
  });
  
  // For draft response editing
  const [draftResponse, setDraftResponse] = useState('');
  const [regenerating, setRegenerating] = useState(false);
  const [sending, setSending] = useState(false);
  const [showTypingEffect, setShowTypingEffect] = useState(false);
  
  // For attachments (files to send to client)
  const [attachments, setAttachments] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  
  // For follow-up modal
  const [followUpModalOpen, setFollowUpModalOpen] = useState(false);
  const [followUpModalContent, setFollowUpModalContent] = useState<{
    type: 'client_reminder' | 'dissatisfaction' | null;
    message: string;
    date: string;
    count: number;
  }>({
    type: null,
    message: '',
    date: '',
    count: 0
  });

  // For follow-ups and conversation thread
  const [followUps, setFollowUps] = useState<any[]>([]);
  const [loadingFollowUps, setLoadingFollowUps] = useState(false);
  const [showConversationThread, setShowConversationThread] = useState(false);

  useEffect(() => {
    fetchRequest();
    fetchFollowUps();
  }, [requestId]);

  const fetchRequest = async () => {
    try {
      const data = await requestsAPI.getById(requestId);
      setRequest(data);
      setEditData({
        status: data.status,
        priority: data.priority,
        title: data.title,
        description: data.description,
        due_date: data.due_date || ''
      });
      setDraftResponse(data.draft_response || '');
    } catch (error) {
      console.error('Error fetching request:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFollowUps = async () => {
    setLoadingFollowUps(true);
    try {
      const data = await requestsAPI.getFollowUps(requestId);
      setFollowUps(data);
    } catch (error) {
      console.error('Error fetching follow-ups:', error);
    } finally {
      setLoadingFollowUps(false);
    }
  };

  // File attachment handlers
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    setAttachments(prev => [...prev, ...files]);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      setAttachments(prev => [...prev, ...files]);
    }
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const handleQuickStatusChange = async (newStatus: string) => {
    if (!request) return;
    
    try {
      await requestsAPI.update(request.id, {
        status: newStatus as RequestStatus
      });
      
      setRequest((prev: any) => prev ? {
        ...prev,
        status: newStatus as RequestStatus
      } : null);
    } catch (error) {
      console.error('Error updating status:', error);
      alert('Error updating status');
    }
  };

  const openFollowUpModal = (type: 'client_reminder' | 'dissatisfaction') => {
    if (!request) return;
    
    setFollowUpModalContent({
      type,
      message: request.latest_follow_up_message || 'No message available',
      date: request.latest_follow_up_at || '',
      count: request.follow_up_count || 0
    });
    setFollowUpModalOpen(true);
  };

  const handleStatusUpdate = async () => {
    if (!request) return;
    
    try {
      await requestsAPI.update(request.id, {
        status: editData.status as RequestStatus,
        priority: editData.priority as RequestPriority,
        title: editData.title,
        description: editData.description,
        due_date: editData.due_date || ""
      });
      
      setRequest((prev: any) => prev ? {
        ...prev,
        status: editData.status as RequestStatus,
        priority: editData.priority as RequestPriority,
        title: editData.title,
        description: editData.description,
        due_date: editData.due_date || null
      } : null);
      
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating request:', error);
      alert('Error updating request');
    }
  };

  const handleRegenerateDraft = async () => {
    if (!request) return;
    
    setRegenerating(true);
    setShowTypingEffect(true);
    try {
      const result = await requestsAPI.regenerateDraft(request.id);
      setDraftResponse(result.draft_response);
      setRequest((prev: any) => prev ? {
        ...prev,
        draft_response: result.draft_response,
        draft_generated_at: result.draft_generated_at
      } : null);
      // alert('✅ Draft response regenerated!');  // Removed to not interrupt typing effect
    } catch (error: any) {
      console.error('Error regenerating draft:', error);
      alert('Failed to regenerate draft: ' + (error.response?.data?.detail || error.message));
      setShowTypingEffect(false);
    } finally {
      setRegenerating(false);
      // Don't set showTypingEffect to false here - let it finish naturally
    }
  };

  const handleSendDraft = async () => {
    if (!request) return;
    
    const attachmentText = attachments.length > 0 
      ? ` with ${attachments.length} attachment${attachments.length > 1 ? 's' : ''}` 
      : '';
    
    if (!confirm(`Send this response to the client${attachmentText}?`)) {
      return;
    }
    
    setSending(true);
    try {
      const result = await requestsAPI.sendDraftResponse(request.id, attachments);
      alert(`✅ Email sent to ${result.to} via ${result.provider}!`);
      setAttachments([]); // Clear attachments after sending
      fetchRequest(); // Refresh to show updated status
    } catch (error: any) {
      console.error('Error sending draft:', error);
      alert('Failed to send email: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSending(false);
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

  const getStatusColor = (status: RequestStatus | string) => {
    switch (status) {
      case RequestStatus.PENDING:
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case RequestStatus.COMPLETED:
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-300';
      case RequestStatus.OVERDUE:
      case 'overdue':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
    );
  }

  if (!request) {
    return (
        <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900">Request not found</h2>
          <Button onClick={() => router.back()} className="mt-4">
            Go Back
          </Button>
        </div>
    );
  }

  return (
      <div className="px-4 py-6 sm:px-0">
        {/* Header */}
      <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => router.back()}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2 flex-wrap">
              <h1 className="text-3xl font-bold text-gray-900">{request.title}</h1>
              
              {/* Interactive Status Dropdown */}
              <div className="relative">
                <select
                  value={editData.status}
                  onChange={(e) => {
                    setEditData({ ...editData, status: e.target.value });
                    handleQuickStatusChange(e.target.value);
                  }}
                  className={`px-3 py-1 rounded-full text-sm font-medium cursor-pointer border-2 ${getStatusColor(editData.status)}`}
                >
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="overdue">Overdue</option>
                </select>
              </div>
              
              {/* Follow-up Badges */}
              {request.follow_up_type === 'client_reminder' && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-orange-100 text-orange-800 border-2 border-orange-300">
                  🔔 Client Reminder {request.follow_up_count > 0 && `(${request.follow_up_count})`}
                </span>
              )}
              {request.follow_up_type === 'dissatisfaction' && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800 border-2 border-red-300">
                  ⚠️ Dissatisfaction {request.follow_up_count > 0 && `(${request.follow_up_count})`}
                </span>
              )}
            </div>
            <p className="text-sm text-gray-600">
              Client: <span className="font-medium">{request.client_name}</span> ({request.client_company})
            </p>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Content (Details, Confirmation, Draft) */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Request Details */}
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-900">Details</h2>
              {!isEditing && (
                <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
                  <Edit className="w-4 h-4 mr-2" />
                  Edit
                </Button>
              )}
            </div>

            {isEditing ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                  <Input
                    value={editData.title}
                    onChange={(e) => setEditData({ ...editData, title: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                    <Textarea
                      value={editData.description}
                    onChange={(e) => setEditData({ ...editData, description: e.target.value })}
                    rows={6}
                  />
                </div>
                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setIsEditing(false)}>
                    <X className="w-4 h-4 mr-2" />
                    Cancel
                  </Button>
                  <Button onClick={handleStatusUpdate}>
                    <Save className="w-4 h-4 mr-2" />
                    Save Changes
                  </Button>
                </div>
              </div>
            ) : (
                  <div>
                <p className="text-gray-700 whitespace-pre-wrap">{request.description}</p>
                      </div>
                    )}
                  </div>

          {/* Confirmation Section (for OUTGOING requests) */}
          {request.type === RequestType.OUTGOING && request.confirmation_received && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <div className="flex items-center mb-4">
                <CheckCircle className="w-6 h-6 text-green-600 mr-2" />
                <h2 className="text-lg font-medium text-green-900">Confirmation Received</h2>
                </div>

              <div className="space-y-3">
                  <div>
                  <span className="text-sm font-medium text-green-800">Confirmed at:</span>
                  <span className="ml-2 text-sm text-green-700">
                    {new Date(request.confirmation_received_at).toLocaleString()}
                  </span>
                </div>

                {request.confirmation_details && (
                  <div>
                    <span className="text-sm font-medium text-green-800 block mb-2">Client Message:</span>
                    <div className="bg-white border border-green-200 rounded p-3 text-sm text-gray-700 whitespace-pre-wrap">
                      {request.confirmation_details}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* AI Draft Response Section (for INCOMING requests) */}
            {request.type === RequestType.INCOMING && (
              <div className="bg-white shadow rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <Sparkles className="w-5 h-5 text-purple-600 mr-2" />
                  <h2 className="text-lg font-medium text-gray-900">AI-Generated Draft Response</h2>
                </div>

                <div className="flex items-center space-x-2">
                          <Button
                    variant="outline"
                            size="sm"
                    onClick={handleRegenerateDraft}
                    disabled={regenerating}
                  >
                    <RefreshCw className={`w-4 h-4 mr-2 ${regenerating ? 'animate-spin' : ''}`} />
                    Regenerate
                  </Button>
                </div>
              </div>

              {request.draft_response ? (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                      Response (editable before sending)
                      </label>
                      {showTypingEffect && regenerating === false ? (
                        <div className="border border-gray-300 rounded-md p-3 bg-white min-h-[240px]">
                          <TextType
                            text={draftResponse}
                            typingSpeed={10}
                            showCursor={true}
                            cursorCharacter="|"
                            loop={false}
                            onSentenceComplete={() => {
                              // Wait a bit then hide typing effect to show editable textarea
                              setTimeout(() => {
                                setShowTypingEffect(false);
                              }, 1000);
                            }}
                            className="text-sm whitespace-pre-wrap text-black"
                          />
                        </div>
                      ) : showTypingEffect ? (
                        <div className="border border-gray-300 rounded-md p-3 bg-white min-h-[240px] flex items-center justify-center">
                          <div className="animate-pulse text-gray-500">Finalizing...</div>
                        </div>
                      ) : (
                        <Textarea
                          value={draftResponse}
                          onChange={(e) => setDraftResponse(e.target.value)}
                          rows={10}
                          className="font-mono text-sm"
                        />
                      )}
                    </div>

                  {/* Attachments Section */}
                  <div className="space-y-3">
                    <label className="block text-sm font-medium text-gray-700">
                      <Paperclip className="w-4 h-4 inline mr-1" />
                      Attachments (optional)
                    </label>
                    
                    {/* Drag & Drop Zone */}
                    <div
                      onDragEnter={handleDragEnter}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                      className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                        isDragging 
                          ? 'border-blue-500 bg-blue-50' 
                          : 'border-gray-300 bg-gray-50 hover:border-gray-400'
                      }`}
                    >
                      <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                      <p className="text-sm text-gray-600 mb-2">
                        Drag & drop files here, or click to browse
                      </p>
                      <input
                        type="file"
                        multiple
                        onChange={handleFileSelect}
                        className="hidden"
                        id="file-upload"
                      />
                      <label
                        htmlFor="file-upload"
                        className="inline-block px-4 py-2 text-sm bg-white border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50 text-gray-900"
                      >
                        Choose Files
                      </label>
                    </div>

                    {/* Attachment Preview List */}
                    {attachments.length > 0 && (
                      <div className="space-y-2">
                        {attachments.map((file, index) => (
                          <div
                            key={index}
                            className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg"
                          >
                            <div className="flex items-center space-x-3">
                              <FileText className="w-5 h-5 text-blue-500" />
                              <div>
                                <p className="text-sm font-medium text-gray-900">{file.name}</p>
                                <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                              </div>
                            </div>
                            <button
                              onClick={() => removeAttachment(index)}
                              className="text-red-500 hover:text-red-700 transition-colors"
                              title="Remove attachment"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {request.draft_generated_at && (
                    <p className="text-xs text-gray-500">
                      Generated: {new Date(request.draft_generated_at).toLocaleString()}
                    </p>
                  )}

                  {request.email_connection_email && (
                    <div className="bg-blue-50 border border-blue-200 rounded p-3">
                      <p className="text-sm text-blue-900">
                        <Mail className="w-4 h-4 inline mr-1" />
                        Will be sent from: <span className="font-medium">{request.email_connection_email}</span>
                      </p>
                    </div>
                  )}

                    <div className="flex justify-end">
                    <Button
                      onClick={handleSendDraft}
                      disabled={sending || !draftResponse}
                      className="bg-green-600 hover:bg-green-700"
                    >
                        <Send className="w-4 h-4 mr-2" />
                      {sending ? 'Sending...' : `Send Response to Client${attachments.length > 0 ? ` (${attachments.length} attachment${attachments.length > 1 ? 's' : ''})` : ''}`}
                      </Button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Sparkles className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                  <p>No draft response available yet</p>
                  <p className="text-sm mt-1">AI will generate one automatically or you can trigger manually</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column - Sidebar (Request Info & Auto-Reminder) */}
        <div className="lg:col-span-1 space-y-6">
          
          {/* Request Information */}
                <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Request Information</h3>
              {!isEditing && (
                <Button variant="ghost" size="sm" onClick={() => setIsEditing(true)}>
                  <Edit className="w-4 h-4" />
                </Button>
              )}
            </div>
            <div className="space-y-3">
              <div>
                <span className="text-sm font-medium text-gray-700">Type:</span>
                <span className="ml-2 text-sm text-gray-900 capitalize">{request.type}</span>
              </div>
              
              {/* Priority - Editable */}
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Priority:</label>
                {isEditing ? (
                  <select
                    value={editData.priority}
                    onChange={(e) => setEditData({ ...editData, priority: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                ) : (
                  <span className="text-sm text-gray-900 capitalize">{request.priority}</span>
                )}
              </div>
              
              {/* Due Date - Editable */}
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Due:</label>
                {isEditing ? (
                  <Input
                    type="datetime-local"
                    value={editData.due_date ? new Date(editData.due_date).toISOString().slice(0, 16) : ''}
                    onChange={(e) => setEditData({ ...editData, due_date: e.target.value })}
                  />
                ) : (
                  <span className="text-sm text-gray-900">
                    {request.due_date ? new Date(request.due_date).toLocaleString() : 'Not set'}
                  </span>
                )}
              </div>
              
              <div>
                <span className="text-sm font-medium text-gray-700">Created:</span>
                <span className="ml-2 text-sm text-gray-900">
                  {new Date(request.created_at).toLocaleDateString()}
                </span>
              </div>
              
              {request.email_connection_email && (
                <div>
                  <span className="text-sm font-medium text-gray-700">Email:</span>
                  <span className="ml-2 text-xs text-gray-900 break-all">{request.email_connection_email}</span>
                </div>
              )}
            </div>
          </div>

          {/* Client Responses (for INCOMING requests) */}
          {request.type === RequestType.INCOMING && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <MessageSquare className="w-5 h-5 mr-2 text-gray-600" />
                Client Responses
              </h3>

              {/* Confirmation Status */}
              <div className="space-y-3">
                {/* Confirmation takes priority - shows in green */}
                {request.confirmation_received ? (
                  <div 
                    onClick={() => {
                      if (request.confirmation_details) {
                        setFollowUpModalContent({
                          type: null,
                          message: request.confirmation_details,
                          date: request.confirmation_received_at || '',
                          count: 1
                        });
                        setFollowUpModalOpen(true);
                      }
                    }}
                    className="flex items-start space-x-3 p-4 bg-green-50 border-2 border-green-300 rounded-lg cursor-pointer hover:bg-green-100 transition-colors shadow-sm"
                  >
                    <CheckCircle2 className="w-6 h-6 text-green-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-base font-semibold text-green-900">✓ Client Confirmed</p>
                        {request.confirmation_received_at && (
                          <span className="text-xs text-green-700 font-medium">
                            {new Date(request.confirmation_received_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-green-700 mt-1">
                        Client is satisfied with the response
                      </p>
                      {request.confirmation_details && (
                        <div className="mt-2 p-2 bg-white border border-green-200 rounded text-xs text-gray-800">
                          {request.confirmation_details.length > 150 
                            ? request.confirmation_details.substring(0, 150) + '...' 
                            : request.confirmation_details}
                        </div>
                      )}
                      {request.confirmation_details && (
                        <p className="text-xs text-green-600 mt-2 font-semibold">Click to view full message →</p>
                      )}
                    </div>
                    </div>
                  ) : (
                  <>
                    {/* Show reminders/dissatisfaction only if NO confirmation */}
                    
                    {/* Client Reminders */}
                    {request.follow_up_type === 'client_reminder' && request.follow_up_count > 0 && (
                  <div 
                    onClick={() => openFollowUpModal('client_reminder')}
                    className="flex items-start space-x-3 p-3 bg-orange-50 border border-orange-200 rounded cursor-pointer hover:bg-orange-100 transition-colors"
                  >
                    <Bell className="w-5 h-5 text-orange-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-orange-900">Client Sent Reminders</p>
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-orange-100 text-orange-800">
                          {request.follow_up_count}x
                        </span>
                      </div>
                      {request.latest_follow_up_at && (
                        <p className="text-xs text-orange-600 mt-1">
                          Latest: {new Date(request.latest_follow_up_at).toLocaleDateString()}
                        </p>
                      )}
                      {request.latest_follow_up_message && (
                        <div className="mt-2 p-2 bg-white border border-orange-200 rounded text-xs text-gray-800">
                          {request.latest_follow_up_message.length > 200 
                            ? request.latest_follow_up_message.substring(0, 200) + '...' 
                            : request.latest_follow_up_message}
                        </div>
                      )}
                      <p className="text-xs text-orange-500 mt-2 font-medium">Click to view full message →</p>
                          </div>
                            </div>
                          )}

                {/* Dissatisfaction */}
                {request.follow_up_type === 'dissatisfaction' && request.follow_up_count > 0 && (
                  <div 
                    onClick={() => openFollowUpModal('dissatisfaction')}
                    className="flex items-start space-x-3 p-3 bg-red-50 border border-red-200 rounded cursor-pointer hover:bg-red-100 transition-colors"
                  >
                    <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-red-900">Needs More Information</p>
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800">
                          {request.follow_up_count}x
                        </span>
                      </div>
                      {request.latest_follow_up_at && (
                        <p className="text-xs text-red-600 mt-1">
                          Latest: {new Date(request.latest_follow_up_at).toLocaleDateString()}
                        </p>
                      )}
                      {request.latest_follow_up_message && (
                        <div className="mt-2 p-2 bg-white border border-red-200 rounded text-xs text-gray-800">
                          {request.latest_follow_up_message.length > 200 
                            ? request.latest_follow_up_message.substring(0, 200) + '...' 
                            : request.latest_follow_up_message}
                        </div>
                      )}
                      <p className="text-xs text-red-500 mt-2 font-medium">Click to view full message →</p>
                    </div>
                    </div>
                  )}

                    {/* No activity yet */}
                    {request.follow_up_type !== 'client_reminder' && 
                     request.follow_up_type !== 'dissatisfaction' && (
                      <div className="flex items-start space-x-3 p-3 bg-gray-50 border border-gray-200 rounded">
                        <Clock className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
                        <div className="flex-1">
                          <p className="text-sm text-gray-600">Awaiting client response</p>
                        </div>
                </div>
                    )}
              </>
            )}
          </div>
            </div>
          )}

          {/* Auto-Reminder System (for OUTGOING requests) */}
          {request.type === RequestType.OUTGOING && (
            <ReminderConfig
              requestId={request.id}
              initialConfig={{
                reminder_enabled: request.reminder_enabled || false,
                reminder_frequency: request.reminder_frequency || 'weekly',
                reminder_message: request.reminder_message || null,
                last_reminder_sent_at: request.last_reminder_sent_at || null,
                reminder_count: request.reminder_count || 0
              }}
              onUpdate={fetchRequest}
            />
          )}

          {/* Parent Request Link (For Follow-Ups) */}
          {request.is_follow_up && request.parent_request_id && (
            <div className="mt-6 bg-blue-50 shadow rounded-lg p-6 border-l-4 border-blue-500">
              <h3 className="text-sm font-medium text-blue-900 mb-2">
                ↩️ This is a follow-up request
              </h3>
                <Button
                  variant="outline"
                size="sm"
                onClick={() => router.push(`/request/${request.parent_request_id}`)}
              >
                View Original Request
                </Button>
            </div>
          )}
        </div>
      </div>

      {/* Follow-Up Modal */}
      {followUpModalOpen && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm"
          onClick={() => setFollowUpModalOpen(false)}
        >
          <div 
            className="bg-white rounded-lg shadow-2xl max-w-3xl w-full mx-4 max-h-[80vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className={`p-6 border-b ${
              followUpModalContent.type === 'client_reminder' 
                ? 'bg-orange-50 border-orange-200' 
                : followUpModalContent.type === 'dissatisfaction'
                ? 'bg-red-50 border-red-200'
                : 'bg-green-50 border-green-200'
            }`}>
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  {followUpModalContent.type === 'client_reminder' ? (
                    <Bell className="w-6 h-6 text-orange-600 mt-1" />
                  ) : followUpModalContent.type === 'dissatisfaction' ? (
                    <AlertTriangle className="w-6 h-6 text-red-600 mt-1" />
                  ) : (
                    <CheckCircle2 className="w-6 h-6 text-green-600 mt-1" />
                  )}
                  <div>
                    <h2 className={`text-xl font-semibold ${
                      followUpModalContent.type === 'client_reminder' 
                        ? 'text-orange-900' 
                        : followUpModalContent.type === 'dissatisfaction'
                        ? 'text-red-900'
                        : 'text-green-900'
                    }`}>
                      {followUpModalContent.type === 'client_reminder' 
                        ? 'Client Reminder' 
                        : followUpModalContent.type === 'dissatisfaction'
                        ? 'Client Dissatisfaction'
                        : 'Client Confirmation'}
                    </h2>
                    <div className="flex items-center space-x-3 mt-1">
                      {followUpModalContent.type && (
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold ${
                          followUpModalContent.type === 'client_reminder'
                            ? 'bg-orange-100 text-orange-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {followUpModalContent.count}x follow-up{followUpModalContent.count > 1 ? 's' : ''}
                        </span>
                      )}
                      {followUpModalContent.date && (
                        <span className="text-sm text-gray-600">
                          {new Date(followUpModalContent.date).toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => setFollowUpModalOpen(false)}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-200px)]">
              <div className="prose max-w-none">
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <p className="text-sm font-medium text-gray-700 mb-2">Client Message:</p>
                  <div className="text-gray-800 whitespace-pre-wrap">
                    {followUpModalContent.message}
                  </div>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-6 border-t bg-gray-50">
              <div className="flex justify-end">
                <Button
                  onClick={() => setFollowUpModalOpen(false)}
                  variant="outline"
                >
                  Close
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
      </div>
  );
}
