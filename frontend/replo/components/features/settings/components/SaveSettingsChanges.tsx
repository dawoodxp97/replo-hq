import Button from '@/components/ui/button/Button';
import { Save } from 'lucide-react';
import { memo } from 'react';

const SaveSettingsChanges = (props: { handleSave: () => void }) => {
  const { handleSave } = props;

  return (
    <div className="rl-settings-footer flex justify-end items-center h-[10%] gap-4 mr-6 rounded-md mt-6 p-6 ml-6 mb-6">
      <div className="save-btn-container flex justify-end">
        <Button
          onClick={handleSave}
          className="rounded-lg !bg-gradient-to-r !from-blue-600 !to-purple-600 !border-0 !text-white hover:!from-blue-700 hover:!to-purple-700"
        >
          <Save className="w-4 h-4 mr-2" />
          Save Changes
        </Button>
      </div>
    </div>
  );
};

export default memo(SaveSettingsChanges);
