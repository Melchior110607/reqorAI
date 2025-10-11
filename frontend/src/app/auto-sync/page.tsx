'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { RefreshCw, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import axios from 'axios';

interface SyncLog {
  id: number;
  sync_type: string;
  total_synced: number;
  total_duplicates: number;
  connections_processed: number;
  details: Array<{
    connection_id: number;
    email: string;
    provider: string;
    synced?: number;
    duplicates?: number;
    error?: string;
  }>;
  error?: string;
  created_at: string;
}

export default function AutoSyncPage() {
  const [logs, setLogs] = useState<SyncLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedLog, setExpandedLog] = useState<number | null>(null);

  useEffect(() => {
    fetchLogs();
    // Auto-refresh toutes les 30 secondes
    const interval = setInterval(fetchLogs, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchLogs = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get('http://localhost:8000/email/sync-logs', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLogs(response.data);
    } catch (error) {
      console.error('Error fetching logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSyncTypeIcon = (syncType: string) => {
    return syncType === 'auto' ? (
      <Clock className="w-5 h-5 text-purple-500" />
    ) : (
      <RefreshCw className="w-5 h-5 text-blue-500" />
    );
  };

  const getStatusColor = (log: SyncLog) => {
    if (log.error) return 'border-red-500 bg-red-50';
    if (log.total_synced > 0) return 'border-green-500 bg-green-50';
    return 'border-gray-300 bg-white';
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
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">🤖 Synchronisation Automatique</h1>
          <p className="mt-2 text-gray-600">
            Logs des synchronisations automatiques toutes les 30 minutes
          </p>
        </div>
        <Button onClick={fetchLogs} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Rafraîchir
        </Button>
      </div>

      {/* Info Box */}
      <div className="mb-8 bg-blue-50 border-2 border-blue-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-blue-800 mb-3">ℹ️ Comment ça marche</h2>
        <ul className="list-disc list-inside space-y-2 text-blue-900">
          <li><strong>Celery Beat</strong> exécute la tâche de sync toutes les 30 minutes</li>
          <li><strong>Anti-doublon</strong> : Utilise `message_id` unique + timestamp `last_sync`</li>
          <li><strong>Providers</strong> : Synchronise tous les comptes Gmail et Outlook actifs</li>
          <li><strong>Arrêt</strong> : `docker-compose stop` arrête automatiquement Celery</li>
          <li><strong>Production</strong> : Celery tourne en continu comme un service</li>
        </ul>
      </div>

      {/* Stats */}
      {logs.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white shadow rounded-lg p-6 border-l-4 border-purple-400">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Syncs</p>
                <p className="text-3xl font-bold text-gray-900">{logs.length}</p>
              </div>
              <Clock className="w-12 h-12 text-purple-400" />
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6 border-l-4 border-green-400">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Dernière Sync</p>
                <p className="text-lg font-bold text-green-600">
                  {logs[0]?.total_synced || 0} nouveaux
                </p>
              </div>
              <CheckCircle className="w-12 h-12 text-green-400" />
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6 border-l-4 border-yellow-400">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Doublons Évités</p>
                <p className="text-3xl font-bold text-yellow-600">
                  {logs.reduce((sum, log) => sum + (log.total_duplicates || 0), 0)}
                </p>
              </div>
              <AlertCircle className="w-12 h-12 text-yellow-400" />
            </div>
          </div>
        </div>
      )}

      {/* Logs List */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Historique des Synchronisations</h2>
        </div>

        {logs.length === 0 ? (
          <div className="text-center py-12">
            <Clock className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Aucune synchronisation pour l'instant</h3>
            <p className="mt-1 text-sm text-gray-500">
              Les logs de synchronisation automatique apparaîtront ici.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {logs.map((log) => (
              <div key={log.id} className={`px-6 py-4 border-l-4 ${getStatusColor(log)}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 flex-1">
                    {getSyncTypeIcon(log.sync_type)}
                    
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                          {log.sync_type === 'auto' ? 'Automatique' : 'Manuelle'}
                        </span>
                        <span className="text-sm text-gray-500">
                          {new Date(log.created_at).toLocaleString()}
                        </span>
                      </div>
                      
                      <div className="mt-2 flex items-center space-x-6">
                        <div className="flex items-center space-x-2">
                          <CheckCircle className="w-4 h-4 text-green-600" />
                          <span className="text-sm font-medium text-gray-900">
                            {log.total_synced} nouveaux
                          </span>
                        </div>
                        
                        {log.total_duplicates > 0 && (
                          <div className="flex items-center space-x-2">
                            <AlertCircle className="w-4 h-4 text-yellow-600" />
                            <span className="text-sm text-gray-600">
                              {log.total_duplicates} doublons évités
                            </span>
                          </div>
                        )}
                        
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-600">
                            {log.connections_processed} compte(s)
                          </span>
                        </div>
                      </div>

                      {log.error && (
                        <div className="mt-2 flex items-center space-x-2 text-red-600">
                          <XCircle className="w-4 h-4" />
                          <span className="text-sm">{log.error}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}
                  >
                    {expandedLog === log.id ? 'Masquer' : 'Détails'}
                  </Button>
                </div>

                {/* Expanded Details */}
                {expandedLog === log.id && log.details && (
                  <div className="mt-4 bg-gray-50 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-gray-900 mb-3">Détails par connexion :</h4>
                    <div className="space-y-2">
                      {/* Déduplication des connexions par connection_id */}
                      {log.details
                        .filter((detail, index, self) => 
                          index === self.findIndex((d) => d.connection_id === detail.connection_id)
                        )
                        .map((detail, idx) => (
                        <div key={detail.connection_id || idx} className="flex items-center justify-between text-sm">
                          <div className="flex items-center space-x-3">
                            <span className="font-medium text-gray-700">{detail.email}</span>
                            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                              {detail.provider}
                            </span>
                          </div>
                          
                          {detail.error ? (
                            <span className="text-red-600">{detail.error}</span>
                          ) : (
                            <div className="flex items-center space-x-4">
                              <span className="text-green-600">✅ {detail.synced || 0}</span>
                              {(detail.duplicates || 0) > 0 && (
                                <span className="text-yellow-600">🔄 {detail.duplicates}</span>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

