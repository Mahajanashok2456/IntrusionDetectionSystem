import logging
import pickle
import os
from ..architectures.data_sampler import DataSampler
from ..architectures.generator import Generator
import torch
from .utils.sample import sample
import pandas as pd
import config

def generate_samples(num_samples: int, batch_size: int = 50):
    """Generates synthetic data using the trained GAN."""
    logging.info("Loading transformer and generator for sample generation...")
    
    # Check if required model files exist
    if not os.path.exists(config.TRANSFORMER_PATH):
        raise FileNotFoundError(f"CTGAN transformer model not found at {config.TRANSFORMER_PATH}. Please train the CTGAN model first.")
    
    if not os.path.exists(config.MODEL_PATH):
        raise FileNotFoundError(f"CTGAN generator model not found at {config.MODEL_PATH}. Please train the CTGAN model first.")
    
    if not os.path.exists(config.DATA_PATH):
        raise FileNotFoundError(f"Training data not found at {config.DATA_PATH}. Please ensure the dataset is available.")
    
    try:
        with open(config.TRANSFORMER_PATH, 'rb') as f:
            transformer = pickle.load(f)
        df = pd.read_csv(config.DATA_PATH)
        train_data = transformer.transform(df)
        data_sampler = DataSampler(train_data, transformer.output_info_list, True)
        generator = Generator(config.LATENT_DIM + data_sampler.dim_cond_vec(), config.GEN_HIDDEN_LAYERS, transformer.output_dimensions)
        generator.load_state_dict(torch.load(config.MODEL_PATH))
        generator.eval()
        
        logging.info("Generating samples...")
        generated = sample(num_samples, batch_size, config.LATENT_DIM, config.DEVICE, data_sampler, generator, transformer)
        return generated
    except Exception as e:
        logging.error(f"Error during sample generation: {str(e)}")
        raise

# generated_data = generate_samples(100, 50)