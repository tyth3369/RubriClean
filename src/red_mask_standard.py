"""
RubriClean Standard — 标准版
基于 Senior 算法改进: R-G>15 & R-B>15 + 白色填充
适合一般情况，几乎不误伤印刷字体
"""
import cv2
import numpy as np

CONFIG_STANDARD = {
    "min_diff": 15,        # R 必须同时大于 G 和 B 的最小差值
    "blue_h_low": 100,     # 蓝色 HSV 范围 (用于蓝笔清除)
    "blue_s_low": 70,
    "blue_v_low": 50,
    "blue_h_high": 130,
    "blue_s_high": 255,
    "blue_v_high": 255,
}


def detect_red_standard(img, config=None):
    """标准版红笔检测：R-G>min_diff & R-B>min_diff"""
    cfg = config or CONFIG_STANDARD
    r = img[:, :, 2].astype(np.int16)
    g = img[:, :, 1].astype(np.int16)
    b = img[:, :, 0].astype(np.int16)
    diff = cfg["min_diff"]
    mask = (r - g > diff) & (r - b > diff)
    return mask.astype(np.uint8) * 255


def detect_blue_standard(img, config=None):
    """标准版蓝笔检测：HSV 蓝色范围"""
    cfg = config or CONFIG_STANDARD
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower = np.array([cfg["blue_h_low"], cfg["blue_s_low"], cfg["blue_v_low"]])
    upper = np.array([cfg["blue_h_high"], cfg["blue_s_high"], cfg["blue_v_high"]])
    return cv2.inRange(hsv, lower, upper)


def white_fill(img, mask):
    """白色填充修复"""
    white = np.ones_like(img) * 255
    return np.where(mask[:, :, np.newaxis] > 0, white, img)
