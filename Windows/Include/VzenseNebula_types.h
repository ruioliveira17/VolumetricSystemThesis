#ifndef VZENSEDS_TYPES_H
#define VZENSEDS_TYPES_H

#include <stdint.h>
#include "VzenseNebula_enums.h"

#ifndef __cplusplus
#include <stdbool.h>
#endif

typedef uint16_t VzDepthPixel;  //!< Depth image pixel type in 16-bit
typedef uint16_t VzGray16Pixel; //!< Gray image pixel type in 16-bit
typedef uint8_t VzGray8Pixel;   //!< Gray image pixel type in 8-bit

#pragma pack (push, 1)
/**
 * @brief Color image pixel type in 24-bit RGB format.
 */
typedef struct
{
	uint8_t r;	//!< Red
	uint8_t g;	//!< Green
	uint8_t b;	//!< Blue
} VzRGB888Pixel;

/**
 * @brief Color image pixel type in 24-bit BGR format.
 */
typedef struct
{
	uint8_t b;	//!< Blue
	uint8_t g;	//!< Green
	uint8_t r;	//!< Red
} VzBGR888Pixel;

/**
 * @brief Stores the x, y, and z components of a 3D vector.
 */
typedef struct  
{
	float x, y, z;	//!< The x, y, and z components of the vector.
}VzVector3f;

/**
 * @brief Stores the x, y, and z components of a 2D vector.
 */
typedef struct
{
	uint16_t x;
	uint16_t y;
}VzVector2u16;

/**
 * @brief Contains depth information for a given pixel.
 */
typedef struct
{
	int          depthX;    //!< The x coordinate of the pixel.
	int          depthY;    //!< The y coordinate of the pixel.
	VzDepthPixel depthZ;    //!< The depth of the pixel, in millimeters.
}VzDepthVector3;

/**
 * @brief image resolution
 */
typedef struct {
    int width;
    int height;
}VzResolution;

/**
 * @brief Supported resolutions.
 */
typedef struct
{
    int count;
    VzResolution resolution[6];
}VzResolutionList;

/**
 * @brief Camera intrinsic parameters and distortion coefficients.
 */
typedef struct
{
	double	fx;  //!< Focal length x (pixel)
	double	fy;  //!< Focal length y (pixel)
	double	cx;  //!< Principal point x (pixel)
	double	cy;  //!< Principal point y (pixel)
	double	k1;  //!< Radial distortion coefficient, 1st-order
	double	k2;  //!< Radial distortion coefficient, 2nd-order
	double	p1;  //!< Tangential distortion coefficient
	double	p2;  //!< Tangential distortion coefficient
	double	k3;  //!< Radial distortion coefficient, 3rd-order
	double	k4;  //!< Radial distortion coefficient, 4st-order
	double	k5;  //!< Radial distortion coefficient, 5nd-order
	double	k6;  //!< Radial distortion coefficient, 6rd-order
}VzSensorIntrinsicParameters;

/** 
 * @brief Extrinsic parameters defines the physical relationship form tof sensor to color sensor
 */
typedef struct
{
	double rotation[9];     //!< Orientation stored as an array of 9 double representing a 3x3 rotation matrix.
	double translation[3];  //!< Location stored as an array of 3 double representing a 3-D translation vector.
}VzSensorExtrinsicParameters;

/**
 * @brief Depth/IR/Color image frame data.
 */
typedef struct
{
	uint32_t       frameIndex;          //!< The index of the frame.
	VzFrameType    frameType;           //!< The type of frame. See ::VzFrameType for more information.
	VzPixelFormat  pixelFormat;         //!< The pixel format used by a frame. See ::VzPixelFormat for more information.
	uint8_t*       pFrameData;          //!< A buffer containing the frame’s image data.
	uint32_t       dataLen;             //!< The length of pFrame, in bytes.
	float          exposureTime;        //!< The exposure time, in milliseconds.
    uint8_t        depthRange;          //!< The depth range mode of the current frame. Used only for depth frames.
	uint16_t       width;               //!< The width of the frame, in pixels.
	uint16_t       height;              //!< The height of the frame, in pixels.
    uint64_t       deviceTimestamp;     //!< The timestamp of the frame from the device.
}VzFrame;

typedef struct
{
	uint32_t depth : 1;
	uint32_t ir : 1;
	uint32_t color : 1;
	uint32_t transformedColor : 1;
	uint32_t transformedDepth : 1;
	uint32_t confidence : 1;
	uint32_t reserved : 26;
}VzFrameReady;

typedef void* VzDeviceHandle;

typedef struct
{
	char productName[64];
    char uri[256];
	char alias[64];
    char serialNumber[64];
    char ip[17];
	VzConnectStatus status;
}VzDeviceInfo;

typedef struct
{
	int threshold;//[0, 3],The larger the value is, the more obvious the filtering effect is and The smaller the point cloud wobble
    bool enable;
} VzTimeFilterParams;

typedef struct
{
	int threshold;//[0, 100],The larger the value is, the more obvious the filtering effect is and the more points are filtered out
    bool enable;
} VzConfidenceFilterParams;

typedef struct
{
    int	threshold;//[0, 49],The larger the value is, the more obvious the filtering effect is and the more points are filtered out
    bool enable;
} VzFlyingPixelFilterParams;

typedef struct
{
    VzExposureControlMode mode;
    int	exposureTime;              //When the control mode is AE,  exposureTime represents the maximum exposure time.
                                   //When the control mode is Manual, exposureTime represents the current exposure time.
} VzExposureTimeParams;
/**
 * @brief Error informations about the device
 */
typedef struct
{
    int errorCount;                     //The count of error messages, the maximum number is 10
    char errorMessage[10][64];          //The maximum length of each error message is 64(contains '\0').
} VzDeviceErrorInfo;

typedef struct
{	
	uint16_t width;                      //[1,65535],The width of input signal.
	uint16_t interval;                   //[34000,65535],The interval of input signal.
	uint8_t polarity;                    //[0,1],0 for active low, 1 for active high.
}VzInputSignalParamsForHWTrigger;        //Input signal parameters for Hardware Trigger.

typedef struct
{
	uint16_t width;                      //[1,65535],The width of output signal.
	uint16_t delay;                      //[0,65535],The delay time of output signal.
	uint8_t polarity;                    //[0,1],0 for active low, 1 for active high.
}VzOutputSignalParams;                   //Output signal parameters.

#pragma pack (pop)

/**
* @brief hotplug status callback function
* pInfo     return the info of the Device, See ::VzDeviceInfo
* state     0:device added , 1:device removed
* pUserData Pointer to user data, which can be null
*/
typedef void(*PtrHotPlugStatusCallback)(const VzDeviceInfo* pInfo, int state, void* pUserData);

typedef void(*PtrUpgradeStatusCallback)(int status, int params, void* pUserData);

#endif /* VZENSEDS_TYPES_H */
