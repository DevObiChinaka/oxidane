import { Suspense } from 'react';
import NewAuthForm from '../../components/NewAuthForm';

function LoginContent() {
  return <NewAuthForm />;
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Loading...</div>}>
      <LoginContent />
    </Suspense>
  );
}
