import { useAuthStore } from '@/store/useAuthStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCurrentUser } from '@/hooks/useAuth';
import { useEffect } from 'react';

export function Dashboard() {
  const user = useAuthStore((state) => state.user);
  const { data: currentUserData, refetch } = useCurrentUser();

  // Optionally keep the user store in sync with /me endpoint
  useEffect(() => {
    refetch();
  }, [refetch]);

  const displayUser = currentUserData || user;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Welcome back, {displayUser?.display_name || displayUser?.username}!
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Profile Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {displayUser?.is_verified ? 'Verified' : 'Pending Verification'}
            </div>
            <p className="text-xs text-muted-foreground">
              Role: {displayUser?.role}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
