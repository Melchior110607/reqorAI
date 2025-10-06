'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  ArrowUpRight, 
  ArrowDownLeft, 
  Users, 
  User,
  Mail,
  Brain,
  Target,
} from 'lucide-react';

export function Sidebar() {
  const pathname = usePathname();

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/outgoing-requests', label: 'Outgoing', icon: ArrowUpRight },
    { href: '/incoming-requests', label: 'Incoming', icon: ArrowDownLeft },
    { href: '/clients', label: 'Clients', icon: Users },
    { href: '/email-settings', label: 'Email', icon: Mail },
    { href: '/ai-monitoring', label: 'AI Debug', icon: Brain },
    { href: '/client-matching', label: 'Matching Test', icon: Target },
    { href: '/profile', label: 'Profile', icon: User },
  ];

  return (
    <aside className="fixed left-0 top-16 h-[calc(100vh-4rem)] w-64 bg-white border-r border-gray-200 overflow-y-auto">
      <nav className="flex flex-col p-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-600 border-l-4 border-blue-600'
                  : 'text-gray-700 hover:bg-gray-50 border-l-4 border-transparent hover:border-gray-300'
              }`}
            >
              <Icon className="w-5 h-5 mr-3" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

