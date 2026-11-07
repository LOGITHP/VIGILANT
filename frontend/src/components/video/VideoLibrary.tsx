import React, { useState, useEffect, useCallback } from 'react';
import {
  Film,
  Upload,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Radio,
  FolderArchive,
  Monitor
} from 'lucide-react';
import { Video, VideoFilterParams, VideoSourceType } from '../../types/video';
import { videoApi } from '../../services/videoApi';
import { VideoFilterBar } from './VideoFilterBar';
import { VideoCard } from './VideoCard';
import { VideoTableView } from './VideoTableView';

interface VideoLibraryProps {
  onPlayVideo: (video: Video) => void;
  onNavigateToUpload: () => void;
  onNavigateToLive?: () => void;
  sourceType?: VideoSourceType | 'ALL';
  title?: string;
  description?: string;
  showSourceFilter?: boolean;
}

export const VideoLibrary: React.FC<VideoLibraryProps> = ({
  onPlayVideo,
  onNavigateToUpload,
  onNavigateToLive,
  sourceType = 'ALL',
  title,
  description,
  showSourceFilter = false,
}) => {
  const [videos, setVideos] = useState<Video[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sourceFilter, setSourceFilter] = useState<'LIVE' | 'UPLOADED' | 'ALL'>(sourceType);
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');

  useEffect(() => {
    setSourceFilter(sourceType);
    setPage(1);
  }, [sourceType]);

  const fetchVideos = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params: VideoFilterParams = {
        page,
        limit: viewMode === 'grid' ? 12 : 15,
        q: searchQuery.trim() || undefined,
        status: statusFilter,
        source_type: sourceFilter !== 'ALL' ? sourceFilter : undefined,
      };
      const res = await videoApi.getVideos(params);
      setVideos(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err: unknown) {
      setError('Failed to load surveillance footage. Please check your connection.');
    } finally {
      setIsLoading(false);
    }
  }, [page, viewMode, searchQuery, statusFilter, sourceFilter]);

  useEffect(() => {
    fetchVideos();
  }, [fetchVideos]);

  const handleDelete = async (id: string) => {
    try {
      await videoApi.deleteVideo(id);
      fetchVideos();
    } catch (err) {
      alert('Failed to delete video. Please check permissions.');
    }
  };

  const getHeaderIcon = () => {
    if (sourceFilter === 'LIVE') {
      return (
        <div className="w-10 h-10 rounded-xl bg-rose-950/70 border border-rose-800/60 flex items-center justify-center text-rose-400 shadow-[0_0_15px_rgba(244,63,94,0.25)]">
          <Radio className="w-5 h-5 animate-pulse" />
        </div>
      );
    }
    return (
      <div className="w-10 h-10 rounded-xl bg-[#0e2729] border border-[#194042] flex items-center justify-center text-[#2dd4bf] shadow-[0_0_15px_rgba(45,212,191,0.2)]">
        <FolderArchive className="w-5 h-5" />
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Archive Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#122e30]">
        <div className="flex items-center gap-3.5">
          {getHeaderIcon()}
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-lg font-medium text-slate-100 tracking-wide">
                {title || (sourceFilter === 'LIVE' ? 'Live CCTV Surveillance Archive' : sourceFilter === 'UPLOADED' ? 'Uploaded Video Archive' : 'All Surveillance Footage Archive')}
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#0a2022] text-[#2dd4bf] border border-[#164346]">
                {total} {total === 1 ? 'RECORDING' : 'RECORDINGS'}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {description || (sourceFilter === 'LIVE'
                ? 'Continuous 24/7 stream recordings and incident event clips captured directly from CCTV feeds.'
                : sourceFilter === 'UPLOADED'
                ? 'Manually ingested evidence clips, patrol logs, and external surveillance video files.'
                : 'Master index of all archived surveillance footage, stream recordings, and manual evidence.')}
            </p>
          </div>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <VideoFilterBar
        searchQuery={searchQuery}
        onSearchChange={(q) => {
          setSearchQuery(q);
          setPage(1);
        }}
        statusFilter={statusFilter}
        onStatusChange={(status) => {
          setStatusFilter(status);
          setPage(1);
        }}
        sourceFilter={sourceFilter}
        onSourceFilterChange={(src) => {
          setSourceFilter(src);
          setPage(1);
        }}
        showSourceFilter={showSourceFilter}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        onRefresh={fetchVideos}
        isLoading={isLoading}
      />

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-red-950/60 border border-red-800 text-red-300 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400 gap-3">
          <Loader2 className="w-8 h-8 text-[#2dd4bf] animate-spin" />
          <p className="text-sm font-mono tracking-wider">RETRIEVING SURVEILLANCE ARCHIVE...</p>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && videos.length === 0 && (
        <div className="border border-dashed border-[#14373a] rounded-3xl p-16 text-center bg-[#071315]/40 flex flex-col items-center justify-center">
          <div className="w-16 h-16 rounded-2xl bg-[#0d2629] border border-[#1a4447] flex items-center justify-center text-[#2dd4bf] mb-4">
            {sourceFilter === 'LIVE' ? (
              <Radio className="w-8 h-8 text-rose-400 opacity-80" />
            ) : (
              <Film className="w-8 h-8 opacity-70" />
            )}
          </div>
          <h3 className="text-lg font-medium text-slate-100 mb-1">
            {sourceFilter === 'LIVE'
              ? 'No Live Camera Recordings Found'
              : sourceFilter === 'UPLOADED'
              ? 'No Uploaded Surveillance Footage Found'
              : 'No Surveillance Footage Found'}
          </h3>
          <p className="text-sm text-slate-400 max-w-sm mb-6 leading-relaxed">
            {searchQuery || statusFilter !== 'ALL'
              ? 'No footage matches your search or filter parameters. Try clearing your filters.'
              : sourceFilter === 'LIVE'
              ? 'There are currently no recordings captured from live CCTV streams. Connect your cameras or trigger a live recording clip.'
              : 'There are currently no uploaded video files in this archive. Ingest your first surveillance recording file.'}
          </p>
          <div className="flex items-center gap-3">
            {sourceFilter === 'LIVE' && onNavigateToLive && (
              <button
                onClick={onNavigateToLive}
                className="px-5 py-2.5 rounded-xl bg-[#15b89a] hover:bg-[#2dd4bf] text-slate-950 font-semibold text-sm flex items-center gap-2 shadow-[0_0_15px_rgba(21,184,154,0.3)] transition-all"
              >
                <Monitor className="w-4 h-4" />
                Go to Live CCTV Grid
              </button>
            )}
            <button
              onClick={onNavigateToUpload}
              className="px-5 py-2.5 rounded-xl bg-[#0e2a2c] hover:bg-[#133c3f] border border-[#1b4b4e] text-[#2dd4bf] font-semibold text-sm flex items-center gap-2 transition-all"
            >
              <Upload className="w-4 h-4" />
              Upload Surveillance Video
            </button>
          </div>
        </div>
      )}

      {/* Video Content Grid or Table */}
      {!isLoading && videos.length > 0 && (
        <>
          {viewMode === 'grid' ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
              {videos.map((video) => (
                <VideoCard
                  key={video.id}
                  video={video}
                  onPlay={onPlayVideo}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          ) : (
            <VideoTableView
              videos={videos}
              onPlay={onPlayVideo}
              onDelete={handleDelete}
            />
          )}

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-[#14373a] pt-4 text-xs font-mono text-slate-400">
              <div>
                Showing {(page - 1) * (viewMode === 'grid' ? 12 : 15) + 1} to{' '}
                {Math.min(page * (viewMode === 'grid' ? 12 : 15), total)} of {total} recordings
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(p - 1, 1))}
                  disabled={page === 1}
                  className="p-2 rounded-lg bg-[#0a1819] border border-[#14373a] hover:border-[#15b89a] disabled:opacity-40 transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span>
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                  disabled={page === totalPages}
                  className="p-2 rounded-lg bg-[#0a1819] border border-[#14373a] hover:border-[#15b89a] disabled:opacity-40 transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};


