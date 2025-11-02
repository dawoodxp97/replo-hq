import React from 'react';
import { Github, Gitlab, Plug2 } from 'lucide-react';

export const getAccountIcon = (name: string): React.ReactNode => {
  switch (name.toLowerCase()) {
    case 'github':
      return <Github className="w-5 h-5 text-white" />;
    case 'gitlab':
      return <Gitlab className="w-5 h-5 text-white" />;
    default:
      return <Plug2 className="w-5 h-5 text-white" />;
  }
};

