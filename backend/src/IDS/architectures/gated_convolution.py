import torch.nn as nn
import torch

class GatedConvolution(nn.Module):
    def __init__(self, input_dim, output_dim, kernel_size=3):
        super(GatedConvolution, self).__init__()
        self.conv1 = nn.Conv1d(input_dim, output_dim, kernel_size, padding=1, stride=1)
        self.conv2 = nn.Conv1d(input_dim, output_dim, kernel_size, padding=1, stride=1)
        nn.init.xavier_uniform_(self.conv1.weight)
        nn.init.xavier_uniform_(self.conv2.weight)

    def forward(self, x):
        A = self.conv1(x)
        B = torch.sigmoid(self.conv2(x))
        return A * B