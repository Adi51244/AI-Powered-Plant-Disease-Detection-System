#!/bin/bash
# Railway OpenCV Fix Script

export OPENCV_IO_ENABLE_OPENEXR=0
export QT_QPA_PLATFORM=offscreen
export DISPLAY=:99

# Start the application
exec "$@"
