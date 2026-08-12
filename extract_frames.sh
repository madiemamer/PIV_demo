#!/usr/bin/env bash
#
# extract_frames.sh -- break a video into individual frame images with ffmpeg
#
# Usage:
#   ./extract_frames.sh <input_video> [output_dir] [fps]
#
# Examples:
#   ./extract_frames.sh piv_uvspeed_video.mp4
#       -> extracts every frame into ./frames/frame_00001.png ...
#
#   ./extract_frames.sh piv_uvspeed_video.mp4 my_frames
#       -> extracts every frame into ./my_frames/frame_00001.png ...
#
#   ./extract_frames.sh piv_uvspeed_video.mp4 my_frames 2
#       -> extracts 2 frames per second of video (instead of every frame)
#
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <input_video> [output_dir] [fps]"
    exit 1
fi

INPUT="$1"
OUTDIR="${2:-frames}"
FPS="${3:-}"   # empty = extract every frame at the video's native rate

if [ ! -f "$INPUT" ]; then
    echo "Error: input file not found: $INPUT"
    exit 1
fi

if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg not found on PATH."
    echo "Install it with: sudo apt install ffmpeg"
    exit 1
fi

mkdir -p "$OUTDIR"

# Extract every single frame at the video's native frame rate
ffmpeg -i "$INPUT" "$OUTDIR/frame_%05d.png"

N=$(ls "$OUTDIR"/frame_*.png 2>/dev/null | wc -l | tr -d ' ')
echo "Wrote $N frames to $OUTDIR/"