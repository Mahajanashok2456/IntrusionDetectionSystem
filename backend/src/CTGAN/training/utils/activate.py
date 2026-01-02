import numpy as np
import torch
import torch.nn.functional as F

def apply_activate(data, transformer):
    data_t = []
    st = 0

    for column_info in transformer.output_info_list:
        for span_info in column_info:
            ed = st + span_info.dim

            if span_info.activation_fn == 'tanh':
                data_t.append(torch.tanh(data[:, st:ed]))
            
            elif span_info.activation_fn == 'softmax':
                transformed = F.gumbel_softmax(data[:, st:ed], tau=0.2, hard=False)
                data_t.append(transformed)
            
            else:
                raise ValueError(f'Unexpected activation function {span_info.activation_fn}.')

            st = ed

    return torch.cat(data_t, dim=1)  # Keep output as a tensor
