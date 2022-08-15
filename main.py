import os
import PySpin
import sys
import datetime
from tkinter.filedialog import askdirectory  # For file select gui

NUM_IMAGES = 1  # number of images to grab


def list_available_node_names(nodemap: PySpin.CNodeMapPtr):
    """
    Every camera has an INodeMap and a TLDeviceNodeMap associated with it.
    This lists the names of all of the nodes of the given nodemap, which is usually enormous.

    Args:
        nodemap (INodeMap): the INodeMap or TLDeviceNodeMap of the camera,
    """
    nodes_list = nodemap.GetNodes()
    nodes_names = []
    for i in range(len(nodes_list)):
        if PySpin.IsAvailable(nodes_list[i]):
            nodes_names.append(nodes_list[i].GetName())
    print(nodes_names)


# *** NOTES ***
#
#  Setting the value of an enumeration node is slightly more complicated
#  than other node types. Two nodes must be retrieved: first, the
#  enumeration node is retrieved from the nodemap; and second, the entry
#  node is retrieved from the enumeration node. The integer value of the
#  entry node is then set as the new value of the enumeration node.
#
#  Notice that both the enumeration and the entry nodes are checked for
#  availability and readability/writability. Enumeration nodes are
#  generally readable and writable whereas their entry nodes are only
#  ever readable.
#
# Retrieve the enumeration node from nodemap
def change_enum_setting(cam: PySpin.CameraPtr, setting: str, choice: str):
    try:
        nodemap = cam.GetNodeMap()
        setting_ptr = PySpin.CEnumerationPtr(nodemap.GetNode(setting))
        if PySpin.IsAvailable(setting_ptr) and PySpin.IsWritable(setting_ptr):
            # print([entry.GetDisplayName() for entry in setting_ptr.GetEntries()])
            choice_ptr = PySpin.CEnumEntryPtr(setting_ptr.GetEntryByName(choice))
            if PySpin.IsAvailable(choice_ptr) and PySpin.IsReadable(choice_ptr):
                choice_value = choice_ptr.GetValue()
                setting_ptr.SetIntValue(choice_value)
                print(
                    "{setting} set to {choice}".format(
                        setting=setting_ptr.GetDisplayName(),
                        choice=choice_ptr.GetDisplayName(),
                    )
                )
            else:
                print(
                    "{choice} is not available...".format(
                        choice=choice_ptr.GetDisplayName()
                    )
                )
        else:
            print(
                "{setting} is not available...".format(
                    setting=setting_ptr.GetDisplayName()
                )
            )
    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)


def change_gain(cam: PySpin.CameraPtr, gain: float):
    """
    Set gain in dB
    """
    # Get camera nodemap
    nodemap = cam.GetNodeMap()

    # Turn off auto gain to allow setting manually
    node_gain_auto = PySpin.CEnumerationPtr(nodemap.GetNode("GainAuto"))
    if PySpin.IsAvailable(node_gain_auto) and PySpin.IsWritable(node_gain_auto):
        entry_gain_auto_off = node_gain_auto.GetEntryByName("Off")
        if PySpin.IsAvailable(entry_gain_auto_off) and PySpin.IsReadable(
            entry_gain_auto_off
        ):
            gain_auto_off = entry_gain_auto_off.GetValue()
            node_gain_auto.SetIntValue(gain_auto_off)

            # Set gain
            node_gain = PySpin.CFloatPtr(nodemap.GetNode("Gain"))
            if PySpin.IsAvailable(node_gain) and PySpin.IsWritable(node_gain):
                node_gain.SetValue(gain)
                print("Set gain to {}".format(gain))

            else:
                print("\nUnable to set Gain (float retrieval). Aborting...\n")
        else:
            print("\nUnable to set Gain Auto (entry retrieval). Aborting...\n")
    else:
        print("\nUnable to set Gain Auto (enumeration retrieval). Aborting...\n")


