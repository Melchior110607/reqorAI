'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { emailAPI } from '@/services/emailAPI';
import { 
  Mail, 
  RefreshCw,
  Eye,
  XCircle,
  Calendar,
  User as UserIcon
} from 'lucide-react';

interface RawEmail {
  id: number;
  sender_email: string;
  sender_name?: string;
  subject: string;
  body: string;
  email_received_at: string;
  created_at: string;
}

export default function AIMonitoringDebugPage() {
  const [emails, setEmails] = useState<RawEmail[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<RawEmail | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

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

  const syncProvider = async (provider: string, providerName: string) => {
    try {
      setSyncing(true);
      await emailAPI.syncEmails(provider);
      // Attendre 2 secondes puis recharger
      setTimeout(() => {
        fetchEmails();
      }, 2000);
      alert(`✅ Synchronisation ${providerName} lancée! Les emails vont apparaître dans 2 secondes.`);
    } catch (error: any) {
      console.error(`Error syncing ${providerName}:`, error);
      alert('❌ Erreur: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSyncing(false);
    }
  };

  const syncAll = async () => {
    try {
      setSyncing(true);
      // Synchroniser Gmail et Outlook en parallèle
      await Promise.all([
        emailAPI.syncEmails('gmail').catch(e => console.log('Gmail sync skipped:', e.message)),
        emailAPI.syncEmails('outlook').catch(e => console.log('Outlook sync skipped:', e.message))
      ]);
      // Attendre 2 secondes puis recharger
      setTimeout(() => {
        fetchEmails();
      }, 2000);
      alert('✅ Synchronisation de tous les comptes lancée! Les emails vont apparaître dans 2 secondes.');
    } catch (error: any) {
      console.error('Error syncing all:', error);
      alert('❌ Erreur: ' + error.message);
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">📧 Email Interception Debug</h1>
            <p className="mt-2 text-gray-600">
              Vérification que les emails Gmail sont bien interceptés par le webhook
            </p>
          </div>
          <div className="flex space-x-2">
            <Button 
              onClick={syncAll} 
              disabled={syncing} 
              className="bg-purple-600 hover:bg-purple-700 text-white"
            >
              <Mail className={`w-4 h-4 mr-2 ${syncing ? 'animate-bounce' : ''}`} />
              {syncing ? 'Syncing...' : '🔄 Sync All'}
            </Button>
            <Button 
              onClick={() => syncProvider('gmail', 'Gmail')} 
              disabled={syncing} 
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              <Mail className={`w-4 h-4 mr-2 ${syncing ? 'animate-bounce' : ''}`} />
              Gmail
            </Button>
            <Button 
              onClick={() => syncProvider('outlook', 'Outlook')} 
              disabled={syncing} 
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Mail className={`w-4 h-4 mr-2 ${syncing ? 'animate-bounce' : ''}`} />
              Outlook
            </Button>
            <Button onClick={fetchEmails} variant="outline">
              <RefreshCw className="w-4 h-4 mr-2" />
              Rafraîchir
            </Button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="mb-8 bg-blue-50 border-2 border-blue-200 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-blue-600 font-medium">Total d'emails interceptés</p>
            <p className="text-4xl font-bold text-blue-900 mt-2">{emails.length}</p>
          </div>
          <Mail className="w-16 h-16 text-blue-400" />
        </div>
      </div>

      {/* Alert si pas d'emails */}
      {emails.length === 0 && (
        <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start">
            <Mail className="w-5 h-5 text-yellow-600 mt-0.5 mr-3" />
            <div className="flex-1">
              <h3 className="text-sm font-medium text-yellow-800">Aucun email intercepté</h3>
              <p className="text-sm text-yellow-700 mt-1">
                Le webhook Gmail n'a pas encore intercepté d'emails. 
                Envoyez-vous un email de test ou attendez qu'un email arrive sur votre compte Gmail connecté.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Liste des emails */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <h2 className="text-lg font-semibold text-gray-900">
            Emails interceptés ({emails.length})
          </h2>
        </div>

        {emails.length > 0 ? (
          <div className="divide-y divide-gray-200">
            {emails.map((email) => (
              <div 
                key={email.id} 
                className="px-6 py-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    {/* From */}
                    <div className="flex items-center space-x-2 mb-2">
                      <UserIcon className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {email.sender_name || 'Inconnu'}
                        </p>
                        <p className="text-xs text-gray-500 truncate">
                          {email.sender_email}
                        </p>
                      </div>
                    </div>

                    {/* Subject */}
                    <div className="flex items-start space-x-2 mb-2">
                      <Mail className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
                      <p className="text-sm text-gray-900 font-medium">
                        {email.subject || '(Pas de sujet)'}
                      </p>
                    </div>

                    {/* Body preview */}
                    <div className="ml-6 mb-2">
                      <p className="text-sm text-gray-600 line-clamp-2">
                        {email.body.substring(0, 200)}
                        {email.body.length > 200 && '...'}
                      </p>
                    </div>

                    {/* Date */}
                    <div className="flex items-center space-x-2 ml-6">
                      <Calendar className="w-4 h-4 text-gray-400" />
                      <p className="text-xs text-gray-500">
                        Reçu le {new Date(email.email_received_at).toLocaleString('fr-FR', {
                          dateStyle: 'medium',
                          timeStyle: 'short'
                        })}
                      </p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="ml-4 flex-shrink-0">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedEmail(email)}
                      className="text-blue-600 hover:text-blue-700"
                    >
                      <Eye className="w-5 h-5" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Mail className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Aucun email</h3>
            <p className="mt-1 text-sm text-gray-500">
              Les emails interceptés apparaîtront ici.
            </p>
          </div>
        )}
      </div>

      {/* Modal détails email */}
      {selectedEmail && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 sticky top-0">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-gray-900">Détails de l'email</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedEmail(null)}
                >
                  <XCircle className="w-5 h-5" />
                </Button>
              </div>
            </div>
            
            {/* Content */}
            <div className="px-6 py-6 space-y-6">
              {/* From */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-xs font-medium text-blue-900 mb-2">DE</p>
                <p className="text-sm font-semibold text-gray-900">
                  {selectedEmail.sender_name || 'Inconnu'}
                </p>
                <p className="text-sm text-gray-600">{selectedEmail.sender_email}</p>
              </div>

              {/* Subject */}
              <div>
                <p className="text-xs font-medium text-gray-500 mb-2">SUJET</p>
                <p className="text-base font-semibold text-gray-900">
                  {selectedEmail.subject || '(Pas de sujet)'}
                </p>
              </div>

              {/* Date */}
              <div>
                <p className="text-xs font-medium text-gray-500 mb-2">DATE DE RÉCEPTION</p>
                <p className="text-sm text-gray-900">
                  {new Date(selectedEmail.email_received_at).toLocaleString('fr-FR', {
                    dateStyle: 'full',
                    timeStyle: 'medium'
                  })}
                </p>
              </div>

              {/* Body */}
              <div>
                <p className="text-xs font-medium text-gray-500 mb-2">CONTENU</p>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 max-h-96 overflow-y-auto">
                  <pre className="text-sm text-gray-900 whitespace-pre-wrap font-sans">
                    {selectedEmail.body}
                  </pre>
                </div>
              </div>

              {/* Debug info */}
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <p className="text-xs font-medium text-purple-900 mb-2">DEBUG INFO</p>
                <div className="space-y-1 text-xs text-purple-800">
                  <p><span className="font-medium">ID:</span> {selectedEmail.id}</p>
                  <p><span className="font-medium">Créé le:</span> {new Date(selectedEmail.created_at).toLocaleString('fr-FR')}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-8 bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h3 className="text-sm font-bold text-gray-900 mb-3">📝 Comment tester</h3>
        <ol className="space-y-2 text-sm text-gray-700">
          <li className="flex items-start">
            <span className="font-bold mr-2">1.</span>
            <span>Envoyez-vous un email sur votre compte Gmail connecté</span>
          </li>
          <li className="flex items-start">
            <span className="font-bold mr-2">2.</span>
            <span>Attendez quelques secondes (le webhook peut prendre 10-30 secondes)</span>
          </li>
          <li className="flex items-start">
            <span className="font-bold mr-2">3.</span>
            <span>Cliquez sur "Rafraîchir" pour recharger la liste</span>
          </li>
          <li className="flex items-start">
            <span className="font-bold mr-2">4.</span>
            <span>L'email devrait apparaître dans la liste ci-dessus</span>
          </li>
        </ol>
      </div>
    </div>
  );
}
