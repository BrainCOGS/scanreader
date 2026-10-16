"""Tests for picking the scan class from the header layout.

ScanImage 2021 and 2022 already write the field names that NewerScanPost2023 reads
(hMotors.samplePosition, hStackManager.numVolumes, stackMode/stackActuator), so the
scan class can not be chosen from VERSION_MAJOR alone. These tests write small
synthetic ScanImage TIFFs, so they need no data files.
"""

import json
import shutil
import tempfile
import unittest
import unittest.mock
from os import path

import numpy as np
import tifffile

import scanreader
from scanreader import core, scans
from scanreader.exceptions import ScanImageVersionError

NUM_FRAMES = 3
ROI_HEIGHT, ROI_WIDTH = 8, 16
NUM_FLY_TO_LINES = (
    2  # ceil(flytoTimePerScanfield / seconds_per_line), even when bidirectional
)


def make_header(
    version,
    layout,
    multiroi=False,
    slow_stack=False,
    num_volumes="50",
    position="[1 2 3]",
):
    """ScanImage header (TIFF Software tag) with the fields scanreader reads.

    Args:
        layout: 'legacy' (hFastZ.numVolumes, hMotors.motorPosition) or 'post2023'
            (hStackManager.numVolumes, hMotors.samplePosition), or 'none' for neither.
        position: Value of motorPosition/samplePosition; None leaves it out.
    """
    lines = [
        f"SI.VERSION_MAJOR = {version}",
        "SI.VERSION_MINOR = 1",
        "SI.hChannels.channelSave = 1",
        "SI.hFastZ.enable = {}".format("false" if slow_stack else "true"),
        f"SI.hRoiManager.mroiEnable = {1 if multiroi else 0}",
        "SI.hStackManager.zs = {}".format("0" if multiroi else "[10 50]"),
        f"SI.hStackManager.framesPerSlice = {NUM_FRAMES if slow_stack else 1}",
        "SI.hScan2D.bidirectional = true",
        "SI.hScan2D.scannerFrequency = 7935.9",
        "SI.hScan2D.scannerType = 'RG'",
        "SI.hScan2D.fillFractionSpatial = 0.9",
        "SI.hScan2D.fillFractionTemporal = 0.7",
        "SI.hScan2D.logAverageFactor = 1",
        "SI.hScan2D.flytoTimePerScanfield = 0.0001",
        "SI.hScan2D.flybackTimePerFrame = 0.001",
        "SI.hRoiManager.linePeriod = 0.0001",
        "SI.hRoiManager.scanVolumeRate = 10",
        "SI.hRoiManager.scanZoomFactor = 1",
        "SI.hRoiManager.scanAngleMultiplierFast = 1",
        "SI.hRoiManager.scanAngleMultiplierSlow = 1",
        "SI.hRoiManager.imagingFovUm = [-300 -300;300 -300;300 300;-300 300]",
        "SI.objectiveResolution = 15",
    ]
    if layout == "legacy":
        lines += [
            f"SI.hFastZ.numVolumes = {num_volumes}",
            "SI.hStackManager.slowStackWithFastZ = false",
        ]
        if position is not None:
            lines.append(f"SI.hMotors.motorPosition = {position}")
    elif layout == "post2023":
        lines += [
            f"SI.hStackManager.numVolumes = {num_volumes}",
            "SI.hStackManager.stackMode = '{}'".format(
                "slow" if slow_stack else "fast"
            ),
            "SI.hStackManager.stackActuator = 'fastZ'",
        ]
        if position is not None:
            lines.append(f"SI.hMotors.samplePosition = {position}")
    elif layout != "none":
        raise ValueError(layout)
    return "\n".join(lines)


def make_roi_groups():
    """Two side-by-side ROIs, each a single scanfield present at every depth."""

    def roi(x):
        return {
            "zs": 0,
            "discretePlaneMode": 0,
            "scanfields": {
                "pixelResolutionXY": [ROI_WIDTH, ROI_HEIGHT],
                "centerXY": [x, 0],
                "sizeXY": [2, 1],
            },
        }

    return {"RoiGroups": {"imagingRoiGroup": {"rois": [roi(-1), roi(1)]}}}


def write_scan(filename, header, multiroi=False):
    """Write a synthetic ScanImage TIFF. Pixel values are the page index."""
    if multiroi:
        num_pages, height, width = (
            NUM_FRAMES,
            2 * ROI_HEIGHT + NUM_FLY_TO_LINES,
            ROI_WIDTH,
        )
        extratags = [(315, "s", 0, json.dumps(make_roi_groups()), True)]  # Artist
    else:
        num_pages, height, width = 2 * NUM_FRAMES, 4, 6  # 2 depths
        extratags = []
    data = np.broadcast_to(
        np.arange(num_pages, dtype=np.int16)[:, None, None], (num_pages, height, width)
    )
    tifffile.imwrite(
        filename,
        np.ascontiguousarray(data),
        photometric="minisblack",
        description="frameNumbers = 1",
        software=header,
        metadata=None,
        extratags=extratags,
    )


