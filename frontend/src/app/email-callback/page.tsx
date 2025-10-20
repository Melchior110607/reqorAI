'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { emailAPI } from '@/services/emailAPI';
import { EmailProvider } from '@/types/email';

function EmailCallbackContent() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    handleCallback();
  }, []);

  const handleCallback = async () => {
    try {
      const success = searchParams.get('success');
      const error = searchParams.get('error');
      const provider = searchParams.get('provider');
      
      if (error) {
        setStatus('error');
        setMessage(`OAuth error: ${error}`);
        return;
      }

      if (success === 'true') {
        setStatus('success');
        setMessage(`${provider} account connected successfully!`);
        
        // Informer la fenêtre parent (popup)
        if (window.opener) {
          window.opener.postMessage({ type: 'OAUTH_SUCCESS' }, window.location.origin);
          setTimeout(() => window.close(), 1500);
        } else {
          // Si pas de popup, rediriger vers les paramètres email
          setTimeout(() => {
            window.location.href = '/email-settings';
          }, 2000);
        }
        return;
      }

      // Si on arrive ici, il manque des paramètres
      setStatus('error');
      setMessage('Invalid callback parameters');
      
    } catch (error: any) {
      console.error('OAuth callback error:', error);
      setStatus('error');
      setMessage('Failed to process callback');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white shadow rounded-lg p-6">
        <div className="text-center">
          {status === 'loading' && (
            <>
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <h2 className="mt-4 text-lg font-medium text-gray-900">Connecting your email account...</h2>
              <p className="mt-2 text-sm text-gray-600">Please wait while we set up your email integration.</p>
            </>
          )}
          
          {status === 'success' && (
            <>
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="mt-4 text-lg font-medium text-gray-900">Success!</h2>
              <p className="mt-2 text-sm text-gray-600">{message}</p>
              <p className="mt-2 text-xs text-gray-500">This window will close automatically...</p>
            </>
          )}
          
          {status === 'error' && (
            <>
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h2 className="mt-4 text-lg font-medium text-gray-900">Connection Failed</h2>
              <p className="mt-2 text-sm text-gray-600">{message}</p>
              <div className="mt-4 flex gap-3 justify-center">
                <button 
                  onClick={() => {
                    // Essayer de fermer la fenêtre (fonctionne si popup)
                    // Sinon rediriger vers email settings
                    if (window.opener) {
                      window.close();
                    } else {
                      window.location.href = '/email-settings';
                    }
                  }}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
                >
                  Close
                </button>
                <button 
                  onClick={() => window.location.href = '/email-settings'}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  Return to Settings
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function EmailCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading...</h2>
        </div>
      </div>
    }>
      <EmailCallbackContent />
    </Suspense>
  );
}
