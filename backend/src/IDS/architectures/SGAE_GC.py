import torch.nn as nn
import torch
from .gated_convolution import GatedConvolution

class SCAE_GC(nn.Module):
    def __init__(self, input_dim, cae1, cae2, cae3, gc_input_dim, gc_output_dim):
        super(SCAE_GC, self).__init__()
        self.cae1 = cae1
        self.cae2 = cae2
        self.cae3 = cae3
        self.gated_conv = GatedConvolution(gc_input_dim, gc_output_dim)
        self.classifier = nn.Linear(20, 12)

    def forward(self, x):
        x, _ = self.cae1(x)
        x, _ = self.cae2(x)
        x, _ = self.cae3(x)

        x = x.unsqueeze(2)
        
        x = self.gated_conv(x)
        
        x = x.view(x.size(0), -1)

        x = self.classifier(x)
        x = torch.softmax(x, dim=1)
        
        return x