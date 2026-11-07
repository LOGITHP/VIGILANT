import re
from typing import Optional, Tuple, List, Dict, Any


class MetadataNormalizer:

    @staticmethod
    def parse_rational_number(val: Optional[str]) -> Tuple[Optional[float], Optional[str]]:
        """
        Parse rational string such as '30000/1001' or '25/1' into (float_val, rational_str).
        Protects against zero division, '0/0', 'N/A', and malformed fractions.
        """
        if not val or not isinstance(val, str) or val in ("0/0", "N/A", "0"):
            return None, None

        val = val.strip()
        if "/" in val:
            parts = val.split("/", 1)
            try:
                num = float(parts[0].strip())
                den = float(parts[1].strip())
                if den == 0.0 or num == 0.0:
                    return None, None
                return round(num / den, 4), f"{int(num) if num.is_integer() else num}/{int(den) if den.is_integer() else den}"
            except (ValueError, ZeroDivisionError):
                return None, None

        # Direct float string (e.g. '29.97')
        try:
            f = float(val)
            if f <= 0:
                return None, None
            return round(f, 4), f"{val}/1"
        except ValueError:
            return None, None

    @staticmethod
    def parse_float_safe(val: Any) -> Optional[float]:
        if val is None:
            return None
        try:
            f = float(val)
            return round(f, 4)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def parse_int_safe(val: Any) -> Optional[int]:
        if val is None:
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    @classmethod
    def select_primary_video_stream(cls, streams: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Identify the primary video stream.
        Explicitly rejects static cover art / thumbnail picture streams (disposition.attached_pic == 1),
        and prioritizes default flags and highest resolution.
        """
        candidates: List[Dict[str, Any]] = []

        for stream in streams:
            if stream.get("codec_type") != "video":
                continue

            disposition = stream.get("disposition") or {}
            # Exclude attached pictures (e.g. MP3/MP4 album art / cover frame)
            if disposition.get("attached_pic") == 1 or stream.get("attached_pic") == 1:
                continue

            # Exclude timed thumbnails
            if disposition.get("timed_thumbnails") == 1:
                continue

            candidates.append(stream)

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        # Priority 1: Marked as explicit default stream
        default_streams = [s for s in candidates if (s.get("disposition") or {}).get("default") == 1]
        if len(default_streams) == 1:
            return default_streams[0]

        # Priority 2: Highest pixel resolution (width * height)
        def get_pixel_area(s: Dict[str, Any]) -> int:
            w = cls.parse_int_safe(s.get("width")) or 0
            h = cls.parse_int_safe(s.get("height")) or 0
            return w * h

        candidates.sort(key=get_pixel_area, reverse=True)
        return candidates[0]

    @classmethod
    def select_primary_audio_stream(cls, streams: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Identify the primary audio stream, if present."""
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
        if not audio_streams:
            return None

        default_audio = [s for s in audio_streams if (s.get("disposition") or {}).get("default") == 1]
        if default_audio:
            return default_audio[0]

        return audio_streams[0]

    @classmethod
    def build_stream_catalog(
        cls,
        streams: List[Dict[str, Any]],
        primary_video_idx: Optional[int],
        primary_audio_idx: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Catalog and summarize all streams within the container."""
        catalog = []
        for s in streams:
            idx = cls.parse_int_safe(s.get("index"))
            if idx is None:
                continue

            stype = s.get("codec_type", "unknown").lower()
            disposition = s.get("disposition") or {}
            is_attached = disposition.get("attached_pic") == 1 or s.get("attached_pic") == 1
            is_default = disposition.get("default") == 1
            is_primary = (stype == "video" and idx == primary_video_idx) or (stype == "audio" and idx == primary_audio_idx)

            fps_eval, rational_fps = cls.parse_rational_number(s.get("r_frame_rate") or s.get("avg_frame_rate"))

            item = {
                "stream_index": idx,
                "stream_type": stype,
                "codec_name": s.get("codec_name"),
                "codec_long_name": s.get("codec_long_name"),
                "is_primary": is_primary,
                "is_default": is_default,
                "is_attached_pic": is_attached,
                "width": cls.parse_int_safe(s.get("width")),
                "height": cls.parse_int_safe(s.get("height")),
                "fps": fps_eval,
                "rational_fps": rational_fps,
                "pixel_format": s.get("pix_fmt"),
                "time_base": s.get("time_base"),
                "sample_rate": cls.parse_int_safe(s.get("sample_rate")),
                "channels": cls.parse_int_safe(s.get("channels")),
                "channel_layout": s.get("channel_layout"),
                "duration_seconds": cls.parse_float_safe(s.get("duration")),
                "bitrate": cls.parse_int_safe(s.get("bit_rate")),
                "disposition": disposition,
                "stream_metadata": s.get("tags") or {}
            }
            catalog.append(item)
        return catalog
