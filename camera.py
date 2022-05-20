import cv2
from turbojpeg import TurboJPEG
import time
import asyncio
from fastapi.logger import logger

# Required libs: ffmeg, libgtk-3-0, libopenjp2-7, libatlas-base-dev, libsrtp2-dev
# Required packages: pytuyrbojpeg

jpeg = TurboJPEG()

class CameraStream:
    QUALITY_HIGH="high"
    QUALITY_MEDIUM = "medium"
    QUALITY_LOW = "low"
    FPS = 30
    SHOW_FPS = False
    
    def __init__(self, device_num) -> None:
        # Initialize video capture for auto detected camera (device_num=-1) or any specified
        self.cap = cv2.VideoCapture(device_num, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_CONVERT_RGB, 0)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 10)
        self.cap.set(cv2.CAP_PROP_FPS, CameraStream.FPS)

        if not self.cap.isOpened():
            raise RuntimeError('cannot open camera')
        
        self.__reset_frame_time()
        self.set_quality(CameraStream.QUALITY_MEDIUM)
        
        # Show values of the camera properties
        logger.info("CAP_PROP_FOURCC:", self.cap.get(cv2.CAP_PROP_FOURCC))
        logger.info("CAP_PROP_FRAME_WIDTH:", self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        logger.info("CAP_PROP_FRAME_HEIGHT:",  self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logger.info("CAP_PROP_FPS:", self.cap.get(cv2.CAP_PROP_FPS))
        logger.info("CAP_PROP_POS_MSEC:", self.cap.get(cv2.CAP_PROP_POS_MSEC))
        logger.info("CAP_PROP_FRAME_COUNT:", self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        logger.info("CAP_PROP_BRIGHTNESS:", self.cap.get(cv2.CAP_PROP_BRIGHTNESS))
        logger.info("CAP_PROP_CONTRAST:", self.cap.get(cv2.CAP_PROP_CONTRAST))
        logger.info("CAP_PROP_SATURATION:", self.cap.get(cv2.CAP_PROP_SATURATION))
        logger.info("CAP_PROP_HUE:", self.cap.get(cv2.CAP_PROP_HUE))
        logger.info("CAP_PROP_GAIN:", self.cap.get(cv2.CAP_PROP_GAIN))
        logger.info("CAP_PROP_CONVERT_RGB:", self.cap.get(cv2.CAP_PROP_CONVERT_RGB))
        
    def set_quality(self, q):
        if q == CameraStream.QUALITY_LOW:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        elif q == CameraStream.QUALITY_MEDIUM:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        elif q == CameraStream.QUALITY_HIGH:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.quality = q
    
    def get_quality(self):
        return self.quality

    def __del__(self):
        self.cap.release()

    def __reset_frame_time(self):
        self.start_time = time.time()
        self.num_frames = 0
    
    def __aiter__(self):
        return self
    
    # Next frame
    async def __anext__(self):
        # Read frame data
        encode_start = time.time()
        ret, encoded_image = self.cap.read()
        encode_end = time.time()
        
        if not ret:
            raise StopAsyncIteration

        # Calculate FPS
        self.num_frames += 1
        duration = time.time()-self.start_time
        if duration >= 1:
            if CameraStream.SHOW_FPS:
                logger.info("FPS:", self.num_frames)
            self.__reset_frame_time()
        
        # Return frame
        await asyncio.sleep(1/CameraStream.FPS-(encode_end - encode_start))
        return encoded_image.tobytes()
