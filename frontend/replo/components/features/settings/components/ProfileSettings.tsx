import ReploInput from '@/components/ui/input/Input';
import { Input } from 'antd';
import { useState } from 'react';

const ProfileSettings = () => {
  const [emailInput, setEmailInput] = useState('');
  return (
    <div className="w-full h-full">
      <div className="pii bg-white shadow-md rounded-md p-6">
        <div className="h-15">ss</div>
        <div className="h-25"></div>

        <div className="">
          <div className="">
            <div className="user-first-name"></div>
            <div className="user-last-name"></div>
          </div>
          <div className="email">
            <ReploInput
              title="Email Address"
              kind="email"
              value={emailInput}
              onChange={e => {
                setEmailInput(e.target.value);
              }}
              required
            />
          </div>
          <div className="bio"></div>
          <div className="">
            <div className="location"></div>
            <div className="website"></div>
          </div>
        </div>
      </div>
      <div className="bg-white shadow-md rounded-md p-6 mt-4"></div>
    </div>
  );
};

export default ProfileSettings;
