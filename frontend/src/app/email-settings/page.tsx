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

  const getProviderIcon =  (provider : EmailProvider) => {
    if (provider == EmailProvider.GMAIL) return (
      <svg className="w-5 h-5 mr-3" viewBox="0 0 23 23">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
    )
    else return (
      <svg className="w-5 h-5 mr-3" viewBox="0 0 23 23">
                    <path fill="#f3f3f3" d="M0 0h23v23H0z"/>
                    <path fill="#f35325" d="M1 1h10v10H1z"/>
                    <path fill="#5b722aff" d="M12 1h10v10H12z"/>
                    <path fill="#05a6f0" d="M1 12h10v10H1z"/>
                    <path fill="#ffba08" d="M12 12h10v10H12z"/>
                  </svg>
    )

    
  } 

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
              variant ="outline"
              className="flex items-center"
            >
              <>
                  <svg className="w-5 h-5 mr-3" viewBox="0 0 23 23">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Continue with Google
                </>
            </Button>
            <Button
              onClick={() => handleConnect(EmailProvider.OUTLOOK)}
              variant="outline"
              className="flex items-center"
            >
              <>
                  <svg className="w-5 h-5 mr-3" viewBox="0 0 23 23">
                    <path fill="#f3f3f3" d="M0 0h23v23H0z"/>
                    <path fill="#f35325" d="M1 1h10v10H1z"/>
                    <path fill="#5b722aff" d="M12 1h10v10H12z"/>
                    <path fill="#05a6f0" d="M1 12h10v10H1z"/>
                    <path fill="#ffba08" d="M12 12h10v10H12z"/>
                  </svg>
                  Connect Outlook
                </>
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
                        <svg className="w-5 h-5 mr-3" viewBox="0 0 23 23">
                        {getProviderIcon(connection.provider)}
                  </svg>
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
