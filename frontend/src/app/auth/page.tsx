import { Suspense } from 'react';
import NewAuthForm from '../components/NewAuthForm';

function AuthContent() {
  return <NewAuthForm />;
}

export default function AuthPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Loading...</div>}>
      <AuthContent />
    </Suspense>
  );
}