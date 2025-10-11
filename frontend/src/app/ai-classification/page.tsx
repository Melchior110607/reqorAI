'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Brain, CheckCircle, XCircle, Clock, ChevronDown, ChevronUp, Zap, AlertCircle } from 'lucide-react';
import { emailAPI } from '@/services/emailAPI';
import Link from 'next/link';

interface InterceptedEmail {
  id: number;
  sender_email: string;
  sender_name: string;
  subject: string;
  email_received_at: string;
  processing_status: string;
  ai_classification?: string;
  ai_confidence?: number;
  ai_reasoning?: string;
  related_request_ids?: number[] | string;
  client_id?: number;
  client_name?: string;
  client_company?: string;
}

export default function AIClassificationPage() {
  const [emails, setEmails] = useState<InterceptedEmail[]>([]);
  const [loading, setLoading] = useState(true);
  const [classifying, setClassifying] = useState(false);
  const [classifyingAll, setClassifyingAll] = useState(false);
  const [expandedEmail, setExpandedEmail] = useState<number | null>(null);
  const [filter, setFilter] = useState<string>('all'); // all, pending, completed, failed

  useEffect(() => {
    fetchEmails();
  }, []);

  const fetchEmails = async () => {
    try {
      setLoading(true);
      const data = await emailAPI.getInterceptedEmails();
      setEmails(data);
    } catch (error) {
      console.error('Error fetching emails:', error);
    } finally {
      setLoading(false);
    }
  };

  const classifyEmail = async (emailId: number) => {
    try {
      setClassifying(true);
      await emailAPI.classifyEmail(emailId);
      await fetchEmails(); // Refresh
    } catch (error) {
      console.error('Error classifying email:', error);
      alert('Erreur lors de la classification');
    } finally {
      setClassifying(false);
    }
  };

  const classifyAllPending = async () => {
    if (!confirm('Classifier tous les emails en attente ? Cela peut prendre quelques minutes.')) {
      return;
    }

    try {
      setClassifyingAll(true);
      const result = await emailAPI.classifyAllEmails();
      alert(`✅ ${result.classified} emails classifiés, ${result.failed} échecs`);
      await fetchEmails(); // Refresh
    } catch (error) {
      console.error('Error classifying all emails:', error);
      alert('Erreur lors de la classification');
    } finally {
      setClassifyingAll(false);
    }
  };

  const getClassificationBadge = (classification?: string) => {
    if (!classification || classification === 'unclassified') {
      return <span className="px-2 py-1 text-xs rounded bg-gray-200 text-gray-700">Unclassified</span>;
    }

    const badges: Record<string, { color: string; label: string }> = {
      'response_to_request': { color: 'bg-blue-100 text-blue-800', label: '💬 Response to Request' },
      'new_request': { color: 'bg-green-100 text-green-800', label: '📥 New Request' },
      'confirmation': { color: 'bg-purple-100 text-purple-800', label: '✅ Confirmation' },
      'client_reminder': { color: 'bg-yellow-100 text-yellow-800', label: '⏰ Client Reminder' },
      'dissatisfaction': { color: 'bg-red-100 text-red-800', label: '😠 Dissatisfaction' },
      'mixed': { color: 'bg-orange-100 text-orange-800', label: '🔀 Mixed' },
    };

    const badge = badges[classification] || { color: 'bg-gray-200 text-gray-700', label: classification };
    return <span className={`px-2 py-1 text-xs rounded ${badge.color}`}>{badge.label}</span>;
  };

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'processing':
        return <Clock className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-400" />;
    }
  };

  const parseRelatedRequests = (jsonString?: string): number[] => {
    if (!jsonString) return [];
    try {
      return JSON.parse(jsonString);
    } catch {
      return [];
    }
  };

  const filteredEmails = emails.filter(email => {
    // Filtrer SEULEMENT les emails avec un client (sinon impossible de classifier)
    if (!email.client_id) return false;
    
    if (filter === 'all') return true;
    if (filter === 'pending') return email.processing_status === 'pending';
    if (filter === 'completed') return email.processing_status === 'completed';
    if (filter === 'failed') return email.processing_status === 'failed';
    return true;
  });

  const pendingCount = emails.filter(e => e.client_id && e.processing_status === 'pending').length;
  const completedCount = emails.filter(e => e.client_id && e.processing_status === 'completed').length;
  const failedCount = emails.filter(e => e.client_id && e.processing_status === 'failed').length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">🤖 Classification IA</h1>
          <p className="mt-2 text-gray-600">
            Analyse automatique des emails avec GPT-4o
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Button onClick={fetchEmails} variant="outline">
            Rafraîchir
          </Button>
          {pendingCount > 0 && (
            <Button 
              onClick={classifyAllPending} 
              disabled={classifyingAll}
              className="bg-purple-600 hover:bg-purple-700"
            >
              <Zap className="w-4 h-4 mr-2" />
              {classifyingAll ? 'Classification...' : `Classifier ${pendingCount} emails`}
            </Button>
          )}
        </div>
      </div>

      {/* Info Box */}
      <div className="mb-8 bg-purple-50 border-2 border-purple-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-purple-800 mb-3">ℹ️ How it works</h2>
        <ul className="list-disc list-inside space-y-2 text-purple-900">
          <li><strong>Displayed emails</strong>: Only those <u>matched to a client</u> (impossible to classify without context)</li>
          <li><strong>Sequential</strong>: Emails are analyzed one by one by OpenAI GPT-4o</li>
          <li><strong>Context</strong>: AI receives all requests (incoming/outgoing) from the client</li>
          <li><strong>Classifications</strong>: Response, New Request, Confirmation, Reminder, Dissatisfaction, Mixed</li>
          <li><strong>No duplicates</strong>: Only unique emails (via message_id) are processed</li>
        </ul>
      </div>

      {/* Debug Info */}
      {emails.length > 0 && (
        <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <p className="text-sm text-gray-700">
            📊 <strong>Total intercepted emails:</strong> {emails.length} | 
            <strong className="ml-2">With client:</strong> {emails.filter(e => e.client_id).length} | 
            <strong className="ml-2">Without client:</strong> {emails.filter(e => !e.client_id).length}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            💡 Emails without client are not displayed here (go to "AI Debug" to see them)
          </p>
        </div>
      )}

      {/* Filters */}
      <div className="mb-6 flex items-center space-x-2">
        <Button
          variant={filter === 'all' ? 'primary' : 'outline'}
          size="sm"
          onClick={() => setFilter('all')}
        >
          Tous ({emails.length})
        </Button>
        <Button
          variant={filter === 'pending' ? 'primary' : 'outline'}
          size="sm"
          onClick={() => setFilter('pending')}
        >
          <Clock className="w-4 h-4 mr-1" />
          En attente ({pendingCount})
        </Button>
        <Button
          variant={filter === 'completed' ? 'primary' : 'outline'}
          size="sm"
          onClick={() => setFilter('completed')}
        >
          <CheckCircle className="w-4 h-4 mr-1" />
          Classifiés ({completedCount})
        </Button>
        {failedCount > 0 && (
          <Button
            variant={filter === 'failed' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setFilter('failed')}
          >
            <XCircle className="w-4 h-4 mr-1" />
            Échecs ({failedCount})
          </Button>
        )}
      </div>

      {/* Emails List */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        {filteredEmails.length === 0 ? (
          <div className="text-center py-12">
            <Brain className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No emails to display</h3>
            <p className="mt-1 text-sm text-gray-500">
              {filter === 'pending' ? 'All emails have been classified!' : 'Change filter or sync your emails.'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredEmails.map((email) => {
              const relatedRequests = parseRelatedRequests(email.related_request_ids);
              const isExpanded = expandedEmail === email.id;

              return (
                <div key={email.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        {getStatusIcon(email.processing_status)}
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="font-medium text-gray-900">{email.sender_name || email.sender_email}</span>
                            {email.client_company && (
                              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                                {email.client_company}
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-600">{email.sender_email}</p>
                        </div>
                      </div>

                      <h3 className="text-sm font-semibold text-gray-800 mb-2">{email.subject}</h3>

                      <div className="flex items-center space-x-4 text-xs text-gray-500 mb-3">
                        <span>{new Date(email.email_received_at).toLocaleString()}</span>
                        {email.processing_status?.toLowerCase() === 'completed' && email.ai_classification && (
                          <>
                            <span>•</span>
                            {getClassificationBadge(email.ai_classification)}
                            {email.ai_confidence && (
                              <span className="flex items-center space-x-1">
                                <span>Confiance:</span>
                                <div className="w-20 bg-gray-200 rounded-full h-2">
                                  <div
                                    className="bg-green-500 h-2 rounded-full"
                                    style={{ width: `${email.ai_confidence * 100}%` }}
                                  />
                                </div>
                                <span>{Math.round(email.ai_confidence * 100)}%</span>
                              </span>
                            )}
                          </>
                        )}
                      </div>

                      {/* Expanded content */}
                      {isExpanded && email.processing_status?.toLowerCase() === 'completed' && (
                        <div className="mt-4 space-y-3">
                          {email.ai_reasoning && (
                            <div className="bg-gray-50 rounded-lg p-4">
                              <h4 className="text-sm font-medium text-gray-700 mb-2">🧠 Raisonnement de l'IA :</h4>
                              <p className="text-sm text-gray-600 whitespace-pre-wrap">{email.ai_reasoning}</p>
                            </div>
                          )}

                          {relatedRequests.length > 0 && (
                            <div className="bg-blue-50 rounded-lg p-4">
                              <h4 className="text-sm font-medium text-blue-700 mb-2">🔗 Demandes liées :</h4>
                              <div className="space-y-1">
                                {relatedRequests.map((requestId) => (
                                  <Link
                                    key={requestId}
                                    href={`/request/${requestId}`}
                                    className="text-sm text-blue-600 hover:text-blue-800 hover:underline block"
                                  >
                                    → Voir la demande #{requestId}
                                  </Link>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="ml-4 flex flex-col items-end space-y-2">
                      {email.processing_status?.toLowerCase() === 'pending' && email.client_id && (
                        <Button
                          size="sm"
                          onClick={() => classifyEmail(email.id)}
                          disabled={classifying}
                        >
                          <Brain className="w-4 h-4 mr-1" />
                          Classifier
                        </Button>
                      )}

                      {email.processing_status?.toLowerCase() === 'completed' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setExpandedEmail(isExpanded ? null : email.id)}
                        >
                          {isExpanded ? (
                            <>
                              <ChevronUp className="w-4 h-4" />
                              Masquer
                            </>
                          ) : (
                            <>
                              <ChevronDown className="w-4 h-4" />
                              Détails
                            </>
                          )}
                        </Button>
                      )}

                      {!email.client_id && (
                        <span className="text-xs text-gray-500 italic">Aucun client</span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

