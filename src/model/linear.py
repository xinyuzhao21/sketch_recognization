import torch.nn as nn
import torch.nn.functional as F
import torch

class ClassificationNet(nn.Module):
    def __init__(self, insize, n_classes):
        super(ClassificationNet, self).__init__()
        self.net1 = nn.Sequential(
            nn.Linear(insize, 200),
            nn.ReLU(inplace=True),
            nn.Linear(200, n_classes)

        )

    def forward(self, x):
        # x = torch.cat((output1,output2),1)
        output = self.net1(x)
        return output