import { cn } from '../lib/utils';

export interface DiagramViewerProps {
  title?: string;
  className?: string;
}

export function DiagramViewer({ title, className }: DiagramViewerProps) {
  return (
    <div className={cn('border border-gray-200 rounded-lg overflow-hidden my-4', className)}>
      {title && <div className="bg-gray-50 px-4 py-2 border-b border-gray-200 text-sm font-medium">{title}</div>}
      <div className="p-4 bg-white">
        <div className="flex items-center justify-center h-40 text-gray-400">
          Diagram renders here
        </div>
      </div>
    </div>
  );
}
