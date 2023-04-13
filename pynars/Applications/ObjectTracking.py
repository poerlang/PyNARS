import cv2
import numpy as np
from matplotlib import pyplot as plt

from pynars.NARS.DataStructures import Memory
from pynars.NARS.InferenceEngine import GeneralEngine
from pynars.Narsese import parser

dist = [5, 8, 10]
HOG_diff = 0.006


def encode(vec):
    # encode a vector of movement into a description
    R = (vec[0] ** 2 + vec[1] ** 2) ** 0.5  # radius
    code = ""
    if vec[0] < 0:
        code += "L"
    else:
        code += "R"
    if vec[1] < 0:
        code += "U"
    else:
        code += "D"
    if R < dist[0] ** 2:
        code += "C"
    elif R < dist[1] ** 2:
        code += "M"
    else:
        code += "F"
    return code


def decode(code):
    tmp = ""
    if code[0] == "L":
        tmp += "left_"
    else:
        tmp += "right_"
    if code[1] == "U":
        tmp += "up_"
    else:
        tmp += "down_"
    if code[2] == "C":
        tmp += "close"
    elif code[2] == "M":
        tmp += "mid"
    else:
        tmp += "far"
    return parser.parse("<(*, new_frame, " + tmp + ") --> position>.")


def in_Narsese(speed):
    tasks = []
    R = (speed[0] ** 2 + speed[1] ** 2) ** 0.5  # radius
    if R < dist[0] ** 2:
        tasks.append("<(*, object, slow) --> speed>")
    elif R < dist[1] ** 2:
        tasks.append("<(*, object, mid) --> speed>")
    else:
        tasks.append("<(*, object, high) --> speed>")
    if speed[0] < 0:
        if speed[1] < 0:
            tasks.append("<(*, object, left_up) --> direction>")
        else:
            tasks.append("<(*, object, left_down) --> direction>")
    else:
        if speed[1] < 0:
            tasks.append("<(*, object, right_up) --> direction>")
        else:
            tasks.append("<(*, object, right_down) --> direction>")
    return parser.parse("(&|, " + ", ".join(tasks) + ").")


def encode_Narsese(word):
    if word == "<left_down_far-->(/, position, new_frame, _)>":
        return "LDF"
    elif word == "<left_down_mid-->(/, position, new_frame, _)>":
        return "LDM"
    elif word == "<left_down_close-->(/, position, new_frame, _)>":
        return "LDC"
    elif word == "<left_up_far-->(/, position, new_frame, _)>":
        return "LUF"
    elif word == "<left_up_mid-->(/, position, new_frame, _)>":
        return "LUM"
    elif word == "<left_up_close-->(/, position, new_frame, _)>":
        return "LUC"
    elif word == "<right_down_far-->(/, position, new_frame, _)>":
        return "RDF"
    elif word == "<right_down_mid-->(/, position, new_frame, _)>":
        return "RDM"
    elif word == "<right_down_close-->(/, position, new_frame, _)>":
        return "RDC"
    elif word == "<right_up_far-->(/, position, new_frame, _)>":
        return "RUF"
    elif word == "<right_up_mid-->(/, position, new_frame, _)>":
        return "RUM"
    elif word == "<right_up_close-->(/, position, new_frame, _)>":
        return "RUC"
    else:
        return None


def move(anchor_belief, code):
    ret = [anchor_belief[0], anchor_belief[1]]  # deep copy
    if code[2] == "C":
        speed = dist[0] ** 0.5
    elif code[2] == "M":
        speed = dist[1] ** 0.5
    else:
        speed = dist[2] ** 0.5
    if code[0] == "L":
        if code[1] == "U":
            ret[0] -= speed
            ret[1] -= speed
        else:
            ret[0] -= speed
            ret[1] += speed
    else:
        if code[1] == "U":
            ret[0] += speed
            ret[1] -= speed
        else:
            ret[0] += speed
            ret[1] += speed
    return [int(ret[0]), int(ret[1])]


# Create a video capture object
cap = cv2.VideoCapture("C:\\Users\\TORY\\Downloads\\pexels-pixabay-855565-1920x1080-24fps.mp4")
# cap = cv2.VideoCapture("C:\\Users\\TORY\\Downloads\\pexels-suika-chan-4562551-1280x720-30fps.mp4")

# memory
memory = Memory(100)

# reasoner
reasoner = GeneralEngine()

# background knowledge
f = open("./background_knowledge.txt")
for each_line in f.readlines():
    memory.accept(parser.parse(each_line))

# Create a MOSSE tracker
tracker = cv2.legacy.TrackerMOSSE_create()

# Read the first frame of the video
success, frame = cap.read()

# Select a region of interest (ROI) to track
bbox = cv2.selectROI(frame, False)
anchor_belief = [bbox[0], bbox[1]]