class HeaderLayoutTest(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp_dir)
        self.num_files = 0

    def read(self, header, multiroi=False):
        self.num_files += 1
        filename = path.join(self.tmp_dir, f"scan_{self.num_files}.tif")
        write_scan(filename, header, multiroi=multiroi)
        scan = scanreader.read_scan(filename)
        self.addCleanup(delattr, scan, "tiff_files")  # closes the open TiffFiles
        return scan

    def test_uses_post2023_header(self):
        self.assertTrue(core.uses_post2023_header(make_header("2022", "post2023")))
        self.assertTrue(
            core.uses_post2023_header(make_header("2022", "post2023", position=None))
        )
        self.assertFalse(core.uses_post2023_header(make_header("2021", "legacy")))
        self.assertFalse(core.uses_post2023_header(make_header("2021", "none")))
        self.assertFalse(core.uses_post2023_header(""))

    def test_post2023_layout_before_2023(self):
        for version in ["2021", "2022", "2023"]:
            with self.subTest(version=version):
                scan = self.read(make_header(version, "post2023"))
                self.assertIsInstance(scan, scans.NewerScanPost2023)
                self.assertEqual(scan.version, version)
                self.assertEqual(scan.num_requested_frames, 50)
                self.assertEqual(scan.motor_position_at_zero, [1, 2, 3])
                self.assertIsNone(scan.initial_secondary_z)
                self.assertIs(scan.is_slow_stack_with_fastZ, False)
                self.assertEqual(scan.num_fields, 2)
                self.assertEqual(scan.num_frames, NUM_FRAMES)
                self.assertEqual(scan.shape, (2, 4, 6, 1, NUM_FRAMES))
                self.assertEqual(scan[1, 0, 0, 0, 2], 5)  # depth 1 of frame 2 is page 5

    def test_legacy_layout(self):
        for version in ["2020", "2021", "2022"]:
            with self.subTest(version=version):
                scan = self.read(make_header(version, "legacy"))
                self.assertNotIsInstance(scan, scans.NewerScanPost2023)
                self.assertEqual(scan.num_requested_frames, 50)
                self.assertEqual(scan.motor_position_at_zero, [1, 2, 3])
                self.assertIs(scan.is_slow_stack_with_fastZ, False)
                self.assertEqual(scan.shape, (2, 4, 6, 1, NUM_FRAMES))

    def test_post2023_layout_corner_cases(self):
        scan = self.read(
            make_header("2022", "post2023", num_volumes="Inf", position="[0 0 0 -25.5]")
        )
        self.assertEqual(scan.num_requested_frames, int(1e9))
        self.assertEqual(scan.motor_position_at_zero, [0, 0, 0])
        self.assertEqual(scan.initial_secondary_z, -25.5)

        scan = self.read(make_header("2022", "post2023", position=None))
        self.assertIsInstance(scan, scans.NewerScanPost2023)
        self.assertIsNone(scan.motor_position_at_zero)
        self.assertIsNone(scan.initial_secondary_z)

        # slow stacks read framesPerSlice in both layouts
        scan = self.read(make_header("2022", "post2023", slow_stack=True))
        self.assertEqual(scan.num_requested_frames, NUM_FRAMES)
        self.assertIs(scan.is_slow_stack_with_fastZ, True)

    def test_no_layout_fields_keeps_version_class(self):
        scan = self.read(make_header("2022", "none"))
        self.assertNotIsInstance(scan, scans.NewerScanPost2023)
        self.assertIsNone(scan.num_requested_frames)
        self.assertIsNone(scan.motor_position_at_zero)

    def test_multiroi_post2023_layout_before_2023(self):
        for version in ["2021", "2022", "2023"]:
            with self.subTest(version=version):
                scan = self.read(
                    make_header(version, "post2023", multiroi=True), multiroi=True
                )
                self.assertIsInstance(scan, scans.ScanMultiROIPost2023)
                self.assertEqual(scan.num_requested_frames, 50)
                self.assertEqual(scan.motor_position_at_zero, [1, 2, 3])
                self.assertEqual(scan.num_rois, 2)
                self.assertEqual(scan.field_heights, [ROI_HEIGHT, ROI_HEIGHT])
                self.assertEqual(scan[1].shape, (ROI_HEIGHT, ROI_WIDTH, 1, NUM_FRAMES))
                self.assertEqual(scan[1][0, 0, 0, 2], 2)

    def test_multiroi_legacy_layout(self):
        # Legacy multiROI scans read RoiGroups from tifffile's scanimage_metadata,
        # which a synthetic file does not have, so feed the ROIs in directly.
        roi_infos = make_roi_groups()["RoiGroups"]["imagingRoiGroup"]["rois"]
        with unittest.mock.patch.object(
            scans.ScanMultiROI, "_read_roi_infos", return_value=roi_infos
        ):
            scan = self.read(
                make_header("2021", "legacy", multiroi=True), multiroi=True
            )
        self.assertIs(type(scan), scans.ScanMultiROI)
        self.assertEqual(scan.motor_position_at_zero, [1, 2, 3])

    def test_unknown_version_still_rejected(self):
        with self.assertRaises(ScanImageVersionError):
            self.read(make_header("2099", "post2023"))


if __name__ == "__main__":
    unittest.main()
