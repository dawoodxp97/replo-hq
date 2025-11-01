"use client";

import { memo } from "react";

import { Tabs } from 'antd';
import type { TabsProps } from 'antd';

interface ReploTabsProps {
    items: TabsProps['items'];
    kind?: String;
}
const ReploTabs = (props: ReploTabsProps) => {
    const { items, kind = 'tab' } = props;
    const renderTabs = () => {
        switch (kind) {
            case 'tab':
                return <Tabs items={items} />;

            case 'card':
                return <div>
                    <Tabs
                        items={items} defaultActiveKey="1" type='card'
                        animated={true}
                        centered
                        style={{ marginBottom: 32 }} size="middle" /></div>;
            default:
                return null;
        }
    }
    return (
        <div className='rl-tabs-container'>
            {
                renderTabs()
            }
        </div>
    );
}


export default memo(ReploTabs);