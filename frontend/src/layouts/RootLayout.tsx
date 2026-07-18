import { Outlet } from 'react-router-dom';
import { Toaster } from '@/components/ui/toaster';

export function RootLayout() {
  return (
    <div className="min-h-screen bg-background font-sans antialiased">
      <Outlet />
      <Toaster />
    </div>
  );
}
