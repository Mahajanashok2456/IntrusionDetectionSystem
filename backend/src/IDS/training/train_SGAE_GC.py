import torch
import logging
import torch.nn as nn
from tqdm import tqdm
from sklearn.metrics import precision_score, recall_score

import torch
import torch.nn as nn

class FocalLoss(nn.Module):
    def __init__(self, gamma=2.0, alpha=0.25, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.gamma = gamma
        self.alpha = alpha
        self.reduction = reduction

    def forward(self, inputs, targets):
        """
        Args:
            inputs: Tensor of shape [batch_size, num_classes]
            targets: Tensor of shape [batch_size]
        """
        # Convert targets to one-hot encoding
        num_classes = inputs.size(-1)
        targets_one_hot = torch.zeros_like(inputs)
        targets_one_hot.scatter_(1, targets.unsqueeze(1), 1)

        # Apply softmax to get probabilities
        probs = torch.softmax(inputs, dim=-1)
        
        # Calculate focal loss
        focal_loss = -self.alpha * (1 - probs) ** self.gamma * targets_one_hot * torch.log(probs + 1e-7)
        
        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss

def train_scae_gc_model(scae_gc_model, train_loader, num_epochs, learning_rate, device):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    scae_gc_model.to(device)
    
    logging.info("SGAE_GC training started successfully.")
    
    for cae in [scae_gc_model.cae1, scae_gc_model.cae2, scae_gc_model.cae3]:
        for param in cae.parameters():
            param.requires_grad = False

    optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, scae_gc_model.parameters()), lr=learning_rate)
    criterion = FocalLoss(gamma=2.0, alpha=0.25)

    for epoch in range(num_epochs):
        scae_gc_model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        all_labels = []
        all_predictions = []

        try:
            for batch in tqdm(train_loader, desc=f"Epoch {epoch + 1}/{num_epochs}", leave=False):
                inputs, labels = batch
                
                # Map any label >= 12 to 0
                labels = torch.where(labels >= 12, torch.tensor(0), labels)
                
                inputs = inputs.float().to(device)
                labels = labels.long().to(device)
                
                optimizer.zero_grad()
                outputs = scae_gc_model(inputs)
                
                # Debug information
                logging.debug(f"Inputs shape: {inputs.shape}")
                logging.debug(f"Labels shape: {labels.shape}")
                logging.debug(f"Outputs shape: {outputs.shape}")
                
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()

                running_loss += loss.item()
                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()
                
                all_labels.extend(labels.cpu().numpy())
                all_predictions.extend(predicted.cpu().numpy())
                
            # Calculate metrics
            epoch_loss = running_loss / len(train_loader)
            accuracy = 100. * correct / total
            precision = precision_score(all_labels, all_predictions, average='weighted')
            recall = recall_score(all_labels, all_predictions, average='weighted')
            
            logging.info(f"Epoch {epoch + 1}/{num_epochs}")
            logging.info(f"Loss: {epoch_loss:.4f}")
            logging.info(f"Accuracy: {accuracy:.2f}%")
            logging.info(f"Precision: {precision:.4f}")
            logging.info(f"Recall: {recall:.4f}")
            
        except Exception as e:
            logging.error(f"Error in epoch {epoch + 1}: {str(e)}")
            logging.error(f"Label: {labels}")
            continue

    logging.info("Training completed")
    return scae_gc_model