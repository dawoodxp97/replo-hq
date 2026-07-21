'use client';

import { memo } from 'react';
import type { TabsProps } from 'antd';
import { Tabs } from 'antd';

interface ReploTabsProps {
  items: TabsProps['items'];
  kind?: String;
  activeKey?: string;
  onChange?: (key: string) => void;
}
const ReploTabs = (props: ReploTabsProps) => {
  const { items, kind = 'tab', activeKey, onChange } = props;
  const renderTabs = () => {
    switch (kind) {
      case 'tab':
        return (
          <Tabs
            items={items}
            activeKey={activeKey}
            onChange={onChange}
            destroyOnHidden={true}
          />
        );

      case 'card':
        return (
          <Tabs
            className="h-full"
            items={items}
            activeKey={activeKey}
            onChange={onChange}
            defaultActiveKey={!activeKey ? '1' : undefined}
            type="card"
            animated={true}
            centered
            style={{ marginBottom: 32 }}
            size="middle"
            tabBarStyle={{ height: '10%', marginBottom: 0 }}
            destroyOnHidden={true}
          />
        );
      default:
        return null;
    }
  };
  return <div className="rl-tabs-container h-full">{renderTabs()}</div>;
};

export default memo(ReploTabs);
