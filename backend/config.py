import os

# Get the current directory (backend folder)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(BASE_DIR, 'data', 'raw', 'KDDTest+.csv')
MODEL_SAVE_PATH = os.path.join(BASE_DIR, 'src', 'models')
MODEL_PATH = os.path.join(MODEL_SAVE_PATH, 'gan_generator.pth')
TRANSFORMER_PATH = os.path.join(MODEL_SAVE_PATH, 'data_transformer.pkl')
DISCRETE_COLUMNS = ['protocol_type', 'service', 'flag', 'class']
BATCH_SIZE = 500
EPOCHS = 1
LATENT_DIM = 128
GEN_HIDDEN_LAYERS = (256, 256)
DISC_HIDDEN_LAYERS = (256, 256)
PAC = 10
LR = 2e-4
BETAS = (0.5, 0.9)
WEIGHT_DECAY = 1e-6
GRADIENT_PENALTY = 10
DEVICE = 'cpu'

OUTPUT_PATH = os.path.join(BASE_DIR, 'src', 'IDS', 'output')
MAPPING_SAVE_PATH = os.path.join(MODEL_SAVE_PATH, "label_mapping.json")
PREPROCESSOR_SAVE_PATH = os.path.join(MODEL_SAVE_PATH, "preprocessor.pkl")
IDS_BATCH_SIZE = 32
TRAIN_RATIO = 0.8
TEST_RATIO = 0.2
EPOCHS = 1
LEARNING_RATE = 0.001
DEVICE = 'cpu'

RIGHT_SKEWED = ['0', '491', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9', '0.10', '0.11', '0.12', '0.13', '0.14', '0.15', '0.16', '0.18', '2', '2.1', '0.00', '0.00.1', '0.00.2']
LEFT_SKEWED = ['20', '150', '1.00']
TYPES = ['normal', 'neptune', 'warezclient', 'portsweep', 'smurf', 
         'satan', 'ipsweep', 'nmap', 'imap', 'back', 'multihop', 'warezmaster']
NUMERIC = ['duration', 'src_bytes', 'dst_bytes', 'wrong_fragment',
       'urgent', 'hot', 'num_failed_logins', 'num_compromised',
       'root_shell', 'su_attempted', 'num_root', 'num_file_creations',
       'num_shells', 'num_access_files', 'num_outbound_cmds',
       'count', 'srv_count', 'serror_rate',
       'srv_serror_rate', 'rerror_rate', 'srv_rerror_rate', 'same_srv_rate',
       'diff_srv_rate', 'srv_diff_host_rate', 'dst_host_count',
       'dst_host_srv_count', 'dst_host_same_srv_rate',
       'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
       'dst_host_srv_diff_host_rate', 'dst_host_serror_rate',
       'dst_host_srv_serror_rate', 'dst_host_rerror_rate',
       'dst_host_srv_rerror_rate', 'other']

PCAP_SAVE_PATH = os.path.join(BASE_DIR, 'data', 'raw', "capture.pcap")
PCAP_OUTPUT_PATH = os.path.join(BASE_DIR, 'data', 'raw', "output.arff")