def configure_camera(cam: PySpin.CameraPtr, gain: float):
    """
    Configures a number of settings on the camera including offsets  X and Y, width,
    height, and pixel format. These settings must be applied before BeginAcquisition()
    is called; otherwise, they will be read only. Also, it is important to note that
    settings are applied immediately. This means if you plan to reduce the width and
    move the x offset accordingly, you need to apply such changes in the appropriate order.

    :param nodemap: GenICam nodemap.
    :type nodemap: INodeMap
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    nodemap = cam.GetNodeMap()

    try:
        result = True

        # Apply mono 16 pixel format
        change_enum_setting(cam, "PixelFormat", "Mono16")

        """
        # Apply minimum to offset X
        #
        # *** NOTES ***
        # Numeric nodes have both a minimum and maximum. A minimum is retrieved
        # with the method GetMin(). Sometimes it can be important to check
        # minimums to ensure that your desired value is within range.
        node_offset_x = PySpin.CIntegerPtr(nodemap.GetNode("OffsetX"))
        if PySpin.IsAvailable(node_offset_x) and PySpin.IsWritable(node_offset_x):

            node_offset_x.SetValue(node_offset_x.GetMin())
            print("Offset X set to %i..." % node_offset_x.GetMin())

        else:
            print("Offset X not available...")

        # Apply minimum to offset Y
        #
        # *** NOTES ***
        # It is often desirable to check the increment as well. The increment
        # is a number of which a desired value must be a multiple of. Certain
        # nodes, such as those corresponding to offsets X and Y, have an
        # increment of 1, which basically means that any value within range
        # is appropriate. The increment is retrieved with the method GetInc().
        node_offset_y = PySpin.CIntegerPtr(nodemap.GetNode("OffsetY"))
        if PySpin.IsAvailable(node_offset_y) and PySpin.IsWritable(node_offset_y):

            node_offset_y.SetValue(node_offset_y.GetMin())
            print("Offset Y set to %i..." % node_offset_y.GetMin())

        else:
            print("Offset Y not available...")
        """

        # Set maximum width
        #
        # *** NOTES ***
        # Other nodes, such as those corresponding to image width and height,
        # might have an increment other than 1. In these cases, it can be
        # important to check that the desired value is a multiple of the
        # increment. However, as these values are being set to the maximum,
        # there is no reason to check against the increment.
        node_width = PySpin.CIntegerPtr(nodemap.GetNode("Width"))
        if PySpin.IsAvailable(node_width) and PySpin.IsWritable(node_width):

            width_to_set = node_width.GetMax()
            node_width.SetValue(width_to_set)
            print("Width set to %i..." % node_width.GetValue())

        else:
            print("Width not available...")

        # Set maximum height
        #
        # *** NOTES ***
        # A maximum is retrieved with the method GetMax(). A node's minimum and
        # maximum should always be a multiple of its increment.
        node_height = PySpin.CIntegerPtr(nodemap.GetNode("Height"))
        if PySpin.IsAvailable(node_height) and PySpin.IsWritable(node_height):
            height_to_set = node_height.GetMax()
            node_height.SetValue(height_to_set)
            print("Height set to %i..." % node_height.GetValue())

        else:
            print("Height not available...")

        # Set triggering source
        # Trigger must be turned off before changes can be made to trigger settings
        change_enum_setting(cam, "TriggerMode", "Off")
        change_enum_setting(cam, "TriggerSource", "Line3")
        change_enum_setting(cam, "TriggerMode", "On")

        # Set global shutter
        change_enum_setting(cam, "SensorShutterMode", "GlobalReset")

        change_gain(cam, gain)

        # Set acquisition mode to single frame
        #
        #  *** NOTES ***
        #  Because the example acquires and saves 10 images, setting acquisition
        #  mode to continuous lets the example finish. If set to single frame
        #  or multiframe (at a lower number of images), the example would just
        #  hang. This would happen because the example has been written to
        #  acquire 10 images while the camera would have been programmed to
        #  retrieve less than that.

        change_enum_setting(cam, "AcquisitionMode", "SingleFrame")

    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        return False

    return result


def print_device_info(nodemap: PySpin.CNodeMapPtr):
    """
    This function prints the device information of the camera from the transport
    layer; please see NodeMapInfo example for more in-depth comments on printing
    device information from the nodemap.

    :param nodemap: Transport layer device nodemap.
    :type nodemap: INodeMap
    :returns: True if successful, False otherwise.
    :rtype: bool
    """

    print("*** DEVICE INFORMATION ***\n")

    try:
        result = True
        node_device_information = PySpin.CCategoryPtr(
            nodemap.GetNode("DeviceInformation")
        )

        if PySpin.IsAvailable(node_device_information) and PySpin.IsReadable(
            node_device_information
        ):
            features = node_device_information.GetFeatures()
            for feature in features:
                node_feature = PySpin.CValuePtr(feature)
                print(
                    "%s: %s"
                    % (
                        node_feature.GetName(),
                        node_feature.ToString()
                        if PySpin.IsReadable(node_feature)
                        else "Node not readable",
                    )
                )

        else:
            print("Device control information not available.")

    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        return False

    return result


def acquire_images(cam: PySpin.CameraPtr, directory: str):
    """
    This function acquires and saves images from a device.

    :param cam: Camera to acquire images from.
    :param nodemap: Device nodemap.
    :param nodemap_tldevice: Transport layer device nodemap.
    :type cam: CameraPtr
    :type nodemap: INodeMap
    :type nodemap_tldevice: INodeMap
    :return: True if successful, False otherwise.
    :rtype: bool
    """

    try:
        result = True

        #  Begin acquiring images
        #
        #  *** NOTES ***
        #  What happens when the camera begins acquiring images depends on the
        #  acquisition mode. Single frame captures only a single image, multi
        #  frame catures a set number of images, and continuous captures a
        #  continuous stream of images. Because the example calls for the
        #  retrieval of 10 images, continuous mode has been set.
        #

        print("Acquiring images...")

        #  Retrieve device serial number for filename
        #
        #  *** NOTES ***
        #  The device serial number is retrieved in order to keep cameras from
        #  overwriting one another. Grabbing image IDs could also accomplish
        #  this.
        nodemap_tldevice = cam.GetTLDeviceNodeMap()
        device_serial_number = ""
        node_device_serial_number = PySpin.CStringPtr(
            nodemap_tldevice.GetNode("DeviceSerialNumber")
        )
        if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(
            node_device_serial_number
        ):
            device_serial_number = node_device_serial_number.GetValue()
            print("Device serial number retrieved as %s..." % device_serial_number)

        # Retrieve, convert, and save images

        # Create ImageProcessor instance for post processing images
        processor = PySpin.ImageProcessor()

        # Set default image processor color processing method
        #
        # *** NOTES ***
        # By default, if no specific color processing algorithm is set, the image
        # processor will default to NEAREST_NEIGHBOR method.
        processor.SetColorProcessing(PySpin.HQ_LINEAR)

        for i in range(NUM_IMAGES):
            try:

                #  Retrieve next received image
                #
                #  *** NOTES ***
                #  Capturing an image houses images on the camera buffer. Trying
                #  to capture an image that does not exist will hang the camera.
                #
                #  *** LATER ***
                #  Once an image from the buffer is saved and/or no longer
                #  needed, the image must be released in order to keep the
                #  buffer from filling up.
                timeout = 10000  # milliseconds
                image_result = cam.GetNextImage(timeout)

                #  Ensure image completion
                #
                #  *** NOTES ***
                #  Images can easily be checked for completion. This should be
                #  done whenever a complete image is expected or required.
                #  Further, check image status for a little more insight into
                #  why an image is incomplete.
                if image_result.IsIncomplete():
                    print(
                        "Image incomplete with image status %d ..."
                        % image_result.GetImageStatus()
                    )

                else:

                    #  Print image information; height and width recorded in pixels
                    #
                    #  *** NOTES ***
                    #  Images have quite a bit of available metadata including
                    #  things such as CRC, image status, and offset values, to
                    #  name a few.
                    width = image_result.GetWidth()
                    height = image_result.GetHeight()
                    print(
                        "Grabbed Image %d, width = %d, height = %d" % (i, width, height)
                    )

                    #  Convert image to mono 8
                    #
                    #  *** NOTES ***
                    #  Images can be converted between pixel formats by using
                    #  the appropriate enumeration value. Unlike the original
                    #  image, the converted one does not need to be released as
                    #  it does not affect the camera buffer.
                    #
                    #  When converting images, color processing algorithm is an
                    #  optional parameter.
                    # Formats are listed in CameraDefs.h and in PySpin.py starting at about line 1600
                    """
                    image_converted = processor.Convert(
                        image_result, PySpin.PixelFormat_Mono8
                    )
                    """

                    # Create a unique filename
                    if device_serial_number:
                        filename = "RatKingReigns-%s-%d.png" % (
                            device_serial_number,
                            i,
                        )
                    else:  # if serial number is empty
                        filename = "RatKingReigns-%d.png" % i

                    # Save image
                    #
                    #  *** NOTES ***
                    #  The standard practice of the examples is to use device
                    #  serial numbers to keep images of one device from
                    #  overwriting those of another.
                    image_result.Save(directory + "/" + filename, PySpin.PNG)
                    print("Image saved at %s" % filename)

                    #  Release image
                    #
                    #  *** NOTES ***
                    #  Images retrieved directly from the camera (i.e. non-converted
                    #  images) need to be released in order to keep from filling the
                    #  buffer.
                    image_result.Release()
                    print("")

            except PySpin.SpinnakerException as ex:
                print("Error: %s" % ex)
                cam.EndAcquisition()
                return False

    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        return False

    return result


def capture(cam_list: PySpin.CameraList):
    """
    This function acts as the body of the example; please see NodeMapInfo example
    for more in-depth comments on setting up cameras.

    :param cam: Camera to run on.
    :type cam: CameraPtr
    :return: True if successful, False otherwise.
    :rtype: bool
    """

    try:
        result = True

        config_file = open("input.tsv", mode="r")
        lines = config_file.readlines()
        config_file.close()

        # Configure cameras
        for i, cam in enumerate(cam_list):
            # Retrieve TL device nodemap and print device information
            nodemap_tldevice = cam.GetTLDeviceNodeMap()

            result &= print_device_info(nodemap_tldevice)

            serial_number = PySpin.CStringPtr(
                nodemap_tldevice.GetNode("DeviceSerialNumber")
            ).GetValue()  # Returns a GCString, which is a wrapper to std::string
            print("\n*** CONFIGURING CAMERA %s *** \n", serial_number)

            for i, line in enumerate(lines):
                if line.split("\t")[0] == "DeviceSerialNumber":
                    if line.split("\t")[1] == serial_number:
                        if lines[i + 1].split("\t")[0] == "Gain":
                            gain = lines[i + 1].split("\t")[1][:-1]
                        else:
                            raise ValueError("Gain should follow serial number")
            try:
                gain
            except NameError:
                print("Gain isn't defined for {}".format(serial_number))

            # Initialize camera
            cam.Init()

            # Retrieve GenICam nodemap
            nodemap = cam.GetNodeMap()

            # Configure custom image settings
            if not configure_camera(cam, gain):
                return False

        # Acquire images
        # Image acquisition must be ended when no more images are needed.
        folder_date = datetime.datetime.now()
        folder_name = (
            folder_date.strftime("%Y")
            + "-"
            + folder_date.strftime("%m")
            + "-"
            + folder_date.strftime("%d")
            + " "
            + folder_date.strftime("%H")
            + "-"
            + folder_date.strftime("%M")
            + "-"
            + folder_date.strftime("%S")
        )
        directory = askdirectory() + "/" + folder_name
        os.mkdir(directory)

        for cam in cam_list:
            cam.BeginAcquisition()
        for i, cam in enumerate(cam_list):
            result &= acquire_images(cam, directory)

        # Deinitialize cameras
        # End acquisition
        #  Ending acquisition appropriately helps ensure that devices clean up
        #  properly and do not need to be power-cycled to maintain integrity.
        for cam in cam_list:
            cam.EndAcquisition()
            cam.DeInit()

    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        result = False

    return result


def main():
    """
    Example entry point; please see Enumeration example for more in-depth
    comments on preparing and cleaning up the system.

    :return: True if successful, False otherwise.
    :rtype: bool
    """

    # Since this application saves images in the current folder
    # we must ensure that we have permission to write to this folder.
    # If we do not have permission, fail right away.
    try:
        test_file = open("test.txt", "w+")
    except IOError:
        print("Unable to write to current directory. Please check permissions.")
        input("Press Enter to exit...")
        return False

    test_file.close()
    os.remove(test_file.name)

    result = True

    # Retrieve singleton reference to system object
    system = PySpin.System.GetInstance()

    # Get current library version
    version = system.GetLibraryVersion()
    print(
        "Library version: %d.%d.%d.%d"
        % (version.major, version.minor, version.type, version.build)
    )

    # Retrieve list of cameras from the system
    cam_list = system.GetCameras()

    num_cameras = cam_list.GetSize()

    print("Number of cameras detected: %d" % num_cameras)

    # Finish if there are no cameras
    if num_cameras == 0:

        # Clear camera list before releasing system
        cam_list.Clear()

        # Release system instance
        system.ReleaseInstance()

        print("Not enough cameras!")
        return False

    for cam in cam_list:
        cam.Init()
        print(cam)

    # Run example on each camera
    result &= capture(cam_list)

    for cam in cam_list:

        # Deinitialize camera
        cam.DeInit()

        # Release reference to camera
        # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being automatically
        # cleaned up when going out of scope.
        # The usage of del is preferred to assigning the variable to None.
        del cam

    # Clear camera list before releasing system
    cam_list.Clear()

    # Release system instance
    system.ReleaseInstance()

    return result


if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
