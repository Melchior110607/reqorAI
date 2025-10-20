'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedLayout } from '../../components/layout/ProtectedLayout';
import { Calendar, Plus } from 'lucide-react';

interface RequestSummary {
  id: number;
  title: string;
  status: string;
  computed_status: string;
  type: string;
  due_date: string | null;
  is_overdue: boolean;
  days_until_due: number | null;
  follow_up_count: number;
  is_follow_up: boolean;
  priority: string;
  client_name?: string;
  created_at: string;
}

interface CalendarDay {
  date: string;
  isToday: boolean;
  isCurrentMonth: boolean;
  requests: RequestSummary[];
}

export default function DashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [calendarData, setCalendarData] = useState<Record<string, RequestSummary[]>>({});
  const [upcomingRequests, setUpcomingRequests] = useState<RequestSummary[]>([]);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, [currentMonth]);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      
      // Fetch calendar data
      const year = currentMonth.getFullYear();
      const month = currentMonth.getMonth() + 1;
      const calendarResponse = await fetch(`http://localhost:8000/dashboard/calendar?year=${year}&month=${month}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      // Fetch upcoming requests
      const upcomingResponse = await fetch('http://localhost:8000/dashboard/upcoming?days=14', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (calendarResponse.ok) {
        const calendarData = await calendarResponse.json();
        setCalendarData(calendarData.calendar || {});
      }

      if (upcomingResponse.ok) {
        const upcomingData = await upcomingResponse.json();
        setUpcomingRequests(upcomingData.requests || []);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    const colors = {
      urgent: 'bg-white border-gray-300',
      high: 'bg-white border-gray-300',
      medium: 'bg-white border-gray-300',
      low: 'bg-white border-gray-300',
    };
    return colors[priority as keyof typeof colors] || 'bg-white border-gray-300';
  };

  const getPriorityBadgeColor = (priority: string) => {
    const colors = {
      urgent: 'bg-gray-900 text-white',
      high: 'bg-gray-700 text-white',
      medium: 'bg-gray-500 text-white',
      low: 'bg-gray-400 text-gray-900',
    };
    return colors[priority as keyof typeof colors] || 'bg-gray-500 text-white';
  };
  
  const getPriorityDot = (priority: string) => {
    const colors = {
      urgent: 'bg-red-500',
      high: 'bg-orange-500',
      medium: 'bg-blue-500',
      low: 'bg-green-500',
    };
    return colors[priority as keyof typeof colors] || 'bg-gray-500';
  };

  const generateCalendarDays = (): CalendarDay[] => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const firstDayOfWeek = firstDay.getDay();
    const daysInMonth = lastDay.getDate();

    const days: CalendarDay[] = [];
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Previous month days
    const prevMonthLastDay = new Date(year, month, 0).getDate();
    for (let i = firstDayOfWeek - 1; i >= 0; i--) {
      const date = new Date(year, month - 1, prevMonthLastDay - i);
      days.push({
        date: date.toISOString().split('T')[0],
        isToday: false,
        isCurrentMonth: false,
        requests: []
      });
    }

    // Current month days
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day);
      const dateStr = date.toISOString().split('T')[0];
      const isToday = date.getTime() === today.getTime();
      
      days.push({
        date: dateStr,
        isToday,
        isCurrentMonth: true,
        requests: calendarData[dateStr] || []
      });
    }

    // Next month days
    const remainingDays = 42 - days.length; // 6 weeks * 7 days
    for (let day = 1; day <= remainingDays; day++) {
      const date = new Date(year, month + 1, day);
      days.push({
        date: date.toISOString().split('T')[0],
        isToday: false,
        isCurrentMonth: false,
        requests: []
      });
    }

    return days;
  };

  const addToCalendar = (request: RequestSummary) => {
    if (!request.due_date) return;
    
    const startDate = new Date(request.due_date);
    const endDate = new Date(startDate);
    endDate.setHours(startDate.getHours() + 1);

    const formatDate = (date: Date) => {
      return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
    };

    const event = {
      title: request.title,
      description: `Request #${request.id} - ${request.type}\\nPriority: ${request.priority}${request.client_name ? `\\nClient: ${request.client_name}` : ''}`,
      start: formatDate(startDate),
      end: formatDate(endDate),
    };

    const icsContent = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//ReqorAI//Calendar//EN
