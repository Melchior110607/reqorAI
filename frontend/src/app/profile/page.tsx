'use client';

import { useState, useEffect } from 'react';
import { ProtectedLayout } from '@/components/layout/ProtectedLayout';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useAuth } from '@/contexts/AuthContext';
import { requestsAPI } from '@/services/api';
import { RequestWithClient } from '@/types';
import { User, Building, Mail, Phone, Calendar, Activity } from 'lucide-react';

export default function ProfilePage() {
  const { user } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [recentRequests, setRecentRequests] = useState<RequestWithClient[]>([]);
  const [formData, setFormData] = useState({
    company_name: user?.company_name || '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    phone: user?.phone || '',
  });

  useEffect(() => {
    fetchRecentRequests();
  }, []);

  const fetchRecentRequests = async () => {
    try {
      const requests = await requestsAPI.getAll();
      setRecentRequests(requests.slice(0, 10)); // Last 10 requests
    } catch (error) {
      console.error('Error fetching recent requests:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Here you would call an API to update user profile
      // For now, we'll just simulate the update
      console.log('Updating profile:', formData);
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleCancel = () => {
    setFormData({
      company_name: user?.company_name || '',
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      phone: user?.phone || '',
    });
    setIsEditing(false);
  };

  if (!user) {
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
          <h1 className="text-3xl font-bold text-gray-900">Profile</h1>
          <p className="mt-2 text-gray-600">Manage your account information and view activity</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Profile Information */}
          <div className="lg:col-span-2">
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-medium text-gray-900">Account Information</h2>
                  {!isEditing && (
                    <Button variant="outline" onClick={() => setIsEditing(true)}>
                      Edit Profile
                    </Button>
                  )}
                </div>
              </div>
              
              <div className="px-6 py-6">
                {isEditing ? (
                  <form onSubmit={handleSubmit} className="space-y-6">
                    <Input
                      label="Company Name"
                      name="company_name"
                      value={formData.company_name}
                      onChange={handleChange}
                      required
                    />
                    
                    <div className="grid grid-cols-2 gap-4">
                      <Input
                        label="First Name"
                        name="first_name"
                        value={formData.first_name}
                        onChange={handleChange}
                      />
                      <Input
                        label="Last Name"
                        name="last_name"
                        value={formData.last_name}
                        onChange={handleChange}
                      />
                    </div>
                    
                    <Input
                      label="Phone"
                      name="phone"
                      type="tel"
                      value={formData.phone}
                      onChange={handleChange}
                    />

                    <div className="flex justify-end space-x-3">
                      <Button type="button" variant="outline" onClick={handleCancel}>
                        Cancel
                      </Button>
                      <Button type="submit" loading={loading} disabled={loading}>
                        Save Changes
                      </Button>
                    </div>
                  </form>
                ) : (
                  <div className="space-y-6">
                    <div className="flex items-center space-x-3">
                      <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                        <User className="w-8 h-8 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="text-xl font-medium text-gray-900">
                          {user.first_name || user.last_name 
                            ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
                            : 'User'
                          }
                        </h3>
                        <p className="text-gray-600">{user.company_name}</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <div className="flex items-center space-x-3">
                          <Mail className="w-5 h-5 text-gray-400" />
                          <div>
                            <p className="text-sm font-medium text-gray-500">Email</p>
                            <p className="text-gray-900">{user.email}</p>
                          </div>
                        </div>

                        <div className="flex items-center space-x-3">
                          <Building className="w-5 h-5 text-gray-400" />
                          <div>
                            <p className="text-sm font-medium text-gray-500">Company</p>
                            <p className="text-gray-900">{user.company_name}</p>
                          </div>
                        </div>
                      </div>

                      <div className="space-y-4">
                        {user.phone && (
                          <div className="flex items-center space-x-3">
                            <Phone className="w-5 h-5 text-gray-400" />
                            <div>
                              <p className="text-sm font-medium text-gray-500">Phone</p>
                              <p className="text-gray-900">{user.phone}</p>
                            </div>
                          </div>
                        )}

                        <div className="flex items-center space-x-3">
                          <Calendar className="w-5 h-5 text-gray-400" />
                          <div>
                            <p className="text-sm font-medium text-gray-500">Member since</p>
                            <p className="text-gray-900">{new Date(user.created_at).toLocaleDateString()}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Activity Sidebar */}
          <div className="space-y-6">
            {/* Recent Activity */}
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  <Activity className="w-5 h-5 mr-2" />
                  Recent Activity
                </h3>
              </div>
              <div className="px-6 py-4">
                <div className="space-y-4">
                  {recentRequests.length > 0 ? (
                    recentRequests.map((request) => (
                      <div key={request.id} className="flex items-start space-x-3">
                        <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-gray-900 truncate">{request.title}</p>
                          <p className="text-xs text-gray-500">
                            {request.client_name} • {new Date(request.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-gray-500">No recent activity</p>
                  )}
                </div>
              </div>
            </div>

            {/* Account Stats */}
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Account Statistics</h3>
              </div>
              <div className="px-6 py-4">
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Total Requests</span>
                    <span className="text-sm font-medium text-gray-900">{recentRequests.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Account Created</span>
                    <span className="text-sm font-medium text-gray-900">
                      {new Date(user.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Last Updated</span>
                    <span className="text-sm font-medium text-gray-900">
                      {new Date(user.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ProtectedLayout>
  );
}
