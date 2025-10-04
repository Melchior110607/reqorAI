'use client';

import { useState, useEffect } from 'react';
import { ProtectedLayout } from '@/components/layout/ProtectedLayout';
import { requestsAPI } from '@/services/api';
import { RequestWithClient, RequestStatus, RequestType } from '@/types';
import { 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  XCircle,
  ArrowUpRight,
  ArrowDownLeft,
  TrendingUp
} from 'lucide-react';

export default function DashboardPage() {
  const [requests, setRequests] = useState<RequestWithClient[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRequests();
  }, []);

  const fetchRequests = async () => {
    try {
      const data = await requestsAPI.getAll();
      setRequests(data);
    } catch (error) {
      console.error('Error fetching requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: RequestStatus) => {
    switch (status) {
      case RequestStatus.PENDING:
        return <Clock className="w-5 h-5 text-yellow-500" />;
      case RequestStatus.COMPLETED:
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case RequestStatus.OVERDUE:
        return <AlertCircle className="w-5 h-5 text-red-500" />;
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

  const outgoingRequests = requests.filter(r => r.type === RequestType.OUTGOING);
  const incomingRequests = requests.filter(r => r.type === RequestType.INCOMING);
  
  const stats = {
    total: requests.length,
    pending: requests.filter(r => r.status === RequestStatus.PENDING).length,
    completed: requests.filter(r => r.status === RequestStatus.COMPLETED).length,
    overdue: requests.filter(r => r.status === RequestStatus.OVERDUE).length,
  };

  const priorityRequests = requests.filter(r => r.is_priority).slice(0, 5);

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
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-2 text-gray-600">Overview of your B2B requests</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
                    <span className="text-white font-semibold">{stats.total}</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Requests</dt>
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

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <CheckCircle className="w-8 h-8 text-green-500" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Completed</dt>
                    <dd className="text-lg font-medium text-gray-900">{stats.completed}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <AlertCircle className="w-8 h-8 text-red-500" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Overdue</dt>
                    <dd className="text-lg font-medium text-gray-900">{stats.overdue}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          {/* <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <AlertCircle className="w-8 h-8 text-red-500" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Overdue</dt>
                    <dd className="text-lg font-medium text-gray-900">{stats.overdue}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div> */}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Priority Requests */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Priority Requests
              </h3>
              <div className="space-y-3">
                {priorityRequests.length === 0 ? (
                  <p className="text-gray-500 text-sm">No priority requests</p>
                ) : (
                  priorityRequests.map((request) => (
                    <div key={request.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                      <div className="flex items-center space-x-3">
                        {request.type === RequestType.OUTGOING ? (
                          <ArrowUpRight className="w-4 h-4 text-blue-500" />
                        ) : (
                          <ArrowDownLeft className="w-4 h-4 text-green-500" />
                        )}
                        <div>
                          <p className="text-sm font-medium text-gray-900">{request.title}</p>
                          <p className="text-xs text-gray-500">{request.client_name}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(request.status)}
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                          {request.status}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Recent Requests
              </h3>
              <div className="space-y-3">
                {requests.slice(0, 5).map((request) => (
                  <div key={request.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                    <div className="flex items-center space-x-3">
                      {request.type === RequestType.OUTGOING ? (
                        <ArrowUpRight className="w-4 h-4 text-blue-500" />
                      ) : (
                        <ArrowDownLeft className="w-4 h-4 text-green-500" />
                      )}
                      <div>
                        <p className="text-sm font-medium text-gray-900">{request.title}</p>
                        <p className="text-xs text-gray-500">{request.client_name}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(request.status)}
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                        {request.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </ProtectedLayout>
  );
}
