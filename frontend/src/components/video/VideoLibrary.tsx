import React, { useState, useEffect, useCallback } from 'react';
import {
  Film,
  Upload,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Loader2
} from 'lucide-react';
import { Video, VideoFilterParams } from '../../types/video';
import { videoApi } from '../../services/videoApi';
import { VideoFilterBar } from './VideoFilterBar';
import { VideoCard } from './VideoCard';
import { VideoTableView } from './VideoTableView';

interface VideoLibraryProps {
  onPlayVideo: (video: Video) => void;
  onNavigateToUpload: () => void;
}

export const VideoLibrary: React.FC<VideoLibraryProps> = ({
  onPlayVideo,
  onNavigateToUpload,
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
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');

  const fetchVideos = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params: VideoFilterParams = {
        page,
        limit: viewMode === 'grid' ? 12 : 15,
        q: searchQuery.trim() || undefined,
        status: statusFilter,
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
  }, [page, viewMode, searchQuery, statusFilter]);

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

  return (
    <div className="space-y-6">
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
            <Film className="w-8 h-8 opacity-70" />
          </div>
          <h3 className="text-lg font-medium text-slate-100 mb-1">No Surveillance Footage Found</h3>
          <p className="text-sm text-slate-400 max-w-sm mb-6 leading-relaxed">
            {searchQuery || statusFilter !== 'ALL'
              ? 'No footage matches your search or filter parameters. Try clearing your filters.'
              : 'There are currently no recorded surveillance videos in the MinIO archive. Ingest your first CCTV recording.'}
          </p>
          <button
            onClick={onNavigateToUpload}
            className="px-5 py-2.5 rounded-xl bg-[#15b89a] hover:bg-[#2dd4bf] text-slate-950 font-semibold text-sm flex items-center gap-2 shadow-[0_0_15px_rgba(21,184,154,0.3)] transition-all"
          >
            <Upload className="w-4 h-4" />
            Upload Video Footage
          </button>
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
