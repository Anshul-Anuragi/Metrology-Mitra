import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/lib/auth';
import Navbar from '@/components/Navbar';

export const metadata: Metadata = {
  title: 'MetrologyMitra — Legal Metrology Compliance Inspection',
  description: 'Automated compliance inspection of packaged commodities under Legal Metrology (Packaged Commodities) Rules, 2011',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 min-h-screen flex flex-col">
        <AuthProvider>
          <Navbar />
          <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
            {children}
          </main>
          <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-500">
            <p>
              © {new Date().getFullYear()} Legal Metrology Packaged Commodities Compliance System (SIH26034) • Department of Consumer Affairs, Government of India
            </p>
          </footer>
        </AuthProvider>
      </body>
    </html>
  );
}

