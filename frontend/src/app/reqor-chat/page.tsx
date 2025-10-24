'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedLayout } from '../../components/layout/ProtectedLayout';
import { Send, Loader2, Sparkles } from 'lucide-react';
import TextType from '../../components/ui/TextType';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isTyping?: boolean;
  requestId?: number; // For clickable link to created request
}

interface ChatResponse {
  type: 'conversation' | 'request_created';
  message: string;
  ready: boolean;
  request_id?: number;
  has_draft?: boolean;
}

export default function ReqorChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hello! I'm Reqor, your personal Request AI Assistant 😄 \n\nI can help you create requests quickly. Just tell me what you need, and I'll take care of the rest!",
      timestamp: new Date(),
      isTyping: false
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<any[]>([]);
  const [extractedData, setExtractedData] = useState({});
  const [requestCreated, setRequestCreated] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [currentTypingIndex, setCurrentTypingIndex] = useState<number | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    // Add to conversation history
    const newHistory = [
      ...conversationHistory,
      { role: 'user', content: inputMessage }
    ];

    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/requests/ai-chat', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: inputMessage,
          conversation_history: conversationHistory,
          extracted_data: extractedData
        })
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data: ChatResponse = await response.json();

      // Check if request was created
      if (data.type === 'request_created' && data.request_id) {
        // Show "Creating request..." message first
        const creatingMessage: Message = {
          role: 'assistant',
          content: '🔄 Creating request...',
          timestamp: new Date(),
          isTyping: false
        };
        setMessages(prev => [...prev, creatingMessage]);
        
        // Small delay then show success with link
        setTimeout(() => {
          setMessages(prev => {
            const withoutCreating = prev.slice(0, -1); // Remove "Creating..." message
            const successMessage = data.has_draft 
              ? `Request created successfully\n A draft response has been auto-generated using your knowledge base.\n\nYou can view it here: Request #${data.request_id}`
              : `Request created successfully\n\nYou can view it here: Request #${data.request_id}`;
            
            return [
              ...withoutCreating,
              {
                role: 'assistant',
                content: successMessage,
                timestamp: new Date(),
                isTyping: false,
                requestId: data.request_id // Add requestId for link
              }
            ];
          });
          setRequestCreated(true);
        }, 500);
      } else {
        // Normal conversation response with typing animation
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.message,
          timestamp: new Date(),
          isTyping: true
        };

        setMessages(prev => [...prev, assistantMessage]);
        setCurrentTypingIndex(messages.length + 1);

        // Update conversation history
        setConversationHistory([...newHistory, { role: 'assistant', content: data.message }]);
      }

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: "Sorry, an error occurred. Can you try again?",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const finishTyping = (index: number) => {
    setMessages(prev => prev.map((msg, i) => 
      i === index ? { ...msg, isTyping: false } : msg
    ));
    setCurrentTypingIndex(null);
  };

  return (
    <ProtectedLayout>
      <div className="fixed top-16 left-64 right-0 bottom-0 flex flex-col">
        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto bg-gray-50 p-6">
          <div className="max-w-4xl mx-auto min-h-full flex flex-col justify-center space-y-4 py-4">
            {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-4 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-800 border border-gray-200'
                }`}
              >
                {message.role === 'assistant' && (
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="w-4 h-4 text-gray-600" />
                    <span className="text-xs font-semibold text-gray-700">Reqor</span>
                  </div>
                )}
                
                {message.isTyping ? (
                  <TextType
                    text={message.content}
                    typingSpeed={20}
                    className="whitespace-pre-wrap text-gray-800"
                    showCursor={false}
                    onSentenceComplete={() => finishTyping(index)}
                  />
                ) : (
                  <div className="whitespace-pre-wrap">
                    {message.content}
                    {message.requestId && (
                      <button
                        onClick={() => router.push(`/request/${message.requestId}`)}
                        className="mt-3 block w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-all text-sm font-medium"
                      >
                        View Request →
                      </button>
                    )}
                  </div>
                )}

                <div className="text-xs opacity-70 mt-2">
                  {message.timestamp.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
            ))}

            {isLoading && (
            <div className="flex justify-start animate-fade-in">
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-gray-600" />
                  <span className="text-sm text-gray-600">Reqor is thinking...</span>
                </div>
              </div>
            </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 p-4 flex-shrink-0">
          <div className="max-w-4xl mx-auto w-full">
            <div className="flex gap-3 items-end">
              <div className="flex-1">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Describe your request in natural language..."
                  className="w-full resize-none rounded-lg border border-gray-300 px-4 py-3 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  rows={1}
                  disabled={isLoading || requestCreated}
                  style={{ 
                    minHeight: '52px',
                    maxHeight: '150px'
                  }}
                  onInput={(e) => {
                    const target = e.target as HTMLTextAreaElement;
                    target.style.height = '52px';
                    target.style.height = `${Math.min(target.scrollHeight, 150)}px`;
                  }}
                />
              </div>
              <button
                onClick={sendMessage}
                disabled={!inputMessage.trim() || isLoading || requestCreated}
                className="bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              💡 Tip: Mention the client, request type (incoming/outgoing), and date if possible
            </p>
          </div>
        </div>
      </div>

      <style jsx global>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }
      `}</style>
    </ProtectedLayout>
  );
}

