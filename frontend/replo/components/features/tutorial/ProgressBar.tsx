'use client';

interface ProgressBarProps {
  progress: number;
}

const ProgressBar = ({ progress }: ProgressBarProps) => {
  // Ensure progress is between 0 and 100
  const clampedProgress = Math.min(Math.max(progress, 0), 100);
  
  return (
    <div className="w-full h-2 bg-gray-200">
      <div 
        className="h-full bg-blue-600 transition-all duration-300 ease-in-out"
        style={{ width: `${clampedProgress}%` }}
      />
    </div>
  );
};

export default ProgressBar;