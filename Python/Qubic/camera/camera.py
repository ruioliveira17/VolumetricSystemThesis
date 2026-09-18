from abc import ABC, abstractmethod


class Camera(ABC):

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def get_frames(self):
        pass

    @abstractmethod
    def set_fps(self, fps):
        pass

    @abstractmethod
    def set_exposureTime(self, value):
        pass

    @abstractmethod
    def set_enableHDR(self, value):
        pass

    @abstractmethod
    def set_hdr_interval(self, low, high):
        pass

    @abstractmethod
    def get_depth_intrinsic_parameters(self):
        pass

    @abstractmethod
    def get_rgb_intrinsic_parameters(self):
        pass

    @abstractmethod
    def set_filter_flyingPixel(self, value):
        pass

    @abstractmethod
    def set_filter_fillHole(self, value):
        pass

    @abstractmethod
    def set_filter_spatial(self, value):
        pass

    @abstractmethod
    def set_filter_confidence(self, value):
        pass