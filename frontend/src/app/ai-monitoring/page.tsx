'use client';

import { useState, useEffect } from 'react';
import { ProtectedLayout } from '@/components/layout/ProtectedLayout';
import { Button } from '@/components/ui/Button';
import { emailAPI } from '@/services/emailAPI';
import { InterceptedEmail, EmailClassification, ProcessingStatus } from '@/types/email';
import { 
  Brain, 
  Mail, 
  User, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  RefreshCw,
  Eye
} from 'lucide-react';

export default function AIMonitoringPage() {
  const [emails, setEmails] = useState<InterceptedEmail[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEmail, setSelectedEmail] = useState<InterceptedEmail | null>(null);
  const [classifying, setClassifying] = useState<number | null>(null);

  useEffect(() => {
    fetchEmails();
  }, []);

  const fetchEmails = async () => {
    try {
      const data = await emailAPI.getInterceptedEmails();
      setEmails(data);
    } catch (error) {
      console.error('Error fetching intercepted emails:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClassify = async (emailId: number) => {
    setClassifying(emailId);
    try {
      await emailAPI.classifyEmail(emailId);
      fetchEmails(); // Rafraîchir pour voir les résultats
    } catch (error) {
      console.error('Error classifying email:', error);
      alert('Failed to classify email');
    } finally {
      setClassifying(null);
    }
  };

  const getClassificationIcon = (classification: EmailClassification) => {
    switch (classification) {
      case EmailClassification.RESPONSE_TO_REQUEST:
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case EmailClassification.NEW_REQUEST:
        return <Mail className="w-4 h-4 text-blue-500" />;
      case EmailClassification.CONFIRMATION:
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case EmailClassification.CLIENT_REMINDER:
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case EmailClassification.DISSATISFACTION:
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case EmailClassification.MIXED:
        return <Brain className="w-4 h-4 text-purple-500" />;
      case EmailClassification.UNCLASSIFIED:
        return <XCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  const getClassificationColor = (classification: EmailClassification) => {
    switch (classification) {
      case EmailClassification.RESPONSE_TO_REQUEST:
        return 'bg-green-100 text-green-800';
      case EmailClassification.NEW_REQUEST:
        return 'bg-blue-100 text-blue-800';
      case EmailClassification.CONFIRMATION:
        return 'bg-green-100 text-green-800';
      case EmailClassification.CLIENT_REMINDER:
        return 'bg-yellow-100 text-yellow-800';
      case EmailClassification.DISSATISFACTION:
        return 'bg-red-100 text-red-800';
      case EmailClassification.MIXED:
        return 'bg-purple-100 text-purple-800';
      case EmailClassification.UNCLASSIFIED:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getProcessingIcon = (status: ProcessingStatus) => {
    switch (status) {
      case ProcessingStatus.PENDING:
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case ProcessingStatus.PROCESSING:
        return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />;
      case ProcessingStatus.COMPLETED:
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case ProcessingStatus.FAILED:
        return <XCircle className="w-4 h-4 text-red-500" />;
    }
  };

  const stats = {
    total: emails.length,
    processed: emails.filter(e => e.processing_status === ProcessingStatus.COMPLETED).length,
    pending: emails.filter(e => e.processing_status === ProcessingStatus.PENDING).length,
    matched: emails.filter(e => e.client_id !== null).length,
  };

  if (loading) {
    return (
      <ProtectedLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
        </div>
      </ProtectedLayout>
    );
  }

  return (
    <ProtectedLayout>
      <div className="px-4 py-6 sm:px-0">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">AI Email Monitoring</h1>
          <p className="mt-2 text-gray-600">
            Monitor intercepted emails and AI classification results
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Mail className="w-8 h-8 text-blue-500" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Emails</dt>
                    <dd className="text-lg font-medium text-gray-900">{stats.total}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Brain className="w-8 h-8 text-purple-500" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">AI Processed</dt>
                    <dd className="text-lg font-medium text-gray-900">{stats.processed}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <User className="w-8 h-8 text-green-500" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Client Matched</dt>
                    <dd className="text-lg font-medium text-gray-900">{stats.matched}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Clock className="w-8 h-8 text-yellow-500" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Pending</dt>
                    <dd className="text-lg font-medium text-gray-900">{stats.pending}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Emails List */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-medium text-gray-900">Intercepted Emails</h2>
              <Button onClick={fetchEmails} variant="outline" size="sm">
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
          
          {emails.length === 0 ? (
            <div className="text-center py-12">
              <Mail className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No emails intercepted yet</h3>
              <p className="mt-1 text-sm text-gray-500">
                Connect your email accounts and sync to see intercepted emails here.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {emails.map((email) => (
                <div key={email.id} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h4 className="text-sm font-medium text-gray-900">
                          {email.subject}
                        </h4>
                        {email.client_name && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                            {email.client_name}
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-sm text-gray-600">
                        From: {email.sender_name || email.sender_email}
                      </p>
                      <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                        <span>Received: {new Date(email.email_received_at).toLocaleString()}</span>
                        <span>Confidence: {(email.confidence_score * 100).toFixed(0)}%</span>
                        {email.ai_confidence > 0 && (
                          <span>AI Confidence: {(email.ai_confidence * 100).toFixed(0)}%</span>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center space-x-2">
                        {getProcessingIcon(email.processing_status)}
                        <span className="text-xs text-gray-500">{email.processing_status}</span>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        {getClassificationIcon(email.ai_classification)}
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getClassificationColor(email.ai_classification)}`}>
                          {email.ai_classification.replace('_', ' ')}
                        </span>
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        {email.processing_status === ProcessingStatus.PENDING && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleClassify(email.id)}
                            disabled={classifying === email.id}
                            className="text-blue-600 hover:text-blue-700"
                          >
                            <Brain className={`w-4 h-4 ${classifying === email.id ? 'animate-pulse' : ''}`} />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedEmail(email)}
                          className="text-gray-600 hover:text-gray-700"
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                  
                  {email.ai_reasoning && (
                    <div className="mt-3 p-3 bg-gray-50 rounded-md">
                      <p className="text-xs text-gray-600">
                        <strong>AI Reasoning:</strong> {email.ai_reasoning}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Email Detail Modal */}
        {selectedEmail && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900">Email Details</h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedEmail(null)}
                  >
                    <XCircle className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              
              <div className="px-6 py-4 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700">From</label>
                    <p className="text-sm text-gray-900">{selectedEmail.sender_name || selectedEmail.sender_email}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Client Match</label>
                    <p className="text-sm text-gray-900">
                      {selectedEmail.client_name ? 
                        `${selectedEmail.client_name} (${selectedEmail.client_company})` : 
                        'No match found'
                      }
                    </p>
                  </div>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-700">Subject</label>
                  <p className="text-sm text-gray-900">{selectedEmail.subject}</p>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-700">Body</label>
                  <div className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md max-h-60 overflow-y-auto whitespace-pre-wrap">
                    {selectedEmail.body}
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700">AI Classification</label>
                    <div className="flex items-center space-x-2 mt-1">
                      {getClassificationIcon(selectedEmail.ai_classification)}
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getClassificationColor(selectedEmail.ai_classification)}`}>
                        {selectedEmail.ai_classification.replace('_', ' ')}
                      </span>
                      <span className="text-xs text-gray-500">
                        ({(selectedEmail.ai_confidence * 100).toFixed(0)}% confidence)
                      </span>
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-gray-700">Processing Status</label>
                    <div className="flex items-center space-x-2 mt-1">
                      {getProcessingIcon(selectedEmail.processing_status)}
                      <span className="text-sm text-gray-900">{selectedEmail.processing_status}</span>
                    </div>
                  </div>
                </div>
                
                {selectedEmail.ai_reasoning && (
                  <div>
                    <label className="text-sm font-medium text-gray-700">AI Reasoning</label>
                    <p className="text-sm text-gray-900 bg-blue-50 p-3 rounded-md">
                      {selectedEmail.ai_reasoning}
                    </p>
                  </div>
                )}
                
                {selectedEmail.related_request_ids && selectedEmail.related_request_ids.length > 0 && (
                  <div>
                    <label className="text-sm font-medium text-gray-700">Related Requests</label>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {selectedEmail.related_request_ids.map((requestId) => (
                        <span key={requestId} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                          Request #{requestId}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </ProtectedLayout>
  );
}
