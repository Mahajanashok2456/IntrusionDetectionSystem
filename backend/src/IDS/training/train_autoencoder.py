import torch
import logging
from tqdm import tqdm

def train_cae(cae, train_loader, num_epochs, learning_rate=0.0001, device='cuda'):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    cae = cae.to(device)
    optimizer = torch.optim.Adam(cae.parameters(), lr=learning_rate)
    
    logging.info("Contractive Autoencoder training started successfully.")
    
    for epoch in range(num_epochs):
        running_loss = 0
        cae.train()
        
        try:
            for batch in tqdm(train_loader, desc=f"Epoch {epoch + 1}/{num_epochs}", leave=False):
                inputs, _ = batch
                inputs = inputs.to(device)
                inputs.requires_grad_(True)
                optimizer.zero_grad()
                
                h, x_reconstructed = cae(inputs)
                loss = cae.loss_function(inputs, x_reconstructed, h)
                loss.backward()
                optimizer.step()
                
                running_loss += loss.item()
        except Exception as e:
            logging.error(f"Error in epoch {epoch + 1}: {str(e)}")
            continue
    
    logging.info("Training completed")
    
    return cae