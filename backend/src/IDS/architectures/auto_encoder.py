import torch.nn as nn
import torch.nn.functional as F
import torch

class ContractiveAutoEncoder(nn.Module):
    def __init__(self, input_dim, hidden_dim, contraction_penalty=1e-4):
        super(ContractiveAutoEncoder, self).__init__()
        self.encoder = nn.Linear(input_dim, hidden_dim)
        self.decoder = nn.Linear(hidden_dim, input_dim)
        self.contraction_penalty = contraction_penalty
        nn.init.xavier_uniform_(self.encoder.weight)
        nn.init.xavier_uniform_(self.decoder.weight)

    def forward(self, x):
        h = torch.sigmoid(self.encoder(x))
        x_reconstructed = self.decoder(h)
        return h, x_reconstructed

    def loss_function(self, x, x_reconstructed, h):
        mse_loss = F.mse_loss(x_reconstructed, x, reduction="mean")
        
        jacobian = torch.autograd.grad(
            outputs=h.sum(), 
            inputs=x,
            grad_outputs=torch.ones_like(h.sum()),
            retain_graph=True,
            create_graph=True
        )[0]
    
        jacobian_norm = torch.sum(jacobian ** 2)
        
        return mse_loss + self.contraction_penalty * jacobian_norm