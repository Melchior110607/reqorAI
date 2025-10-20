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
  Sparkles
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
    try {
      const result = await requestsAPI.regenerateDraft(request.id);
      setDraftResponse(result.draft_response);
      setRequest((prev: any) => prev ? {
        ...prev,
        draft_response: result.draft_response,
        draft_generated_at: result.draft_generated_at
      } : null);
      alert('✅ Draft response regenerated!');
    } catch (error: any) {
      console.error('Error regenerating draft:', error);
      alert('Failed to regenerate draft: ' + (error.response?.data?.detail || error.message));
    } finally {
      setRegenerating(false);
    }
  };

  const handleSendDraft = async () => {
    if (!request) return;
    
    if (!confirm('Send this response to the client?')) {
      return;
    }
    
    setSending(true);
    try {
      const result = await requestsAPI.sendDraftResponse(request.id);
      alert(`✅ Email sent to ${result.to} via ${result.provider}!`);
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
                    <Textarea
                      value={draftResponse}
                      onChange={(e) => setDraftResponse(e.target.value)}
                      rows={10}
                      className="font-mono text-sm"
                    />
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
                      {sending ? 'Sending...' : 'Send Response to Client'}
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

          {/* Follow-Up Requests (Incoming Requests) */}
          {request.type === RequestType.INCOMING && followUps.length > 0 && (
            <div className="mt-6 bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <span className="mr-2">📋</span>
                Follow-Up Requests ({followUps.length})
              </h3>
              <div className="space-y-3">
                {followUps.map((followUp) => (
                  <div 
                    key={followUp.id}
                    className="border-l-4 border-blue-500 pl-4 py-2 hover:bg-gray-50 cursor-pointer"
                    onClick={() => router.push(`/request/${followUp.id}`)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <h4 className="text-sm font-medium text-gray-900">{followUp.title}</h4>
                          {followUp.follow_up_type === 'client_reminder' && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800">
                              🔔 Reminder
                            </span>
                          )}
                          {followUp.follow_up_type === 'dissatisfaction' && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                              ⚠️ Dissatisfied
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          Created: {new Date(followUp.created_at).toLocaleString()}
                        </p>
                      </div>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        followUp.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {followUp.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
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
    </div>
  );
}
