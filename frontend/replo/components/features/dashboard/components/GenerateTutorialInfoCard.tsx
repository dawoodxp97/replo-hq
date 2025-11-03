import TutorialGeneratingUi from '@/components/shared/tutorial-generating-ui/TutorialGeneratingUi';
import { Card } from 'antd';
import { memo } from 'react';

interface GenerateTutorialInfoCardProps {
  isGenerating: boolean;
  generationStep: number;
  generationProgress: number;
}

const GenerateTutorialInfoCard = (props: GenerateTutorialInfoCardProps) => {
  const { isGenerating, generationStep, generationProgress } = props;

  if (isGenerating) {
    return (
      <TutorialGeneratingUi
        generationStep={generationStep}
        generationProgress={generationProgress}
      />
    );
  }
  return (
    <div className="generate-tutorial-info-card">
      <Card className="generate-tutorial-info-card-content">
        <Card.Meta
          title="Generate Tutorial"
          description="Generate a tutorial for a GitHub repository"
        />
      </Card>
    </div>
  );
};

export default memo(GenerateTutorialInfoCard);
