import os
import pandas as pd
import torch
import logging
import argparse
from torch.utils.data import DataLoader, random_split
from ..preprocessing.preprocess import Preprocessor
from .train_autoencoder import train_cae
from ..architectures.auto_encoder import ContractiveAutoEncoder
from ..architectures.SGAE_GC import SCAE_GC
from .train_SGAE_GC import train_scae_gc_model
from .utils.datasets import CustomDataset, TensorDataset
import json
import pickle
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_args():
    parser = argparse.ArgumentParser(description='Train SCAE-GC model with custom data path')
    parser.add_argument('--data_path', type=str, default=config.DATA_PATH, 
                       help='Path to the training data CSV file')
    return parser.parse_args()

def save_model_weights(models, model_names, save_dir):
    try:
        os.makedirs(save_dir, exist_ok=True)
        for model, name in zip(models, model_names):
            path = os.path.join(save_dir, f"{name}.pth")
            torch.save(model.state_dict(), path)
            logging.info(f"Model {name} saved successfully at {path}")
    except Exception as e:
        logging.error(f"Error in saving models: {e}")
        raise

def save_preprocessor(preprocessor, save_path):
    try:
        with open(save_path, 'wb') as f:
            pickle.dump(preprocessor, f)
        logging.info(f"Preprocessor saved successfully at {save_path}")
    except Exception as e:
        logging.error(f"Error in saving preprocessor: {e}")
        raise

def save_mapping(mapping, save_path):
    try:
        with open(save_path, 'w') as f:
            json.dump(mapping, f, indent=4)
        logging.info(f"Label mapping saved successfully at {save_path}")
    except Exception as e:
        logging.error(f"Error in saving label mapping: {e}")
        raise

def map_types_to_numbers(series, types):
    type_to_number = {type_name: i for i, type_name in enumerate(types)}
    return series.map(type_to_number).values, type_to_number

def create_dataset(cae, loader, device):
    cae.eval()
    features_list, labels_list = [], []
    with torch.no_grad():
        for features, labels in loader:
            features, labels = features.to(device), labels.to(device)
            h, _ = cae(features)
            features_list.append(h.cpu())
            labels_list.append(labels.cpu())
    return DataLoader(TensorDataset(torch.cat(features_list), torch.cat(labels_list)), batch_size=config.IDS_BATCH_SIZE, shuffle=True)

def main(custom_data_path=None):
    """
    Main training function that can be called programmatically
    
    Args:
        custom_data_path: Optional path to custom training data
    """
    # Determine data path
    if custom_data_path:
        DATA_PATH = custom_data_path
        logging.info(f"Using custom data path: {DATA_PATH}")
    else:
        if __name__ == "__main__":
            args = parse_args()
            DATA_PATH = args.data_path
        else:
            DATA_PATH = config.DATA_PATH
    
    try:
        preprocessor = Preprocessor(config.OUTPUT_PATH)
        df = pd.read_csv(DATA_PATH)
        logging.info(f"Loading training data from: {DATA_PATH}")
        logging.info(f"Dataset shape: {df.shape}")
        preprocessor.load_train_data(df, 'class')
        preprocessor.process()
        final_features, labels = preprocessor.train_df, preprocessor.train_labels
        logging.info(f"Data loaded and processed successfully. Shape: {final_features.shape}")
        logging.info(f"Labels: {labels.unique()}")
    except Exception as e:
        logging.error(f"Error in preprocessing: {e}")
        raise

    mapped_result, mapping = map_types_to_numbers(pd.Series(labels), labels.unique())

    dataset = CustomDataset(final_features, mapped_result)
    total_size = len(dataset)
    train_size = int(config.TRAIN_RATIO * total_size)
    test_size = total_size - train_size
    train_dataset, test_dataset = random_split(dataset, [train_size, test_size])
    train_loader = DataLoader(train_dataset, batch_size=config.IDS_BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=config.IDS_BATCH_SIZE, shuffle=False)
    logging.info("DataLoader created successfully.")

    # Initialize and train autoencoders
    CAE_LAYERS = [(37, 80), (80, 40), (40, 20)]
    autoencoders = [ContractiveAutoEncoder(in_dim, out_dim) for in_dim, out_dim in CAE_LAYERS]

    try:
        data_loader = train_loader
        trained_autoencoders = []
        for cae in autoencoders:
            trained_cae = train_cae(cae, data_loader, config.EPOCHS, config.LEARNING_RATE, config.DEVICE)
            trained_autoencoders.append(trained_cae)
            data_loader = create_dataset(trained_cae, data_loader, config.DEVICE)
        logging.info("All autoencoders trained successfully.")
    except Exception as e:
        logging.error(f"Error in training autoencoders: {e}")
        raise

    try:
        scae_gc = SCAE_GC(37, *trained_autoencoders, 20, 20)
        trained_model = train_scae_gc_model(scae_gc, train_loader, config.EPOCHS, config.LEARNING_RATE, config.DEVICE)
        logging.info("SCAE-GC model trained successfully.")
    except Exception as e:
        logging.error(f"Error in training SCAE-GC model: {e}")
        raise

    model_list = trained_autoencoders + [trained_model]
    model_names = ["CAE1", "CAE2", "CAE3", "SCAE_GC"]
    save_model_weights(model_list, model_names, config.MODEL_SAVE_PATH)
    save_preprocessor(preprocessor, config.PREPROCESSOR_SAVE_PATH)
    save_mapping(mapping, config.MAPPING_SAVE_PATH)
    
    logging.info("Training completed successfully!")

if __name__ == "__main__":
    main()