BEGIN:VEVENT
UID:request-${request.id}@reqorai.com
DTSTAMP:${formatDate(new Date())}
DTSTART:${event.start}
DTEND:${event.end}
SUMMARY:${event.title}
DESCRIPTION:${event.description}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR`;

    const blob = new Blob([icsContent], { type: 'text/calendar' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `request-${request.id}.ics`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const calendarDays = generateCalendarDays();

  if (loading) {
    return (
      <ProtectedLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
        </div>
      </ProtectedLayout>
    );
  }

  return (
    <ProtectedLayout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>

        {/* Calendar Section */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center">
              <Calendar className="w-5 h-5 mr-2 text-gray-600" />
              {currentMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
            </h2>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))}
                className="px-3 py-1.5 text-sm bg-white border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
              >
                ← Prev
              </button>
              <button
                onClick={() => setCurrentMonth(new Date())}
                className="px-3 py-1.5 text-sm bg-white border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
              >
                Today
              </button>
              <button
                onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))}
                className="px-3 py-1.5 text-sm bg-white border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
              >
                Next →
              </button>
            </div>
          </div>

          {/* Calendar Grid */}
          <div className="grid grid-cols-7 gap-px bg-gray-200 border border-gray-200">
            {/* Day headers */}
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <div key={day} className="text-center text-xs font-semibold text-gray-600 py-2 bg-gray-50">
                {day}
              </div>
            ))}

            {/* Calendar days */}
            {calendarDays.map((day, index) => (
              <div
                key={index}
                className={`min-h-[80px] p-1.5 bg-white transition-all ${
                  day.isToday
                    ? 'bg-blue-50 border-2 border-blue-400'
                    : day.isCurrentMonth
                    ? 'hover:bg-gray-50'
                    : 'bg-gray-50'
                } cursor-pointer`}
                onClick={() => setSelectedDate(day.date)}
              >
                <div className={`text-xs font-medium mb-1 ${
                  day.isToday
                    ? 'text-blue-600 font-semibold'
                    : day.isCurrentMonth
                    ? 'text-gray-900'
                    : 'text-gray-400'
                }`}>
                  {new Date(day.date).getDate()}
                </div>

                {day.requests.length > 0 && (
                  <div className="space-y-0.5">
                    {day.requests.slice(0, 3).map(req => (
                      <div
                        key={req.id}
                        className="flex items-center text-xs px-1 py-0.5 rounded cursor-pointer hover:bg-gray-100"
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/request/${req.id}`);
                        }}
                        title={req.title}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${getPriorityDot(req.priority || 'medium')} mr-1 flex-shrink-0`}></span>
                        <span className="truncate text-gray-700">{req.title}</span>
                      </div>
                    ))}
                    {day.requests.length > 3 && (
                      <div className="text-xs text-gray-500 pl-2.5">
                        +{day.requests.length - 3}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Selected Date Details */}
        {selectedDate && calendarData[selectedDate] && calendarData[selectedDate].length > 0 && (
          <div className="bg-white border border-gray-200 rounded-lg p-6 mb-8">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {new Date(selectedDate).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
              </h3>
              <button
                onClick={() => setSelectedDate(null)}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Close
              </button>
            </div>
            <div className="space-y-2">
              {calendarData[selectedDate].map(req => (
                <div
                  key={req.id}
                  className="border border-gray-200 rounded p-3 cursor-pointer hover:border-gray-300 hover:shadow-sm transition-all"
                  onClick={() => router.push(`/request/${req.id}`)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 flex items-start gap-2">
                      <span className={`w-2 h-2 rounded-full ${getPriorityDot(req.priority || 'medium')} mt-1.5 flex-shrink-0`}></span>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-gray-900 mb-1">{req.title}</h4>
                        <div className="text-sm text-gray-600">
                          <span>{req.type === 'incoming' ? 'Incoming' : 'Outgoing'}</span>
                          {req.client_name && <span> • {req.client_name}</span>}
                          {req.is_overdue && (
                            <span className="text-red-600 font-medium"> • Overdue by {Math.abs(req.days_until_due || 0)}d</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <span className={`${getPriorityBadgeColor(req.priority || 'medium')} text-xs px-2 py-1 rounded`}>
                        {(req.priority || 'medium').toUpperCase()}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          addToCalendar(req);
                        }}
                        className="text-xs text-gray-600 hover:text-gray-900"
                        title="Add to calendar"
                      >
                        <Plus className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Upcoming Requests */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Upcoming Requests (Next 14 Days)
          </h2>
          
          {upcomingRequests.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No upcoming requests</p>
          ) : (
            <div className="space-y-2">
              {upcomingRequests.map(req => (
                <div
                  key={req.id}
                  className="border border-gray-200 rounded p-3 cursor-pointer hover:border-gray-300 hover:shadow-sm transition-all"
                  onClick={() => router.push(`/request/${req.id}`)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 flex items-start gap-2">
                      <span className={`w-2 h-2 rounded-full ${getPriorityDot(req.priority || 'medium')} mt-1.5 flex-shrink-0`}></span>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-gray-900 mb-1">{req.title}</h3>
                        <div className="text-sm text-gray-600">
                          <span>Due: {new Date(req.due_date!).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                          {req.days_until_due !== null && <span> ({req.days_until_due}d)</span>}
                          <span> • {req.type === 'incoming' ? 'Incoming' : 'Outgoing'}</span>
                          {req.client_name && <span> • {req.client_name}</span>}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <span className={`${getPriorityBadgeColor(req.priority || 'medium')} text-xs px-2 py-1 rounded whitespace-nowrap`}>
                        {(req.priority || 'medium').toUpperCase()}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          addToCalendar(req);
                        }}
                        className="text-xs text-gray-600 hover:text-gray-900"
                        title="Add to calendar"
                      >
                        <Plus className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </ProtectedLayout>
  );
}
