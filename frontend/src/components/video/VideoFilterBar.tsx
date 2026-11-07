import React from 'react';
import { Search, LayoutGrid, List, RefreshCw, X } from 'lucide-react';

interface VideoFilterBarProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  statusFilter: string;
  onStatusChange: (status: string) => void;
  sourceFilter?: 'LIVE' | 'UPLOADED' | 'ALL';
  onSourceFilterChange?: (source: 'LIVE' | 'UPLOADED' | 'ALL') => void;
  showSourceFilter?: boolean;
  viewMode: 'grid' | 'table';
  onViewModeChange: (mode: 'grid' | 'table') => void;
  onRefresh: () => void;
  isLoading: boolean;
}

export const VideoFilterBar: React.FC<VideoFilterBarProps> = ({
  searchQuery,
  onSearchChange,
  statusFilter,
  onStatusChange,
  sourceFilter = 'ALL',
  onSourceFilterChange,
  showSourceFilter = false,
  viewMode,
  onViewModeChange,
  onRefresh,
  isLoading,
}) => {
  const statusOptions = [
    { label: 'All Status', value: 'ALL' },
    { label: 'Ready', value: 'READY' },
    { label: 'Processing', value: 'PROCESSING' },
    { label: 'Failed', value: 'FAILED' },
  ];

  const sourceOptions: { label: string; value: 'ALL' | 'LIVE' | 'UPLOADED' }[] = [
    { label: 'All Sources', value: 'ALL' },
    { label: 'Live Rec', value: 'LIVE' },
    { label: 'Uploaded', value: 'UPLOADED' },
  ];

  return (
    <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 bg-[#0a1819]/70 border border-[#14373a] rounded-2xl p-4 backdrop-blur-md">
      {/* Search Bar */}
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search surveillance archive by title, camera tag, or file..."
          className="w-full bg-[#061112] border border-[#1a4447] rounded-xl pl-10 pr-9 py-2 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#15b89a] transition-colors"
        />
        {searchQuery && (
          <button
            onClick={() => onSearchChange('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Filter Pills & View Toggles */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* Source Pills (when enabled) */}
        {showSourceFilter && onSourceFilterChange && (
          <div className="flex items-center bg-[#061112] border border-[#1a4447] rounded-xl p-1">
            {sourceOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => onSourceFilterChange(opt.value)}
                className={`px-3 py-1 text-xs rounded-lg transition-all ${
                  sourceFilter === opt.value
                    ? 'bg-[#15b89a] text-slate-950 font-medium shadow-[0_0_12px_rgba(21,184,154,0.3)]'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        )}

        {/* Status Pills */}
        <div className="flex items-center bg-[#061112] border border-[#1a4447] rounded-xl p-1">
          {statusOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => onStatusChange(opt.value)}
              className={`px-3 py-1 text-xs rounded-lg transition-all ${
                statusFilter === opt.value
                  ? 'bg-[#15b89a] text-slate-950 font-medium shadow-[0_0_12px_rgba(21,184,154,0.3)]'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* View Mode Switcher (Grid / Table) */}
        <div className="flex items-center bg-[#061112] border border-[#1a4447] rounded-xl p-1">
          <button
            onClick={() => onViewModeChange('grid')}
            title="Grid View"
            className={`p-1.5 rounded-lg transition-colors ${
              viewMode === 'grid'
                ? 'bg-[#15b89a] text-slate-950'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <LayoutGrid className="w-4 h-4" />
          </button>
          <button
            onClick={() => onViewModeChange('table')}
            title="Table View"
            className={`p-1.5 rounded-lg transition-colors ${
              viewMode === 'table'
                ? 'bg-[#15b89a] text-slate-950'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <List className="w-4 h-4" />
          </button>
        </div>

        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={isLoading}
          title="Refresh Archive"
          className="p-2 rounded-xl bg-[#061112] border border-[#1a4447] text-slate-400 hover:text-[#2dd4bf] hover:border-[#15b89a] transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>
    </div>
  );
};

