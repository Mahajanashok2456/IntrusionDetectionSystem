import torch
import numpy as np
from .inverse_transform import inverse_transform

def sample(n, batch_size, embedding_dim,device, data_sampler, generator, transformer):
    steps = (n // batch_size) + 1
    data = []
    
    for _ in range(steps):
        mean = torch.zeros(batch_size, embedding_dim, device=device)
        std = mean + 1
        fakez = torch.normal(mean=mean, std=std)

        condvec = data_sampler.sample_original_condvec(batch_size)
        if condvec is not None:
            c1 = torch.from_numpy(condvec).to(device)
            fakez = torch.cat([fakez, c1], dim=1)

        fake = generator(fakez)
        fakeact = fake.detach().cpu().numpy()
        data.append(fakeact)

    data = np.concatenate(data, axis=0)[:n]
    print(data.shape)

    expected_cols = sum(info.output_dimensions for info in transformer._column_transform_info_list)
    print(expected_cols)
    if data.shape[1] != expected_cols:
        raise ValueError(f"Shape mismatch: Generated {data.shape[1]} columns, expected {expected_cols}.")

    return inverse_transform(data, transformer)