# initial HOG
initial_image_patch = frame[bbox[1]:bbox[1] + bbox[3], bbox[0]:bbox[0] + bbox[2], :]
initial_image_patch = np.resize(initial_image_patch, (128, 128, 3))
initial_image_patch_shape = initial_image_patch.shape
HOG = cv2.HOGDescriptor()
initial_HOG_feature = HOG.compute(initial_image_patch)

# Initialize the tracker with the first frame and ROI
tracker.init(frame, bbox)

# visualize the quality of tracking
MSE = []

# initial guess of the next position of tracking, symbolically
anchor_expected = "LDC"

# Loop through the rest of the frames
while True:

    occluded = False

    # Read a new frame from the video
    success, frame = cap.read()

    # If we have reached the end of the video, break out of the loop
    if not success:
        break

    # Update the tracker with the new frame
    success, bbox = tracker.update(frame)
    bbox = [int(i) for i in bbox]
    anchor_tracker = [bbox[0], bbox[1]]

    # If the tracker was successful, draw the bounding box around the tracked object
    if success:

        vec = [anchor_tracker[0] - anchor_belief[0], anchor_tracker[1] - anchor_belief[1]]
        code = encode(vec)
        image_patch = frame[bbox[1]:bbox[1] + bbox[3], bbox[0]:bbox[0] + bbox[2], :]
        image_patch = np.resize(image_patch, initial_image_patch_shape)
        HOG_feature = HOG.compute(image_patch)
        if code != anchor_expected:
            # the b-box by the tracker is inconsistent with my expectation
            # whether my expectation is wrong or the tracker is unreliable
            print(np.square(HOG_feature - initial_HOG_feature).mean(axis=0))
            if np.square(HOG_feature - initial_HOG_feature).mean(axis=0) < HOG_diff:
                # print("!!!!!!")
                # HOG feature dif is small, so my expectation is wrong.
                memory.accept(decode(code))
                new_anchor_belief = move(anchor_belief, code)
                # print(code)
            else:
                # print("------")
                # The tracker is not correct
                memory.accept(decode(anchor_expected))
                new_anchor_belief = move(anchor_belief, anchor_expected)
                # print(anchor_expected)
        else:
            # the b-box by the tracker is consistent with my expectation
            if np.square(HOG_feature - initial_HOG_feature).mean(axis=0) < HOG_diff:
                # print("------")
                # nothing is wrong, perfect
                memory.accept(decode(code))
                new_anchor_belief = move(anchor_belief, code)
                # print(code)
            else:
                # print("------")
                # the object is occluded
                memory.accept(decode(code))
                memory.accept(parser.parse("<object --> occluded>. :|:"))
                occluded = True
                new_anchor_belief = move(anchor_belief, code)
                # print(code)

        # translate the current situation in Narsese, and put it in the memory
        speed = [new_anchor_belief[0] - anchor_belief[0], new_anchor_belief[1] - anchor_belief[1]]
        memory.accept(in_Narsese(speed))

        # ask questions
        memory.accept(parser.parse("<(*, new_frame, #x) --> position>?"))

        # system cycles
        changed = False
        for _ in range(10):  # for each cycle
            if changed:
                break
            concept = memory.take(remove=True)
            if concept is not None:
                tasks_inference_derived, _ = reasoner.step(concept)
                for each in tasks_inference_derived:
                    tmp = encode_Narsese(each.term.word)
                    if tmp is not None:
                        anchor_expected = tmp
                        changed = True
                        break
                memory.put_back(concept)

        if not changed:  # default value
            anchor_expected = "LDC"

        # print(anchor_expected)

        # draw the expected anchor
        if not occluded:
            frame = cv2.circle(frame, (new_anchor_belief[0], new_anchor_belief[1]), 30, (0, 0, 255), thickness=30)
        else:
            frame = cv2.circle(frame, (new_anchor_belief[0], new_anchor_belief[1]), 30, (0, 255, 0), thickness=30)
        anchor_belief = new_anchor_belief

        # current HOG
        image_patch = frame[int(bbox[1]):int(bbox[1]) + int(bbox[3]), int(bbox[0]):int(bbox[0]) + int(bbox[2]), :]
        image_patch = np.resize(image_patch, initial_image_patch_shape)
        HOG_feature = HOG.compute(image_patch)
        MSE.append(np.square(HOG_feature - initial_HOG_feature).mean(axis=0))

        # draw the bbox by the tracker
        x, y, w, h = [int(i) for i in bbox]
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        center_x, center_y = x + w // 2, y + h // 2
        frame = cv2.circle(frame, (center_x, center_y), 30, (0, 0, 255))

    # Display the frame with the tracked object
    cv2.imshow('Frame', frame)

    # Exit if the user presses the 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
cap.release()
cv2.destroyAllWindows()

plt.figure()
plt.grid()
plt.plot(MSE)
plt.show()
