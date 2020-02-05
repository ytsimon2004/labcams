from ximea import xiapi
from .cams import *

class XimeaCam(GenericCam):
    def __init__(self,
                 camId = None,
                 outQ = None,
                 binning = 2,
                 exposure = 20000,
                 triggerSource = np.uint16(2),
                 outputs = ['XI_GPO_EXPOSURE_ACTIVE'],
                 triggered = Event(),
                 **kwargs):
        super(XimeaCam,self).__init__()
        self.drivername = 'Ximea'
        if camId is None:
            display('[Ximea] - Need to supply a camera ID.')
        self.cam_id = camId
        self.triggered = triggered
        self.queue = outQ
        self.outputs = outputs
        self.binning = binning
        self.exposure = exposure
        frame = self.get_one()

        self.h = frame.shape[0]
        self.w = frame.shape[1]
        self.nchannels = 1
        self.dtype = np.uint16
        self._init_variables(self.dtype)
        self.triggerSource = triggerSource
        self.img[:] = np.reshape(frame,self.img.shape)[:]

        display("[Ximea {0}] - got info from camera.".format(self.cam_id))

    def _init_controls(self):
        self.ctrevents = dict(
            exposure=dict(
                function = 'set_exposure',
                widget = 'float',
                variable = 'exposure',
                units = 'ms',
                type = 'int',
                min = 1,
                max = 10000000000,
                step = 10))
    
    def get_one(self):
        self._cam_init()
        self.cam.start_acquisition()
        self.cam.get_image(self.cambuf)
        frame = self.cambuf.get_image_data_numpy()
        self.cam.stop_acquisition()
        self.cam.close_device()
        self.cam = None
        self.cambuf = None
        return frame
    
    def set_exposure(self,exposure = 20000):
        '''Set the exposure time is in us'''
        self.exposure = exposure
        if not self.cam is None:
            if self.cam_is_running:
                self.start_trigger.set()
                self.stop_trigger.set()

    def _cam_init(self,set_gpio=True):
        self.cam = xiapi.Camera()
        #start communication
        self.cam.open_device()
        self.cam.set_acq_timing_mode('XI_ACQ_TIMING_MODE_FREE_RUN')
        self.cam.set_exposure(self.exposure)
        self.cam.set_binning_vertical(self.binning)
        self.cam.set_binning_horizontal(self.binning)
        # Set the GPIO
        self.cam.set_gpi_selector('XI_GPI_PORT1')
        self.cam.set_trigger_source('XI_TRG_OFF')

        if set_gpio:
            self.cam.set_gpo_selector('XI_GPO_PORT1')
            # for now set the GPO to blink in software (port1 will do that for sync purposes, the test cam does not support XI_GPO_EXPOSURE_PULSE)
            self.cam.set_gpo_mode('XI_GPO_ON'); #XI_GPO_EXPOSURE_PULSE
            if self.triggered.is_set():
                self.cam.set_gpi_mode('XI_GPI_TRIGGER')
                self.cam.set_trigger_source('XI_TRG_EDGE_RISING')
        self.cam.set_led_selector('XI_LED_SEL1')
        self.cam.set_led_mode('XI_LED_OFF')
        self.cam.set_led_selector('XI_LED_SEL2')
        self.cam.set_led_mode('XI_LED_OFF')
        self.cam.set_led_selector('XI_LED_SEL3')
        self.cam.set_led_mode('XI_LED_OFF')
        self.cambuf = xiapi.Image()
        self.lastframeid = -1
        self.nframes.value = 0
        self.camera_ready.set()

    def _cam_startacquisition(self):
        self.cam.start_acquisition()

    def _cam_loop(self):
        try:
            self.cam.get_image(self.cambuf)
        except xiapi.Xi_error:
            return
        frame = self.cambuf.get_image_data_numpy()
        frameID = self.cambuf.nframe
        timestamp = self.cambuf.tsUSec
        if self.saving.is_set():
            self.was_saving = True
            if not frameID == self.lastframeid :
                self.queue.put((frame.copy(),
                                (frameID,timestamp)))
        elif self.was_saving:
            self.was_saving = False
            self.queue.put(['STOP'])
        if not frameID == self.lastframeid:
            self.buf[:] = np.reshape(frame.copy(),self.buf.shape)[:]
            self.cam.set_gpo_mode('XI_GPO_OFF'); #XI_GPO_EXPOSURE_PULSE
            time.sleep(0.001)
            self.cam.set_gpo_mode('XI_GPO_ON'); #XI_GPO_EXPOSURE_PULSE
            self.nframes.value += 1
        self.lastframeid = frameID
        
    def _cam_close(self):
        self.cam.stop_acquisition()
        self.cam.close_device()
        self.cam = None        
