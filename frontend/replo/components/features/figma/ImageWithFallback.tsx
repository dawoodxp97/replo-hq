'use client';

import { useState } from 'react';
import Image from 'next/image';

interface ImageWithFallbackProps {
  src: string;
  alt: string;
  className?: string;
  fallbackSrc?: string;
}

export function ImageWithFallback({
  src,
  alt,
  className = '',
  fallbackSrc,
}: ImageWithFallbackProps) {
  const [imgSrc, setImgSrc] = useState(src);
  const [hasError, setHasError] = useState(false);

  const defaultFallback =
    'https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=400';

  const handleError = () => {
    if (!hasError) {
      setHasError(true);
      setImgSrc(fallbackSrc || defaultFallback);
    }
  };

  return (
    <div className="relative w-full h-full">
      <Image
        src={imgSrc}
        alt={alt}
        fill
        className={className}
        onError={handleError}
        style={{ objectFit: 'cover' }}
        unoptimized
      />
    </div>
  );
}
