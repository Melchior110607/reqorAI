'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { emailAPI } from '@/services/emailAPI';
import { EmailConnection, EmailProvider, ConnectionStatus } from '@/types/email';
import { 
  Mail, 
  Plus, 
  Trash2, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Clock,
  ExternalLink
} from 'lucide-react';

export default function EmailSettingsPage() {
  const [connections, setConnections] = useState<EmailConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState<number | null>(null);

  useEffect(() => {
    fetchConnections();
  }, []);

  const fetchConnections = async () => {
    try {
      const data = await emailAPI.getConnections();
      setConnections(data);
    } catch (error) {
      console.error('Error fetching connections:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (provider: EmailProvider) => {
    try {
      const { auth_url } = await emailAPI.getAuthUrl(provider);
      
      // Ouvrir dans la même fenêtre pour éviter les problèmes de popup
      window.location.href = auth_url;
      
    } catch (error: any) {
      console.error('Error connecting email:', error);
      alert(`Failed to connect ${provider} account: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleSync = async (connectionId: number) => {
    setSyncing(connectionId);
    try {
      const result = await emailAPI.syncEmails(connectionId);
      alert(result.message);
      fetchConnections();
    } catch (error) {
      console.error('Error syncing emails:', error);
      alert('Failed to sync emails');
    } finally {
      setSyncing(null);
    }
  };

  const handleDelete = async (connectionId: number) => {
    if (!confirm('Are you sure you want to delete this email connection?')) return;
    
    try {
      await emailAPI.deleteConnection(connectionId);
      fetchConnections();
    } catch (error) {
      console.error('Error deleting connection:', error);
      alert('Failed to delete connection');
    }
  };

  const getStatusIcon = (status: ConnectionStatus) => {
    switch (status) {
      case ConnectionStatus.ACTIVE:
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case ConnectionStatus.ERROR:
        return <XCircle className="w-5 h-5 text-red-500" />;
      case ConnectionStatus.EXPIRED:
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case ConnectionStatus.INACTIVE:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: ConnectionStatus) => {
    switch (status) {
      case ConnectionStatus.ACTIVE:
        return 'bg-green-100 text-green-800';
      case ConnectionStatus.ERROR:
        return 'bg-red-100 text-red-800';
      case ConnectionStatus.EXPIRED:
        return 'bg-yellow-100 text-yellow-800';
      case ConnectionStatus.INACTIVE:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getProviderIcon = (provider: EmailProvider) => {
    switch (provider) {
      case EmailProvider.GMAIL:
        return '📧'; // Gmail icon
      case EmailProvider.OUTLOOK:
        return '📮'; // Outlook icon
    }
  };

  if (loading) {
    return (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
        </div>
    );
  }

  return (
      <div className="px-4 py-6 sm:px-0">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Email Settings</h1>
          <p className="mt-2 text-gray-600">
            Connect your email accounts to automatically process B2B requests
          </p>
        </div>

        {/* Add New Connection */}
        <div className="bg-white shadow rounded-lg p-6 mb-8">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Connect Email Account</h2>
          <div className="flex space-x-4">
            <Button
              onClick={() => handleConnect(EmailProvider.GMAIL)}
              className="flex items-center"
            >
              <span className="mr-2">📧</span>
              Connect Gmail
            </Button>
            <Button
              onClick={() => handleConnect(EmailProvider.OUTLOOK)}
              variant="outline"
              className="flex items-center"
            >
              <span className="mr-2">📮</span>
              Connect Outlook
            </Button>
          </div>
        </div>

        {/* Connected Accounts */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Connected Accounts</h2>
          </div>
          
          {connections.length === 0 ? (
            <div className="text-center py-12">
              <Mail className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No email accounts connected</h3>
              <p className="mt-1 text-sm text-gray-500">
                Connect your Gmail or Outlook account to start processing emails automatically.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {connections.map((connection) => (
                <div key={connection.id} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="text-2xl">
                        {getProviderIcon(connection.provider)}
                      </div>
                      <div>
                        <h3 className="text-sm font-medium text-gray-900">
                          {connection.email_address}
                        </h3>
                        <p className="text-sm text-gray-500 capitalize">
                          {connection.provider}
                        </p>
                        {connection.last_sync && (
                          <p className="text-xs text-gray-400">
                            Last sync: {new Date(connection.last_sync).toLocaleString()}
                          </p>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(connection.status)}
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(connection.status)}`}>
                          {connection.status}
                        </span>
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleSync(connection.id)}
                          disabled={syncing === connection.id}
                          className="text-blue-600 hover:text-blue-700"
                        >
                          <RefreshCw className={`w-4 h-4 ${syncing === connection.id ? 'animate-spin' : ''}`} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(connection.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-blue-900 mb-2">How it works</h3>
          <div className="text-sm text-blue-800 space-y-2">
            <p>1. <strong>Connect your email:</strong> Authorize access to your Gmail or Outlook account</p>
            <p>2. <strong>Automatic processing:</strong> Incoming emails are automatically matched to your clients</p>
            <p>3. <strong>AI classification:</strong> Our AI analyzes emails and categorizes them (responses, new requests, etc.)</p>
            <p>4. <strong>Smart actions:</strong> Requests are automatically updated based on email content</p>
          </div>
        </div>
      </div>
  );
}
