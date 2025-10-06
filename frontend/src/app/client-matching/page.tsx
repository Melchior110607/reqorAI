'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { emailAPI } from '@/services/emailAPI';
import { Users, CheckCircle, XCircle, AlertCircle, Search } from 'lucide-react';

interface MatchResult {
  email_id: number;
  sender_email: string;
  subject: string;
  matched: boolean;
  client_id?: number;
  client_name?: string;
  client_company?: string;
  confidence: number;
  rule_type?: string;
  rule_pattern?: string;
}

export default function ClientMatchingPage() {
  const [matching, setMatching] = useState(false);
  const [results, setResults] = useState<MatchResult[]>([]);
  const [stats, setStats] = useState<{
    total: number;
    matched: number;
    ignored: number;
  } | null>(null);
  const [filter, setFilter] = useState<'all' | 'matched' | 'ignored'>('all');

  const runMatching = async () => {
    try {
      setMatching(true);
      const data = await emailAPI.matchClientsToEmails();
      
      setResults(data.results);
      setStats({
        total: data.total_emails,
        matched: data.matched_count,
        ignored: data.ignored_count,
      });
      
      alert(`✅ Matching terminé!\n${data.matched_count} emails matchés\n${data.ignored_count} emails ignorés`);
    } catch (error: any) {
      console.error('Error running matching:', error);
      alert('❌ Erreur: ' + (error.response?.data?.detail || error.message));
    } finally {
      setMatching(false);
    }
  };

  const filteredResults = results.filter(r => {
    if (filter === 'matched') return r.matched;
    if (filter === 'ignored') return !r.matched;
    return true;
  });

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">🎯 Client Matching Test</h1>
          <p className="mt-2 text-gray-600">
            Testez l'algorithme de reconnaissance client sur vos emails
          </p>
        </div>
        <Button 
          onClick={runMatching} 
          disabled={matching}
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          <Search className={`w-4 h-4 mr-2 ${matching ? 'animate-spin' : ''}`} />
          {matching ? 'Matching en cours...' : '🔍 Lancer le Matching'}
        </Button>
      </div>

      {/* Instructions */}
      <div className="mb-8 bg-blue-50 border-2 border-blue-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-blue-800 mb-3">📋 Instructions</h2>
        <ol className="list-decimal list-inside space-y-2 text-blue-900">
          <li>Créez des clients dans l'onglet "Clients" avec des emails correspondant à vos emails interceptés</li>
          <li>Cliquez sur "Lancer le Matching" pour appliquer l'algorithme</li>
          <li>Vérifiez quels emails sont correctement matchés avec leurs clients</li>
          <li>Les emails non-matchés apparaîtront dans "Ignorés"</li>
        </ol>
      </div>

      {/* Statistics */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white shadow rounded-lg p-6 border-l-4 border-gray-400">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Emails</p>
                <p className="text-3xl font-bold text-gray-900">{stats.total}</p>
              </div>
              <Users className="w-12 h-12 text-gray-400" />
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6 border-l-4 border-green-400">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Emails Matchés</p>
                <p className="text-3xl font-bold text-green-600">{stats.matched}</p>
              </div>
              <CheckCircle className="w-12 h-12 text-green-400" />
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6 border-l-4 border-red-400">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Emails Ignorés</p>
                <p className="text-3xl font-bold text-red-600">{stats.ignored}</p>
              </div>
              <XCircle className="w-12 h-12 text-red-400" />
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      {results.length > 0 && (
        <div className="mb-4 flex space-x-2">
          <Button
            variant={filter === 'all' ? 'primary' : 'outline'}
            onClick={() => setFilter('all')}
            size="sm"
          >
            Tous ({results.length})
          </Button>
          <Button
            variant={filter === 'matched' ? 'primary' : 'outline'}
            onClick={() => setFilter('matched')}
            size="sm"
            className="text-green-600"
          >
            ✅ Matchés ({results.filter(r => r.matched).length})
          </Button>
          <Button
            variant={filter === 'ignored' ? 'primary' : 'outline'}
            onClick={() => setFilter('ignored')}
            size="sm"
            className="text-red-600"
          >
            ❌ Ignorés ({results.filter(r => !r.matched).length})
          </Button>
        </div>
      )}

      {/* Results */}
      {results.length > 0 ? (
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Résultats du Matching</h2>
          </div>
          
          <div className="divide-y divide-gray-200">
            {filteredResults.map((result) => (
              <div 
                key={result.email_id} 
                className={`px-6 py-4 ${result.matched ? 'bg-green-50' : 'bg-red-50'}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      {result.matched ? (
                        <CheckCircle className="w-5 h-5 text-green-600" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-600" />
                      )}
                      <h4 className="text-sm font-medium text-gray-900">
                        {result.subject}
                      </h4>
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-2">
                      From: <span className="font-medium">{result.sender_email}</span>
                    </p>
                    
                    {result.matched ? (
                      <div className="mt-3 space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-medium text-green-700">Client:</span>
                          <span className="text-sm font-semibold text-gray-900">
                            {result.client_name} ({result.client_company})
                          </span>
                        </div>
                        
                        <div className="flex items-center space-x-4">
                          <div className="flex items-center space-x-2">
                            <span className="text-xs font-medium text-green-700">Confiance:</span>
                            <span className={`text-sm font-bold ${
                              result.confidence >= 0.9 ? 'text-green-600' :
                              result.confidence >= 0.7 ? 'text-yellow-600' :
                              'text-orange-600'
                            }`}>
                              {(result.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            <span className="text-xs font-medium text-green-700">Règle:</span>
                            <span className="text-xs bg-green-200 text-green-800 px-2 py-1 rounded">
                              {result.rule_type}: {result.rule_pattern}
                            </span>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="mt-2 flex items-center space-x-2">
                        <AlertCircle className="w-4 h-4 text-red-500" />
                        <span className="text-sm text-red-600 font-medium">
                          Aucun client correspondant trouvé
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg p-12 text-center">
          <Search className="mx-auto h-16 w-16 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun résultat pour l'instant</h3>
          <p className="text-sm text-gray-500 mb-6">
            Cliquez sur "Lancer le Matching" pour tester l'algorithme
          </p>
        </div>
      )}
    </div>
  );
}

