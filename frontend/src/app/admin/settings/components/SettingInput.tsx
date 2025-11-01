import { PlatformSetting } from '../../types/admin';

interface SettingInputProps {
  setting: PlatformSetting;
  value: any;
  onChange: (value: any) => void;
  disabled?: boolean;
}

export function SettingInput({ setting, value, onChange, disabled = false }: SettingInputProps) {
  const renderInput = () => {
    switch (setting.data_type) {
      case 'boolean':
        return (
          <div className="flex items-center">
            <button
              type="button"
              onClick={() => !disabled && onChange(!value)}
              disabled={disabled}
              className={`
                relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                ${value ? 'bg-blue-600' : 'bg-gray-200'}
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <span
                className={`
                  inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                  ${value ? 'translate-x-6' : 'translate-x-1'}
                `}
              />
            </button>
            <span className="ml-3 text-sm text-gray-700">
              {value ? 'Enabled' : 'Disabled'}
            </span>
          </div>
        );

      case 'integer':
        return (
          <input
            type="number"
            value={value ?? ''}
            onChange={(e) => onChange(parseInt(e.target.value) || 0)}
            disabled={disabled}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500 text-gray-900"
          />
        );

      case 'email':
        return (
          <input
            type="email"
            value={value ?? ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500 text-gray-900"
          />
        );

      case 'url':
        return (
          <input
            type="url"
            value={value ?? ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            placeholder="https://example.com"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500 text-gray-900"
          />
        );

      case 'color':
        return (
          <div className="flex items-center space-x-3">
            <input
              type="color"
              value={value ?? '#000000'}
              onChange={(e) => onChange(e.target.value)}
              disabled={disabled}
              className="h-10 w-20 rounded border border-gray-300 cursor-pointer disabled:opacity-50"
            />
            <input
              type="text"
              value={value ?? ''}
              onChange={(e) => onChange(e.target.value)}
              disabled={disabled}
              placeholder="#000000"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500 text-gray-900"
            />
          </div>
        );

      case 'text':
        return (
          <textarea
            value={value ?? ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            rows={4}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500 text-gray-900"
          />
        );

      case 'json':
        return (
          <textarea
            value={typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
            onChange={(e) => {
              try {
                onChange(JSON.parse(e.target.value));
              } catch {
                onChange(e.target.value);
              }
            }}
            disabled={disabled}
            rows={6}
            className="w-full px-4 py-2 font-mono text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500 text-gray-900"
          />
        );

      default: // string
        return (
          <input
            type={setting.is_sensitive ? 'password' : 'text'}
            value={value ?? ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500 text-gray-900"
          />
        );
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-gray-700">
          {setting.label}
          {setting.is_encrypted && (
            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
              🔒 Encrypted
            </span>
          )}
          {setting.requires_restart && (
            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800">
              ⚠️ Requires Restart
            </span>
          )}
        </label>
      </div>
      
      {setting.description && (
        <p className="text-sm text-gray-500">{setting.description}</p>
      )}
      
      <div className="mt-2">
        {renderInput()}
      </div>
    </div>
  );
}
