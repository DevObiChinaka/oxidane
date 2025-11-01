import { ReactNode } from 'react';

interface SettingsCardProps {
  title: string;
  description?: string;
  icon?: string;
  children: ReactNode;
  actions?: ReactNode;
}

export function SettingsCard({ title, description, icon, children, actions }: SettingsCardProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {icon && <span className="text-2xl">{icon}</span>}
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
              {description && (
                <p className="mt-1 text-sm text-gray-500">{description}</p>
              )}
            </div>
          </div>
          {actions && <div className="flex items-center space-x-2">{actions}</div>}
        </div>
      </div>
      <div className="px-6 py-5">
        {children}
      </div>
    </div>
  );
}
