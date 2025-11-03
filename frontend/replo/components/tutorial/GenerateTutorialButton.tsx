import { memo, useState } from 'react';
import { GenerateModal } from '../modals/GenerateModal';
import { Sparkles } from 'lucide-react';
import { Tooltip } from 'antd';

const GenerateTutorialButton = () => {
  const [showGenerateModal, setShowGenerateModal] = useState(false);

  const handleGenerateTutorial = () => {
    setShowGenerateModal(true);
  };

  return (
    <>
      <div className="rl-generate-tutorial-button">
        <Tooltip title="Generate New Tutorial" placement="left">
          <button
            onClick={handleGenerateTutorial}
            className="fixed bottom-15 right-5 w-16 h-16 bg-gradient-to-br from-indigo-400 via-purple-400 to-pink-300 rounded-full shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-110 active:scale-95 flex items-center justify-center group z-50 border-4 border-white/50 ai-float"
            style={{
              boxShadow:
                '0 8px 24px rgba(129, 140, 248, 0.3), 0 0 0 0 rgba(129, 140, 248, 0.4)',
            }}
          >
            <div className="relative">
              <Sparkles className="w-7 h-7 text-white group-hover:scale-110 transition-transform duration-300" />
              <div className="absolute inset-0 bg-white/20 rounded-full blur-md group-hover:blur-xl transition-all"></div>
            </div>
            <div className="absolute -top-1 -right-1 w-5 h-5 bg-green-500 rounded-full animate-pulse border-2 border-white"></div>
          </button>
        </Tooltip>
      </div>
      <GenerateModal
        open={showGenerateModal}
        onClose={() => setShowGenerateModal(false)}
      />
    </>
  );
};

export default memo(GenerateTutorialButton);
