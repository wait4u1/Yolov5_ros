#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from numpy.lib.utils import source
import numpy as np
import cv2
import random
import torch
import time
import rospy
from sensor_msgs.msg import Image
from std_msgs.msg import Header
from cv_bridge import CvBridge
from yolov5_ros.msg import BoundingBox


class Yolo_Dect:
    def __init__(self):

        weight_path = rospy.get_param('/weight_path', '')
        image_topic = rospy.get_param(
            '/image_topic', '/camera/color/image_raw')
        pub_topic = rospy.get_param('/pub_topic', '/yolov5/BoundingBoxes')
        conf = rospy.get_param('conf', '0.5')

        self.model = torch.hub.load('ultralytics/yolov5', 'custom',
                                    path=weight_path, force_reload=False)

        self.model.conf = 0.5
        self.bridge = CvBridge()
        self.color_image = Image()
        self.depth_image = Image()

        # image subscribe
        self.color_sub = rospy.Subscriber(image_topic, Image, self.image_callback,
                                          queue_size=1, buff_size=52428800)

        # Output publishers
        self.position_pub = rospy.Publisher(
            pub_topic,  BoundingBox, queue_size=1)

        self.image_pub = rospy.Publisher(
            '/yolov5/detection_image',  Image, queue_size=1)

    def image_callback(self, image):
        self.color_image = np.frombuffer(image.data, dtype=np.uint8).reshape(
            image.height, image.width, -1)
        self.color_image = cv2.cvtColor(self.color_image, cv2.COLOR_BGR2RGB)
        results = self.model(self.color_image)
        boxs = results.pandas().xyxy[0].values
        self.dectshow(self.color_image, boxs)

        cv2.waitKey(3)

    def dectshow(self, org_img, boxs):
        img = org_img.copy()

        count = 0
        for i in boxs:
            count += 1

        for box in boxs:
            cv2.rectangle(img, (int(box[0]), int(box[1])),
                          (int(box[2]), int(box[3])), (0, 255, 0), 2)
            cv2.putText(img, box[-1],
                        (int(box[0]), int(box[1])), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            boundingBox = BoundingBox()
            boundingBox.probability = box[4]
            boundingBox.xmin = box[0]
            boundingBox.ymin = box[1]
            boundingBox.xmax = box[2]
            boundingBox.ymax = box[3]
            boundingBox.num = count
            boundingBox.Class = box[-1]
            self.position_pub.publish(boundingBox)
        self.publish_image(img)
        cv2.imshow('YOLOv5', img)

    def publish_image(self, imgdata):
        image_temp = Image()
        header = Header(stamp=rospy.Time.now())
        header.frame_id = 'map'
        image_temp.height = 480
        image_temp.width = 640
        image_temp.encoding = 'bgr8'
        image_temp.data = np.array(imgdata).tobytes()
        image_temp.header = header
        image_temp.step = 1920
        self.image_pub.publish(image_temp)


def main():
    rospy.init_node('yolov5_ros', anonymous=True)
    yolo_dect = Yolo_Dect()
    rospy.spin()


if __name__ == "__main__":

    main()
