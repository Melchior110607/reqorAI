'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedLayout } from '@/components/layout/ProtectedLayout';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { RequestForm } from '@/components/requests/RequestForm';
import { requestsAPI, clientsAPI } from '@/services/api';
import { RequestWithClient, RequestType, RequestStatus, RequestPriority, Client } from '@/types';
import { 
  Plus, 
  Edit, 
  Trash2, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  XCircle,
  TrendingUp,
  Filter
} from 'lucide-react';

export default function IncomingRequestsPage() {
  const router = useRouter();
  const [requests, setRequests] = useState<RequestWithClient[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedClient, setSelectedClient] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedPriority, setSelectedPriority] = useState<string>('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [requestsData, clientsData] = await Promise.all([
        requestsAPI.getAll({ request_type: RequestType.INCOMING }),
        clientsAPI.getAll()
      ]);
      setRequests(requestsData);
      setClients(clientsData);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRequest = async (data: any) => {
    try {
      console.log('Creating request with data:', data);
      await requestsAPI.create(data);
      setIsCreateModalOpen(false);
      fetchData();
    } catch (error) {
      console.error('Error creating request:', error);
      alert('Error creating request: ' + (error as any)?.response?.data?.detail || (error as any)?.message);
      throw error; // Re-throw pour que RequestForm puisse gérer le loading
    }
  };


  const handleDeleteRequest = async (id: number) => {
    if (!confirm('Are you sure you want to delete this request?')) return;
    
    try {
      await requestsAPI.delete(id);
      fetchData();
    } catch (error) {
      console.error('Error deleting request:', error);
    }
  };

  const getStatusIcon = (status: RequestStatus) => {
    switch (status) {
      case RequestStatus.PENDING:
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case RequestStatus.COMPLETED:
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case RequestStatus.OVERDUE:
        return <AlertCircle className="w-4 h-4 text-red-500" />;
    }
  };

  const getStatusColor = (status: RequestStatus) => {
    switch (status) {
      case RequestStatus.PENDING:
        return 'bg-yellow-100 text-yellow-800';
      case RequestStatus.COMPLETED:
        return 'bg-green-100 text-green-800';
      case RequestStatus.OVERDUE:
        return 'bg-red-100 text-red-800';
    }
  };

  const getPriorityColor = (priority: RequestPriority) => {
    switch (priority) {
      case RequestPriority.LOW:
        return 'bg-gray-100 text-gray-800';
      case RequestPriority.MEDIUM:
        return 'bg-blue-100 text-blue-800';
      case RequestPriority.HIGH:
        return 'bg-orange-100 text-orange-800';
      case RequestPriority.URGENT:
        return 'bg-red-100 text-red-800';
    }
  };

  const filteredRequests = requests.filter(request => {
    if (selectedClient && request.client_id !== parseInt(selectedClient)) return false;
    if (selectedStatus && request.status !== selectedStatus) return false;
    if (selectedPriority && request.priority !== selectedPriority) return false;
    return true;
  });

  // Group requests by client
  const requestsByClient = filteredRequests.reduce((acc, request) => {
    const clientKey = `${request.client_id}-${request.client_name}`;
    if (!acc[clientKey]) {
      acc[clientKey] = {
        client: { id: request.client_id, name: request.client_name, company: request.client_company },
        requests: []
      };
    }
    acc[clientKey].requests.push(request);
    return acc;
  }, {} as Record<string, { client: { id: number; name: string; company: string }; requests: RequestWithClient[] }>);

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
        <div className="sm:flex sm:items-center sm:justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Incoming Requests</h1>
            <p className="mt-2 text-gray-600">Manage requests received from clients</p>
          </div>
          <Button onClick={() => setIsCreateModalOpen(true)}>
            <Plus className="w-4 h-4 mr-2" />
            New Request
          </Button>
        </div>

        {/* Filters */}
        <div className="bg-white p-4 rounded-lg shadow mb-6">
          <div className="flex items-center space-x-4">
            <Filter className="w-5 h-5 text-gray-400" />
            <select
              value={selectedClient}
              onChange={(e) => setSelectedClient(e.target.value)}
              className="rounded-md border-gray-300 text-sm text-gray-900 bg-white px-3 py-2"
            >
              <option value="">All Clients</option>
              {clients.map(client => (
                <option key={client.id} value={client.id}>
                  {client.name} ({client.company})
                </option>
              ))}
            </select>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="rounded-md border-gray-300 text-sm text-gray-900 bg-white px-3 py-2"
            >
              <option value="">All Statuses</option>
              <option value={RequestStatus.PENDING}>Pending</option>
              <option value={RequestStatus.COMPLETED}>Completed</option>
              <option value={RequestStatus.OVERDUE}>Overdue</option>
            </select>
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="rounded-md border-gray-300 text-sm text-gray-900 bg-white px-3 py-2"
            >
              <option value="">All Priorities</option>
              <option value={RequestPriority.LOW}>Low</option>
              <option value={RequestPriority.MEDIUM}>Medium</option>
              <option value={RequestPriority.HIGH}>High</option>
              <option value={RequestPriority.URGENT}>Urgent</option>
            </select>
          </div>
        </div>

        {/* Requests by Client */}
        <div className="space-y-6">
          {Object.entries(requestsByClient).map(([clientKey, { client, requests }]) => (
            <div key={clientKey} className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">
                  {client.name} ({client.company})
                </h3>
                <p className="text-sm text-gray-500">{requests.length} request(s)</p>
              </div>
              <div className="divide-y divide-gray-200">
                {requests.map((request) => (
                  <div key={request.id} className="px-6 py-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-center justify-between">
                      <div 
                        className="flex-1 cursor-pointer"
                        onClick={() => router.push(`/request/${request.id}`)}
                      >
                        <div className="flex items-center space-x-3">
                          <h4 className="text-sm font-medium text-gray-900 hover:text-blue-600">
                            {request.title}
                            {request.is_priority && (
                              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                                Priority
                              </span>
                            )}
                          </h4>
                        </div>
                        <p className="mt-1 text-sm text-gray-600">{request.description}</p>
                        <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                          <span>Created: {new Date(request.created_at).toLocaleDateString()}</span>
                          {request.due_date && (
                            <span>Due: {new Date(request.due_date).toLocaleDateString()}</span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(request.status)}
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                            {request.status}
                          </span>
                        </div>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(request.priority)}`}>
                          {request.priority}
                        </span>
                        <div className="flex items-center space-x-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteRequest(request.id)}
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
            </div>
          ))}
        </div>

        {Object.keys(requestsByClient).length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No incoming requests found</p>
          </div>
        )}

        {/* Create Request Modal */}
        <Modal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          title="Create New Request"
        >
          <RequestForm
            onSubmit={handleCreateRequest}
            onCancel={() => setIsCreateModalOpen(false)}
            initialData={{ type: RequestType.INCOMING }}
          />
        </Modal>

      </div>
    </ProtectedLayout>
  );
}
