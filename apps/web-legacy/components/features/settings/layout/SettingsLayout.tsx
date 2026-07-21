import { memo } from 'react';
import { Switch } from 'antd';

export const SettingsCard = (props: {
  children: React.ReactNode;
  header?: {
    icon: React.ReactNode;
    title: React.ReactNode;
    description: string;
  };
  className?: string;
}) => {
  const {
    children,
    header = { icon: null, title: '', description: '' },
    className,
  } = props;

  return (
    <div
      className={`bg-white rounded-xl p-6 ml-6 mr-6 mb-6 mt-6 shadow-[0px_7px_29px_rgba(100,100,111,0.15)] hover:shadow-[0px_7px_29px_rgba(100,100,111,0.25)] transition-shadow duration-300 ${className}`}
    >
      <div className="flex items-center h-10 text-lg font-medium text-gray-900">
        {header?.icon}
        {header?.title}
      </div>
      <div className="h-10 text-sm text-gray-500">{header?.description}</div>
      {children}
    </div>
  );
};

export const SettingsSeparator = () => {
  return <div className="h-[1px] bg-gray-200 my-4 w-full"></div>;
};

interface SettingsToggleCardProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  bgColor?: string;
  customButton?: React.ReactNode;
  customStyles?: React.CSSProperties;
  className?: string;
}

export const SettingsToggleCard = (props: SettingsToggleCardProps) => {
  const {
    icon,
    title,
    description,
    checked,
    onChange,
    bgColor = 'bg-gradient-to-r from-blue-50 to-purple-50',
    customButton,
    customStyles,
    className,
  } = props;
  return (
    <div
      className={`h-[75px] flex items-center justify-between ${
        icon ? 'p-4' : 'p-0 pr-4  !h-[50px]'
      } ${bgColor} rounded-xl mb-4 transition-all duration-300 ${className}`}
      style={customStyles}
    >
      <div className={`details flex items-center ${icon ? 'gap-3' : 'gap-0'}`}>
        <div className="icon-container">{icon}</div>
        <div className="description-container flex flex-col gap-1">
          <p className="font-medium text-gray-900 !mb-0">{title}</p>
          <p className="text-sm text-gray-600 !mb-0">{description}</p>
        </div>
      </div>
      <div className="toggle">
        {customButton ? (
          customButton
        ) : (
          <Switch checked={checked} onChange={onChange} />
        )}
      </div>
    </div>
  );
};

export const SettingsContentWrapper = (props: {
  children: React.ReactNode;
}) => {
  const { children } = props;
  return (
    <div className="w-full overflow-auto h-[calc(100vh-209px)]">{children}</div>
  );
};
