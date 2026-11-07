import React from 'react';

export const BrandLogo: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({ size = 'md' }) => {
  const textSize = size === 'sm' ? 'text-lg' : size === 'lg' ? 'text-3xl' : 'text-2xl';

  return (
    <div className="flex items-center gap-2.5 select-none">
      <div className="relative flex items-center justify-center">
        {/* Surveillance beacon */}
        <span className="relative flex h-2.5 w-2.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#15b89a] opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#15b89a]"></span>
        </span>
      </div>
      <span className={`${textSize} font-semibold tracking-wider text-slate-100 lowercase font-sans`}>
        vigilant
      </span>
    </div>
  );
};

