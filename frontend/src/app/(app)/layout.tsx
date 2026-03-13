import { Sidebar } from "@/components/layout/sidebar";
import { AuthTokenProvider } from "@/lib/auth-token-provider";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthTokenProvider>
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 overflow-y-auto bg-gray-50">{children}</main>
      </div>
    </AuthTokenProvider>
  );
}
