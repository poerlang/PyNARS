import cv2
import numpy as np
import torch
from torchvision import datasets, transforms

transform = transforms.Compose([transforms.ToTensor(),
                                transforms.Resize([28, 28])])

data_train = datasets.MNIST(root="C:/Users/TORY/OneDrive - Temple University/AGI research/NARS_Optimizer/data/",
                            transform=transform,
                            train=True,
                            download=True)

data_test = datasets.MNIST(root="C:/Users/TORY/OneDrive - Temple University/AGI research/NARS_Optimizer/data/",
                           transform=transform,
                           train=False)

dataloader_train = torch.utils.data.DataLoader(dataset=data_train,
                                               batch_size=1,
                                               shuffle=True)

dataloader_test = torch.utils.data.DataLoader(dataset=data_test,
                                              batch_size=1,
                                              shuffle=True)


def MNIST_num(num, num_train, num_test, dataloader_train, dataloader_test, shape):
    """
    num now is a list of numbers expected in the learning process. e.g., [0, 1, 2, 3, 4]
    """
    ret_train = []
    ret_test = []
    for x, y in dataloader_train:
        if len(ret_train) == num_train:
            break
        if y in num:
            x = cv2.resize(np.array(x).squeeze(), shape)
            x = np.reshape(x, (shape[0] * shape[1]))
            x = x.reshape(shape)
            # x = np.array([True if each > 0.5 else False for each in x]).reshape(shape)
            ret_train.append((x, y))
    for x, y in dataloader_test:
        if len(ret_test) == num_test:
            break
        if y in num:
            x = cv2.resize(np.array(x).squeeze(), shape)
            x = np.reshape(x, (shape[0] * shape[1]))
            x = x.reshape(shape)
            # x = np.array([True if each > 0.5 else False for each in x]).reshape(shape)
            ret_test.append((x, y))
    return ret_train, ret_test
